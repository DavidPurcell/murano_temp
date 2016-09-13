#    Copyright (c) 2016 AT&T
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

import os
import tempfile

import mock
from oslo_serialization import base64
import yaml as yamllib

from murano.dsl import helpers
from murano.dsl import murano_object
from murano.dsl import murano_type
from murano.dsl import object_store
from murano.engine.system import agent
from murano.engine.system import resource_manager
from murano.tests.unit import base


class TestResourceManager(base.MuranoTestCase):
    def setUp(self):
        super(TestResourceManager, self).setUp()
        self.yaml_loader = yamllib.SafeLoader

        self.addCleanup(mock.patch.stopall)

    @mock.patch("murano.dsl.helpers.get_caller_context")
    @mock.patch("murano.dsl.helpers.get_type")
    def test_init(self, context_type, caller_context):
        self.resource_manager = resource_manager.ResourceManager(context_type)

    @mock.patch("murano.dsl.helpers.get_caller_context")
    @mock.patch("murano.dsl.helpers.get_type")
    def test_get_package_none_owner(self, context_type, caller_context):
        owner = None
        receiver = None
        resource_manager.ResourceManager._get_package(owner, receiver)
