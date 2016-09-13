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

import mock
import unittest

from murano.dsl import dsl
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import murano_method
from murano.dsl import murano_object
from murano.dsl import murano_type

import neutronclient.v2_0.client as nclient

from oslo_config import cfg

from murano.engine.system import net_explorer
from murano.tests.unit import base

CONF = cfg.CONF


class TestNetExplorer(base.MuranoTestCase):
    def setUp(self):
        super(TestNetExplorer, self).setUp()
        self.mock_class = mock.MagicMock(spec=murano_type.MuranoClass)
        self.mock_method = mock.MagicMock(spec=murano_method.MuranoMethod)

        self.nclient_mock = mock.Mock()
        self._this = mock.MagicMock()
        self._this._region = None

        self.addCleanup(mock.patch.stopall)

    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_init(self, execution_session):
        region_name = "regionOne"
        net_explorer.NetworkExplorer(self._this, region_name)
