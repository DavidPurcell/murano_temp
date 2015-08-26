#    Copyright (c) 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
import contextlib
import itertools
import types
import weakref

import eventlet
import eventlet.event
from oslo_log import log as logging
from yaql.language import specs

from murano.common.i18n import _LW
from murano.dsl import attribute_store
from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import helpers
from murano.dsl import murano_method
from murano.dsl import object_store
from murano.dsl.principal_objects import stack_trace
from murano.dsl import yaql_functions
from murano.dsl import yaql_integration

LOG = logging.getLogger(__name__)


class MuranoDslExecutor(object):
    def __init__(self, package_loader, environment=None):
        self._package_loader = package_loader
        self._attribute_store = attribute_store.AttributeStore()
        self._root_context = \
            self.create_root_context().create_child_context()
        self._root_context[constants.CTX_EXECUTOR] = weakref.proxy(self)
        self._root_context[
            constants.CTX_PACKAGE_LOADER] = weakref.proxy(self._package_loader)
        self._root_context[constants.CTX_ENVIRONMENT] = environment
        self._root_context[constants.CTX_ATTRIBUTE_STORE] = weakref.proxy(
            self._attribute_store)
        self._object_store = object_store.ObjectStore(self._root_context)
        self._locks = {}

    @property
    def object_store(self):
        return self._object_store

    @property
    def attribute_store(self):
        return self._attribute_store

    @property
    def package_loader(self):
        return self._package_loader

    def invoke_method(self, method, this, context, args, kwargs,
                      skip_stub=False):
        if isinstance(this, dsl.MuranoObjectInterface):
            this = this.object
        kwargs = yaql_integration.filter_parameters_dict(kwargs)
        if context is None or not skip_stub:
            actions_only = context is None and not method.name.startswith('.')
            method_context = self._create_method_context(
                this, method, context, actions_only, skip_frame=True)
            return method.yaql_function_definition(
                yaql_integration.ENGINE, method_context, this.real_this)(
                *args, **kwargs)

        if (context[constants.CTX_ACTIONS_ONLY] and method.usage !=
                murano_method.MethodUsages.Action):
            raise Exception('{0} is not an action'.format(method.name))

        context = self._create_method_context(this, method, context)
        this = this.real_this

        if method.arguments_scheme is not None:
            args, kwargs = self._canonize_parameters(
                method.arguments_scheme, args, kwargs)

        with self._acquire_method_lock(method, this):
            for i, arg in enumerate(args, 2):
                context[str(i)] = arg
            for key, value in kwargs.iteritems():
                context[key] = value

            def call():
                if isinstance(method.body, specs.FunctionDefinition):
                    native_this = this.cast(
                        method.murano_class).extension
                    return method.body(
                        yaql_integration.ENGINE, context, native_this)(
                        *args, **kwargs)
                else:
                    return (None if method.body is None
                            else method.body.execute(context))

            if (not isinstance(method.body, specs.FunctionDefinition)
                    or not method.body.meta.get(constants.META_NO_TRACE)):
                with self._log_method(context, args, kwargs) as log:
                    result = call()
                    log(result)
                    return result
            else:
                return call()

    @contextlib.contextmanager
    def _acquire_method_lock(self, func, this):
        method_id = id(func)
        this_id = this.object_id
        thread_id = helpers.get_current_thread_id()
        while True:
            event, event_owner = self._locks.get(
                (method_id, this_id), (None, None))
            if event:
                if event_owner == thread_id:
                    event = None
                    break
                else:
                    event.wait()
            else:
                event = eventlet.event.Event()
                self._locks[(method_id, this_id)] = (event, thread_id)
                break
        try:
            yield
        finally:
            if event is not None:
                del self._locks[(method_id, this_id)]
                event.send()

    @contextlib.contextmanager
    def _log_method(self, context, args, kwargs):
        method = helpers.get_current_method(context)
        param_gen = itertools.chain(
            (str(arg) for arg in args),
            ('{0} => {1}'.format(name, value)
             for name, value in kwargs.iteritems()))
        params_str = ', '.join(param_gen)
        method_name = '{0}::{1}'.format(method.murano_class.name, method.name)
        thread_id = helpers.get_current_thread_id()
        caller_str = ''
        caller_ctx = helpers.get_caller_context(context)
        if caller_ctx is not None:
            frame = stack_trace.compose_stack_frame(caller_ctx)
            if frame['location']:
                caller_str = ' called from ' + stack_trace.format_frame(frame)

        LOG.trace('{0}: Begin execution {1}({2}){3}'.format(
            thread_id, method_name, params_str, caller_str))
        try:
            def log_result(result):
                LOG.trace('{0}: End execution {1} with result {2}'.format(
                    thread_id, method_name, result))
            yield log_result
        except Exception as e:
            LOG.trace('{0}: End execution {1} with exception {2}'.format(
                thread_id, method_name, e))
            raise

    @staticmethod
    def _canonize_parameters(arguments_scheme, args, kwargs):
        arg_names = arguments_scheme.keys()
        parameter_values = yaql_integration.filter_parameters_dict(kwargs)
        for i, arg in enumerate(args):
            name = arg_names[i]
            parameter_values[name] = arg
        return tuple(), parameter_values

    def _create_method_context(self, this, method, context=None,
                               actions_only=False, skip_frame=False):
        new_context = self.create_local_context(
            parent_context=this.context,
            murano_class=this.type)
        caller = context
        while caller is not None and caller[constants.CTX_SKIP_FRAME]:
            caller = caller[constants.CTX_CALLER_CONTEXT]
        new_context[constants.CTX_CALLER_CONTEXT] = caller
        new_context[constants.CTX_CURRENT_METHOD] = method
        new_context[constants.CTX_ACTIONS_ONLY] = actions_only
        new_context[constants.CTX_SKIP_FRAME] = skip_frame

        if context is not None:
            new_context[constants.CTX_ALLOW_PROPERTY_WRITES] = context[
                constants.CTX_ALLOW_PROPERTY_WRITES]
        return new_context

    def load(self, data):
        if not isinstance(data, types.DictionaryType):
            raise TypeError()
        self._attribute_store.load(data.get(constants.DM_ATTRIBUTES) or [])
        result = self._object_store.load(data.get(constants.DM_OBJECTS), None)
        if result is None:
            return None
        return dsl.MuranoObjectInterface(
            result, yaql_integration.ENGINE, executor=self)

    def cleanup(self, data):
        objects_copy = data.get(constants.DM_OBJECTS_COPY)
        if not objects_copy:
            return
        gc_object_store = object_store.ObjectStore(self._root_context)
        gc_object_store.load(objects_copy, None)
        objects_to_clean = []
        for object_id in self._list_potential_object_ids(objects_copy):
            if (gc_object_store.has(object_id)
                    and not self._object_store.has(object_id)):
                obj = gc_object_store.get(object_id)
                objects_to_clean.append(obj)
        if objects_to_clean:
            for obj in objects_to_clean:
                methods = obj.type.find_methods(lambda m: m.name == '.destroy')
                for method in methods:
                    try:
                        method.invoke(self, obj, (), {}, None)
                    except Exception as e:
                        LOG.warn(_LW(
                            'Muted exception during execution of .destroy '
                            'on {1}: {2}').format(obj, e), exc_info=True)

    def _list_potential_object_ids(self, data):
        if isinstance(data, types.DictionaryType):
            for val in data.values():
                for res in self._list_potential_object_ids(val):
                    yield res
            sys_dict = data.get('?')
            if (isinstance(sys_dict, types.DictionaryType)
                    and sys_dict.get('id')
                    and sys_dict.get('type')):
                yield sys_dict['id']
        elif isinstance(data, collections.Iterable) and not isinstance(
                data, types.StringTypes):
            for val in data:
                for res in self._list_potential_object_ids(val):
                    yield res

    # noinspection PyMethodMayBeStatic
    def create_local_context(self, parent_context, murano_class):
        return parent_context.create_child_context()

    # noinspection PyMethodMayBeStatic
    def create_root_context(self):
        context = yaql_integration.create_context()
        yaql_functions.register(context)
        return context
