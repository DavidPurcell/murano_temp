# Copyright 2016 AT&T Corp
# All Rights Reserved.
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

import webob
import mock
from murano.common import wsgi
from murano.api.middleware import fault
from murano.packages import exceptions
from oslo_config import cfg
from murano.tests.unit import base
from webob import exc
from oslo_serialization import jsonutils

CONF = cfg.CONF

class FaultWrapperTest(base.MuranoTestCase):
    def test_error_500(self):
	fault_wrapper = fault.FaultWrapper(None)	
	result = fault_wrapper._error(exc.HTTPInternalServerError())
        self.assertEquals(result['code'],500)
	self.assertEquals(result['explanation'],
		'The server has either erred or is incapable of performing the requested operation.')        
    def test_error_value_error(self):
	fault_wrapper = fault.FaultWrapper(None)
        result = fault_wrapper._error(exceptions.PackageClassLoadError("test"))
	print(result)
        self.assertEquals(result['code'],400)
	self.assertEquals(result['error']['message'], 'Unable to load class "test" from package')

    def test_fault_wrapper(self):
	fault_wrapper = fault.FaultWrapper(None)
	exception_disguise = fault.HTTPExceptionDisguise(exc.HTTPInternalServerError())
	result = fault_wrapper._error(exception_disguise)
	self.assertEquals(result['code'],500)                            
        self.assertEquals(result['explanation'],
                'The server has either erred or is incapable of performing the requested operation.')

    def test_process_request(self):
	CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
	fault_wrapper = fault.FaultWrapper(None)
	environ = {
            'SERVER_NAME': 'server.test',
            'SERVER_PORT': '8082',
            'SERVER_PROTOCOL': 'http',
            'SCRIPT_NAME': '/',
            'PATH_INFO': '/asdf/asdf/asdf/asdf',
            'wsgi.url_scheme': 'http',
            'QUERY_STRING': '',
            'CONTENT_TYPE': 'application/json',
	    'REQUEST_METHOD': 'HEAD'
        }
	req = wsgi.Request(environ)
	req.get_response = mock.MagicMock(side_effect=exc.HTTPInternalServerError())
	self.assertRaises(exc.HTTPInternalServerError, fault_wrapper.process_request, req)

    def test_fault_call(self):
	fault_wrapper = fault.FaultWrapper(None)
	test_fault = fault.Fault(fault_wrapper._error(exceptions.PackageClassLoadError("test")))
	environ = {
            'SERVER_NAME': 'server.test',
            'SERVER_PORT': '8082',
            'SERVER_PROTOCOL': 'http',
            'SCRIPT_NAME': '/',
            'PATH_INFO': '/',
            'wsgi.url_scheme': 'http',
            'QUERY_STRING': '',
            'CONTENT_TYPE': 'application/json',
            'REQUEST_METHOD': 'HEAD'
        }
        req = wsgi.Request(environ)
	response = jsonutils.loads(test_fault(req).body)
	self.assertEquals(response['code'], 400)

