#    Copyright (c) 2016 AT&T Inc.
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

from murano import utils

from murano.tests.unit import base

from webob import exc

from mock import MagicMock

from murano.db import session


class UtilsTests(base.MuranoTestCase):
    def test_check_session(self):
        self.assertRaises(exc.HTTPNotFound, utils.check_session,
                          None, None, None, None)

        s = session
        s.environment_id = MagicMock(return_value=1)
        self.assertRaises(exc.HTTPBadRequest, utils.check_session,
                          None, 2, s, None)
