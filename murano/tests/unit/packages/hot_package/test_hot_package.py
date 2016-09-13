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
import os
from shutil import rmtree
import yaml

from murano.packages import exceptions
import murano.packages.hot_package
import murano.packages.load_utils as load_utils
import murano.tests.unit.base as test_base


MANIFEST_TEMPLATE = {
    'resources': '',
    'parameters': {
        'foo': {
            'type': 'number',
            'label': 'foo_label',
            'description': 'foo_desc',
            'default': 'default_val',
            'constraints': [
                {
                    'length': {
                        'min': 0,
                        'max': 5
                    }
                },
                {
                    'range': {
                        'min': 0,
                        'max': 4
                    },
                    'description': 'range_desc'
                },
                {
                    'allowed_values': [0, 1, 2, 3, 4],
                    'description': 'allowed_values_desc'
                },
                {
                    'allowed_pattern': ['A-Za-z0-9'],
                    'description': 'allowed_values_desc'
                }
            ]
        },
        'bar': {
            'type': 'boolean'
        },
        'baz': {
            'type': 'string'
        }
    },
    'parameter_groups': [
        {
            'parameters': {
                'foo': {
                    'type': 'number',
                    'label': 'foo_label',
                    'description': 'foo_desc',
                    'default': 'default_val',
                    'constraints': [
                        {
                            'length': {
                                'min': 0,
                                'max': 5
                            }
                        },
                        {
                            'range': {
                                'min': 0,
                                'max': 4
                            },
                            'description': 'range_desc'
                        },
                        {
                            'allowed_values': [0, 1, 2, 3, 4],
                            'description': 'allowed_values_desc'
                        },
                        {
                            'allowed_pattern': ['A-Za-z0-9'],
                            'description': 'allowed_values_desc'
                        }
                    ]
                }
            }
        }
    ]
}


