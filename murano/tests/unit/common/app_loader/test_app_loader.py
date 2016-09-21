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

import os
from oslo_config import cfg

from murano.common import app_loader
from murano.tests.unit import base

CONF = cfg.CONF


class AppLoaderTest(base.MuranoTestCase):

    def setUp(cls):
        super(AppLoaderTest, cls).setUp()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        cls.conf_file = os.path.join(dir_path, 'test-paste.ini')

    def test_load_paste_app(self):
        self.override_config('config_file',
                             self.conf_file,
                             group='paste_deploy')
        self.override_config('flavor',
                             'test_v1_app',
                             group='paste_deploy')
        app = app_loader.load_paste_app(app_name='test_app')
        self.assertIsNotNone(app)
        # Test whether the app's class corresponds to
        # murano.api.v1.router:API.factory
        self.assertEqual(unicode(app.__class__),
                         "<class 'murano.api.v1.router.API'>")

    def test_load_paste_app_with_erroneous_flavor(self):
        self.override_config('config_file',
                             self.conf_file,
                             group='paste_deploy')
        self.override_config('flavor',
                             'erroneous_flavor',
                             group='paste_deploy')
        self.assertRaises(
            RuntimeError,
            app_loader.load_paste_app,
            app_name='test_app')

    def test_load_paste_app_with_missing_paste_lookup(self):
        self.override_config('config_file',
                             self.conf_file,
                             group='paste_deploy')
        self.override_config('flavor',
                             'test_v2_app',
                             group='paste_deploy')
        self.assertRaises(
            RuntimeError,
            app_loader.load_paste_app,
            app_name='test_app')
