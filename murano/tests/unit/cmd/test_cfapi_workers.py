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

import mock
import sys

from oslo_concurrency import processutils
from oslo_log import log as logging

from murano.cmd import cfapi
from murano.common import app_loader
from murano.common import config
from murano.common import policy
from murano.tests.unit import base



class TestCFAPIWorkers(base.MuranoTestCase):

    def setUp(self):
        super(TestCFAPIWorkers, self).setUp()
        sys.argv = ['murano']

    @mock.patch.object(config, 'parse_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch.object(policy, 'init')
    @mock.patch.object(config, 'set_middleware_defaults')
    @mock.patch.object(app_loader, 'load_paste_app')
    @mock.patch('oslo_service.service.ServiceLauncher.launch_service')
    def test_workers_default(self, launch, setup, parse_args, init,
                             load_paste_app, set_middleware_defaults):
        cfapi.main()
        self.assertTrue(launch.called)

    @mock.patch.object(config, 'parse_args')
    @mock.patch.object(logging, 'setup')
    @mock.patch.object(policy, 'init')
    @mock.patch.object(config, 'set_middleware_defaults')
    @mock.patch.object(app_loader, 'load_paste_app')
    @mock.patch('oslo_service.service.ServiceLauncher.launch_service')
    def test_workers_runtime_error(self, launch, setup, parse_args, init,
                                   load_paste_app, set_middleware_defaults):
        launch.side_effect = RuntimeError("test")
        self.assertRaises(SystemExit, cfapi.main)