class TestHotPackage(test_base.MuranoTestCase):

    def setUp(cls):
        super(TestHotPackage, cls).setUp()
        # Create test yaml files
        dirname, _ = os.path.split(os.path.abspath(__file__))
        cls.test_dirs = [
            os.path.join(dirname, sub) for sub in ['test1', 'test2', 'test3']
        ]
        manifest_file_contents = [MANIFEST_TEMPLATE, {}]
        for i in range(len(cls.test_dirs)):
            if not os.path.isdir(cls.test_dirs[i]):
                os.makedirs(cls.test_dirs[i])
            yaml_file = os.path.join(cls.test_dirs[i], 'template.yaml')
            if i < len(manifest_file_contents):
                with open(yaml_file, 'w') as yaml_file:
                    yaml.dump(manifest_file_contents[i], yaml_file,
                        default_flow_style=True)
        # Test manifest
        cls.manifest = {
            'FullName': 'FullTestName',
            'Version': '1.0.0',
            'Type': 'Application',
            'Name': 'TestName',
            'Description': 'TestDescription',
            'Author': 'TestAuthor',
            'Supplier': 'TestSupplier',
            'Logo:': 'TestLogo',
            'Tags': ['Tag1', 'Tag2']
        }

    def tearDown(cls):
        super(TestHotPackage, cls).tearDown()
        for i in range(len(cls.test_dirs)):
            if os.path.isdir(cls.test_dirs[i]):
                rmtree(cls.test_dirs[i])

    def test_heat_files_generated(self):
        package_dir = os.path.abspath(
            os.path.join(__file__,
                         '../../test_packages/test.hot.v1.app_with_files')
        )
        load_utils.load_from_dir(package_dir)

        files = murano.packages.hot_package.HotPackage._translate_files(
            package_dir)
        expected_result = {
            "testHeatFile",
            "middle_file/testHeatFile",
            "middle_file/inner_file/testHeatFile",
            "middle_file/inner_file2/testHeatFile"
        }
        msg = "hot files were not generated correctly"
        self.assertSetEqual(expected_result, set(files), msg)

    def test_heat_files_generated_empty(self):
        package_dir = os.path.abspath(
            os.path.join(__file__,
                         '../../test_packages/test.hot.v1.app')
        )
        load_utils.load_from_dir(package_dir)

        files = murano.packages.hot_package.HotPackage \
            ._translate_files(package_dir)
        msg = "heat files were not generated correctly. Expected empty list"
        self.assertEqual([], files, msg)

    def test_build_properties(self):
        hot = {}
        hot['parameters'] = {
            'param1': {
                'type': 'boolean',
                'constraints': [
                    {
                        'allowed_values': [True, False]
                    }
                ]
            },
            'param2': {
                'type': 'string',
                'constraints': [
                    {
                        'allowed_values': ['bar'],
                    },
                    {
                        'length': {
                            'max': 50
                        },
                    },
                    {
                        'length': {
                            'min': 0
                        },
                    },
                    {
                        'allowed_pattern': '[A-Za-z0-9]'
                    }
                ]
            },
            'param3': {
                'type': 'number',
                'constraints': [
                    {
                        'allowed_values': [0, 1, 2, 3, 4]
                    },
                    {
                        'length': {
                            'min': 0,
                            'max': 5
                        },
                    },
                    {
                        'range': {
                            'min': 0,
                            'max': 4
                        }
                    }
                ]
            },
            'param4': {
                'type': 'number',
                'constraints': [
                    {
                        'range': {
                            'min': -1000
                        }
                    },
                    {
                        'range': {
                            'max': 1000
                        }
                    }
                ]
            },
            'param5': {
                'type': 'json'
            },
            'param6': {
                'type': 'comma_delimited_list'
            }
        }

        result = murano.packages.hot_package.HotPackage._build_properties(hot,
            validate_hot_parameters=True)

        self.assertIn('templateParameters', result)
        params = result['templateParameters']
        self.assertEqual(len(params['Contract']), 6)
        param1 = params['Contract']['param1']
        self.assertEqual(param1.expr, "$.bool().check($ in list(True, False))")
        param2 = params['Contract']['param2']
        self.assertEqual(param2.expr, "$.string().check($ in list('bar'))."
            "check(len($) <= 50).check(len($) >= 0).check(matches($, '["
            "A-Za-z0-9]'))")
        param3 = params['Contract']['param3']
        self.assertEqual(param3.expr, "$.int().check($ in list(0, 1, 2, 3, 4))"".check(len($) >= 0 and len($) <= 5).check($ >= 0 and $ <= 4)")
        param4 = params['Contract']['param4']
        self.assertEqual(param4.expr,"$.int().check($ >= -1000).check($ <= "
            "1000)")
        param5 = params['Contract']['param5']
        self.assertEqual(param5.expr, "$.string()")
        param6 = params['Contract']['param6']
        self.assertEqual(param6.expr, "$.string()")

        result = murano.packages.hot_package.HotPackage._build_properties(hot,
            validate_hot_parameters=False)
        expected_result = {
            'Contract': {},
            'Default': {},
            'Usage': 'In'
        }
        self.assertEquals(result['templateParameters'], expected_result)

    def test_translate_param_to_contract_with_inappropriate_value(self):
        func = murano.packages.hot_package.HotPackage.\
            _translate_param_to_contract
        self.assertRaises(
            ValueError,
            func,
            {'type': 'Inappropriate value'}
        )

    def test_get_class_name(self):
        hot_package = murano.packages.hot_package.HotPackage(
            None, None, source_directory=self.test_dirs[0],
            manifest=self.manifest
        )
        translated_class, _ = hot_package.get_class(hot_package.full_name)
        self.assertIsNotNone(translated_class)
        self.assertEqual(translated_class, hot_package._translated_class)

    def test_get_class_name_with_invalid_template_name(self):
        hot_package = murano.packages.hot_package.HotPackage(
            None, None, source_directory=self.test_dirs[0],
            manifest=self.manifest
        )
        self.assertRaises(
            exceptions.PackageClassLoadError,
            hot_package.get_class,
            'Invalid name')

    def test_get_class_name_with_invalid_template_format(self):
        hot_package = murano.packages.hot_package.HotPackage(
            None, None, source_directory=self.test_dirs[1],
            manifest=self.manifest
        )
        self.assertRaises(
            exceptions.PackageFormatError,
            hot_package.get_class,
            hot_package.full_name)

    def test_get_class_name_with_nonexistent_template(self):
        hot_package = murano.packages.hot_package.HotPackage(
            None, None, source_directory=self.test_dirs[2],
            manifest=self.manifest
        )
        self.assertRaises(
            exceptions.PackageClassLoadError,
            hot_package.get_class,
            hot_package.full_name)

    def test_translate_ui(self):
        hot_package = murano.packages.hot_package.HotPackage(
            None, None, source_directory=self.test_dirs[0],
            manifest=self.manifest
        )
        hot_package._translate_ui()

    def test_translate_ui_with_nonexistent_template(self):
        hot_package = murano.packages.hot_package.HotPackage(
            None, None, source_directory=self.test_dirs[2],
            manifest=self.manifest
        )
        self.assertRaises(
            exceptions.PackageClassLoadError,
            hot_package._translate_ui)

