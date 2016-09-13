# Copyright (c) 2016 AT&T
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

try:
    from mistralclient.api import client
except ImportError as mistral_import_error:
    mistralcli = None

import mock
from oslo_config import cfg

from murano.dsl import dsl
from murano.dsl import exceptions
from murano.dsl import murano_method
from murano.dsl import murano_object
from murano.dsl import murano_type

from murano.engine.system import workflowclient
from murano.tests.unit import base

CONF = cfg.CONF


class TestMistralClient(base.MuranoTestCase):
    def setUp(self):
        super(TestMistralClient, self).setUp()
        self.mistral_client_mock = mock.Mock()
        self.mistral_client_mock.client = mock.MagicMock(spec=client.client)
        workflowclient.MistralClient._create_client = mock.Mock(
            return_value=self.mistral_client_mock)
        workflowclient.MistralClient._client = mock.Mock(
            return_value=self.mistral_client_mock)

        self.mock_class = mock.MagicMock(spec=murano_type.MuranoClass)
        self.mock_method = mock.MagicMock(spec=murano_method.MuranoMethod)

        self._this = mock.MagicMock()
        self._this.owner = None

        self.addCleanup(mock.patch.stopall)

    def test_run(self):
        run_name = 'test'
        timeout = 0
        mc = workflowclient.MistralClient(self._this, 'regionOne')
        mc.run(run_name, timeout)

    def test_upload(self):
        mc = workflowclient.MistralClient(self._this, 'regionOne')
        definition = "test"
        mc.upload(definition)
