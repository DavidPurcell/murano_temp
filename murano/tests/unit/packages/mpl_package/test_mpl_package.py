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

import mock
import os
import yaml

from murano.packages import exceptions
import murano.packages.mpl_package as mpl_package
import murano.packages.load_utils as load_utils
import murano.tests.unit.base as test_base

class TestMPLPackage(test_base.MuranoTestCase):

    def setUp(cls):
        super(TestMPLPackage, cls).setUp()
        cls.source_directory , _ = os.path.split(os.path.abspath(__file__))
        manifest_path = os.path.join(cls.source_directory, 'manifest.yaml')
        cls.manifest = {}
        with open(manifest_path) as manifest_file:
            for key, value in yaml.load(manifest_file).iteritems():
                cls.manifest[key] = value

    def test_classes_property(self):
        package = mpl_package.MuranoPlPackage(None, None,
            self.source_directory, self.manifest)
        classes = package.classes
        self.assertIn('Class1', classes)
        self.assertIn('Class2', classes)

    def test_ui_property(self):
        package = mpl_package.MuranoPlPackage(None, None,
            self.source_directory, self.manifest)
        ui = package.ui
        self.assertIsNotNone(ui)

    def test_meta_property(self):
        package = mpl_package.MuranoPlPackage(None, None,
            self.source_directory, self.manifest)
        meta = package.meta
        self.assertEqual(meta, 'test.meta')

    def test_get_class(self):
        package = mpl_package.MuranoPlPackage(None, None,
            self.source_directory, self.manifest)
        stream, path = package.get_class('Class1')
        expected_path = os.path.join(self.source_directory, 'Classes',
            'test.class1')
        self.assertIn('test.class1', stream)
        self.assertEqual(path, expected_path)

    def test_get_class_with_inappropriate_name(self):
        package = mpl_package.MuranoPlPackage(None, None,
            self.source_directory, self.manifest)
        self.assertRaises(exceptions.PackageClassLoadError,
            package.get_class,
            'Invalid name')

    def test_get_class_with_nonexistent_class(self):
        package = mpl_package.MuranoPlPackage(None, None,
            self.source_directory, self.manifest)
        self.assertRaises(exceptions.PackageClassLoadError,
            package.get_class,
            'Class2')