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

import webob
import mock
from keystoneauth1 import exceptions
from oslo_serialization import base64
from murano.api.middleware import ext_context
from oslo_config import cfg
from murano.tests.unit import base

CONF = cfg.CONF

class MiddlewareExtContextTest(base.MuranoTestCase):

    def test_middleware_ext_context_default(self):
        middleware = ext_context.ExternalContextMiddleware(None)
	middleware.get_keystone_token = mock.MagicMock(return_value="token?")
 	auth = 'Basic {}'.format(base64.encode_as_text(b'test:test'))
        request_headers = {
                'Authorization': auth,
        }
        request = webob.Request.blank('/environments',
                                      headers=request_headers)
        result = middleware.process_request(request)

    def test_middleware_ext_context_except_key_error(self):
        middleware = ext_context.ExternalContextMiddleware(None)
        middleware.get_keystone_token = mock.MagicMock(side_effect=KeyError('test key error'))
        auth = 'Basic {}'.format(base64.encode_as_text(b'test:test'))
        request_headers = {
                'Authorization': auth,
        }
        request = webob.Request.blank('/environments',
                                      headers=request_headers)
        self.assertRaises(webob.exc.HTTPUnauthorized,middleware.process_request,request)

    def test_middleware_ext_context_except_key_error(self):
        middleware = ext_context.ExternalContextMiddleware(None)
        middleware.get_keystone_token = mock.MagicMock(side_effect=exceptions.Unauthorized(''))
        auth = 'Basic {}'.format(base64.encode_as_text(b'test:test'))
        request_headers = {
                'Authorization': auth,
        }
        request = webob.Request.blank('/environments',
                                      headers=request_headers)
        self.assertRaises(webob.exc.HTTPUnauthorized,middleware.process_request,request)

