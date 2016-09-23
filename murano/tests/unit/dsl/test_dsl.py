#    Copyright (c) 2015 Mirantis, Inc.
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

import mock

from yaql.language import yaqltypes
from yaql.language import expressions as yaql_expressions

from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.tests.unit.dsl.foundation import test_case

class TestMuranoObjectParameter(test_case.DslTestCase):
    def setUp(self):
        super(TestMuranoObjectParameter, self).setUp()
        self.mop = dsl.MuranoObjectParameter()

    @mock.patch.object(yaqltypes.PythonType, 'check', return_value=False)
    def test_check_fail_super_check(self, mock_parent_check):
        val = dsl_types.MuranoObject()
        is_check = self.mop.check(val, 'context', 123, foo='bar')
        mock_parent_check.assert_called_with(val, 'context', 123, foo='bar')
        self.assertFalse(is_check)

    @mock.patch.object(yaqltypes.PythonType, 'check', return_value=True)
    def test_check_val_none_or_yaql_expr(self, mock_parent_check):
        is_check1 = self.mop.check(None, 'context')
        is_check2 = self.mop.check(yaql_expressions.Expression(), 'context')
        self.assertTrue(is_check1 and is_check2)

    @mock.patch.object(yaqltypes.PythonType, 'check', return_value=True)
    def test_check_val_not_murano_object(self, mock_parent_check):
        is_check = self.mop.check('value', 'context')
        self.assertFalse(is_check)

    @mock.patch.object(yaqltypes.PythonType, 'check', return_value=True)
    def test_check_val_murano_object(self, mock_parent_check):
        val = dsl_types.MuranoObject()
        is_check = self.mop.check(val, 'context')
        self.assertTrue(is_check)

    @mock.patch.object(yaqltypes.PythonType, 'check', return_value=True)
    @mock.patch.object(helpers, 'get_type')
    @mock.patch.object(helpers, 'is_instance_of', return_value=True)
    def test_check_string_murano_class(self, mock_iio, mock_gt, 
                                           mock_parent_check):
        val = dsl_types.MuranoObject()
        self.mop = dsl.MuranoObjectParameter(murano_class='myclass')
        is_check = self.mop.check(val, 'context')
        self.assertTrue(is_check)

    @mock.patch.object(yaqltypes.PythonType, 'check', return_value=True)
    def test_check_murano_class(self, mock_parent_check):
        val = dsl_types.MuranoObject()
        murano_class = mock.MagicMock()
        murano_class.is_compatible.return_value = False
        self.mop = dsl.MuranoObjectParameter(murano_class=murano_class)
        is_check = self.mop.check(val, 'context')
        self.assertFalse(is_check)

    @mock.patch.object(yaqltypes.PythonType, 'convert', return_value='result')
    @mock.patch.object(dsl.MuranoObjectInterface, 'create', return_value='return')
    def test_convert(self, mock_moi_create, mock_parent_convert):
        ret = self.mop.convert('val', 'sender', 'context', 'fs', 'eng')
        mock_parent_convert.assert_called_with('val', 'sender', 'context', 'fs', 'eng')
        mock_moi_create.assert_called_with('result')
        self.assertEqual('return', ret)

    @mock.patch.object(yaqltypes.PythonType, 'convert')
    def test_convert_no_decorate(self, mock_parent_convert):
        self.mop = dsl.MuranoObjectParameter(decorate=False)
        expected = dsl_types.MuranoObject()
        mock_parent_convert.return_value = expected
        ret = self.mop.convert('val', 'sender', 'context', 'fs', 'eng')
        mock_parent_convert.assert_called_with('val', 'sender', 'context', 'fs', 'eng')
        self.assertEqual(expected, ret)

    @mock.patch.object(yaqltypes.PythonType, 'convert')
    def test_convert_no_decorate_none(self, mock_parent_convert):
        self.mop = dsl.MuranoObjectParameter(decorate=False)
        mock_parent_convert.return_value = None
        ret = self.mop.convert('val', 'sender', 'context', 'fs', 'eng')
        mock_parent_convert.assert_called_with('val', 'sender', 'context', 'fs', 'eng')
        self.assertIs(None, ret)

    @mock.patch.object(yaqltypes.PythonType, 'convert')
    def test_convert_no_decorate_non_murano_object(self, mock_parent_convert):
        self.mop = dsl.MuranoObjectParameter(decorate=False)
        mock_parent_convert.return_value = mock.MagicMock(object='myobject')
        ret = self.mop.convert('val', 'sender', 'context', 'fs', 'eng')
        mock_parent_convert.assert_called_with('val', 'sender', 'context', 'fs', 'eng')
        self.assertIs('myobject', ret)


class TestThisParameter(test_case.DslTestCase): 
    def setUp(self):
        super(TestThisParameter, self).setUp()
        self.this_param = dsl.ThisParameter()

    @mock.patch.object(dsl, 'get_this', return_value='return')
    def test_convert(self, mock_get_this):
        ret = self.this_param.convert('val', 'sender', 'ctxt', 'fs', 'eng')
        mock_get_this.assert_called_with('ctxt')
        self.assertEqual('return', ret)


class TestInterfacesParameter(test_case.DslTestCase):
    def setUp(self):
        super(TestInterfacesParameter, self).setUp()
        self.ifs_param = dsl.InterfacesParameter()

    @mock.patch.object(helpers, 'get_this', return_value='gotthis')
    @mock.patch.object(dsl, 'Interfaces', return_value='interfaces')
    def test_convert(self, mock_interfaces, mock_h_get_this):
        ret = self.ifs_param.convert('val', 'sender', 'ctxt', 'fs', 'eng')
        mock_interfaces.assert_called_with('gotthis')
        self.assertEqual('interfaces', ret)


class TestMuranoTypeParameter(test_case.DslTestCase):
    def setUp(self):
        super(TestMuranoTypeParameter, self).setUp()
        self.mtp = dsl.MuranoTypeParameter()

    @mock.patch.object(yaqltypes.PythonType, 'check', return_value=False)
    def test_check_fail_super_check(self, mock_parent_check):
        val = dsl_types.MuranoTypeReference(mock.MagicMock())
        is_check = self.mtp.check(val, 'context', 123, foo='bar')
        mock_parent_check.assert_called_with(val, 'context', 123, foo='bar')
        self.assertFalse(is_check)

    @mock.patch.object(yaqltypes.PythonType, 'check', return_value=True)
    def tests_check_value_not_string_not_resolve_strings(
        self, mock_parent_check):
        self.mtp = dsl.MuranoTypeParameter(resolve_strings=False)
        val = 12345
        is_check = self.mtp.check(val, 'context')
        self.assertFalse(is_check)
