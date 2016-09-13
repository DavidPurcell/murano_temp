# Copyright (c) 2016 AT&T Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import mock
from oslo_utils import timeutils

from murano.api.v1 import environments
from murano.api.v1 import sessions
from murano.api.v1 import instance_statistics

from oslo_config import fixture as config_fixture
from oslo_serialization import jsonutils

from murano.db import session as db_session

from murano.api import v1
from murano.common import policy
from murano.db import models
import murano.tests.unit.api.base as tb
import murano.tests.unit.utils as test_utils


class TestInitApi(tb.ControllerTest, tb.MuranoApiTestCase):
    def setUp(self):
        super(TestInitApi, self).setUp()
        self.environments_controller = environments.Controller()
        self.sessions_controller = sessions.Controller()
	self.statistics_controller = instance_statistics.Controller()
        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])

    def test_get_aggregated(self):
	CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@',
	     'get_aggregated_statistics': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        environment_id = response_body['id']

	self.expect_policy_check('get_aggregated_statistics', {'environment_id': environment_id})

	result = self.statistics_controller.get_aggregated(request, environment_id)
	self.assertEquals([], result)

    def test_get_for_instance(self):
	CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@',
             'get_aggregated_statistics': '@',
	     'get_instance_statistics': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        environment_id = response_body['id']
        instance_id = 12

        self.expect_policy_check('get_instance_statistics', {'environment_id': environment_id, 'instance_id': instance_id})

        result = self.statistics_controller.get_for_instance(request, environment_id, instance_id)
        self.assertEquals([], result)

    def test_get_for_environment(self):
        CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@',
             'get_statistics': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        environment_id = response_body['id']

        self.expect_policy_check('get_statistics', {'environment_id': environment_id})

        result = self.statistics_controller.get_for_environment(request, environment_id)
        self.assertEquals([], result)
