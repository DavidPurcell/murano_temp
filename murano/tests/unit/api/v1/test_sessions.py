# Copyright (c) 2015 Mirantis Inc.
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
from oslo_config import fixture as config_fixture
from oslo_serialization import jsonutils

from murano.api.v1 import environments
from murano.api.v1 import sessions
from murano.db import models
from murano.db import session as db_session
from murano.services import states
import murano.tests.unit.api.base as tb

from webob import exc

class TestSessionsApi(tb.ControllerTest, tb.MuranoApiTestCase):
    def setUp(self):
        super(TestSessionsApi, self).setUp()
        self.environments_controller = environments.Controller()
        self.sessions_controller = sessions.Controller()
        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])

    def test_deploy_session(self):
        CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        ENVIRONMENT_ID = response_body['id']
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        SESSION_ID = response_body['id']
        request = self._post(
            '/environments/{environment_id}/sessions/'
            '{session_id}/deploy'.format(environment_id=ENVIRONMENT_ID,
                                         session_id=SESSION_ID),
            b'',
            **CREDENTIALS
        )
        response = request.get_response(self.api)
        self.assertEqual(response.status_code, 200)
        request = self._get(
            '/environments/{environment_id}/sessions/{session_id}'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertIn(response_body['state'], [states.SessionState.DEPLOYED,
                                               states.SessionState.DEPLOYING])

    def test_cant_deploy_from_another_tenant(self):
        """Test to prevent deployment under another tenant user's creds

        If user from one tenant uses session id and environment id
        of user from another tenant - he is not able to deploy
        the environment.

        Bug: #1382026
        """
        CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        CREDENTIALS_2 = {'tenant': 'test_tenant_2', 'user': 'test_user_2'}

        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment for user #1
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS_1['tenant'],
                         response_body['tenant_id'])

        ENVIRONMENT_ID = response_body['id']

        # Create session of user #1
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)

        SESSION_ID = response_body['id']

        # Deploy the environment using environment id and session id of user #1
        # by user #2
        request = self._post(
            '/environments/{environment_id}/sessions/'
            '{session_id}/deploy'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS_2
        )
        response = request.get_response(self.api)

        # Should be forbidden!
        self.assertEqual(403, response.status_code)

    def test_session_show(self):
        CREDENTIALS_1 = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        CREDENTIALS_2 = {'tenant': 'test_tenant_2', 'user': 'test_user_2'}

        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment for user #1
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS_1['tenant'],
                         response_body['tenant_id'])
        ENVIRONMENT_ID = response_body['id']

        # Create session of user #1
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        SESSION_ID = response_body['id']

        # Show environment with correct credentials
        request = self._get(
            '/environments/{environment_id}/sessions/{session_id}'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS_1
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(SESSION_ID, response_body['id'])

        # Show environment with incorrect credentials
        request = self._get(
            '/environments/{environment_id}/sessions/{session_id}'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS_2
        )
        response = request.get_response(self.api)
        self.assertEqual(403, response.status_code)

    def test_session_delete(self):
        CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}

        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        # Create environment
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        self.assertEqual(CREDENTIALS['tenant'],
                         response_body['tenant_id'])
        ENVIRONMENT_ID = response_body['id']

        # Create session
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        SESSION_ID = response_body['id']

        # Delete session
        request = self._delete(
            '/environments/{environment_id}/delete/{session_id}'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS
        )
        response = self.sessions_controller.delete(
            request, ENVIRONMENT_ID, SESSION_ID)

        # Make sure the session was deleted
        request = self._get(
            '/environments/{environment_id}/sessions/{session_id}'
            .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
            b'',
            **CREDENTIALS
        )
        response = request.get_response(self.api)
        self.assertEqual(404, response.status_code)
        session = unit.query(models.Session).get(SESSION_ID)
        self.assertIsNone(session)

    @mock.patch('murano.db.services.environments.EnvironmentServices.'
                'get_status')
    def test_configure_handle_exc(self, mock_function):
        """Test whether env status in DEPLOYING, DELETING throws exception."""
        CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        ENVIRONMENT_ID = response_body['id']

        env_statuses = [states.EnvironmentStatus.DEPLOYING,
                        states.EnvironmentStatus.DELETING]
        for env_status in env_statuses:
            mock_function.return_value = env_status
            request = self._post(
                '/environments/{environment_id}/configure'
                .format(environment_id=ENVIRONMENT_ID),
                b'',
                **CREDENTIALS
            )
            response = request.get_response(self.api)
            self.assertEqual(response.status_code, 403)
        self.assertEqual(mock_function.call_count, len(env_statuses))

    def test_show_handle_exc(self):
        """Test whether invalid user/invalid session throws exception."""
        CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        ENVIRONMENT_ID = response_body['id']
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        SESSION_ID = response_body['id']

        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(ENVIRONMENT_ID)
        mock_context = mock.MagicMock(user_id=None,
                                      tenant=environment.tenant_id)
        mock_request = mock.MagicMock(context=mock_context)
        self.assertRaises(exc.HTTPUnauthorized,
                          self.sessions_controller.show,
                          mock_request,
                          ENVIRONMENT_ID,
                          SESSION_ID)

        with mock.patch('murano.db.services.sessions.SessionServices.'
                        'validate') as mock_validate:
            mock_validate.return_value = False
            request = self._get(
                '/environments/{environment_id}/sessions/{session_id}'
                .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
                b'',
                **CREDENTIALS
            )
            response = request.get_response(self.api)
            self.assertEqual(response.status_code, 403)

    def test_delete_handle_exc(self):
        """Test whether invalid user/invalid session throws exception."""
        CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        ENVIRONMENT_ID = response_body['id']
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        SESSION_ID = response_body['id']

        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(ENVIRONMENT_ID)
        mock_context = mock.MagicMock(user_id=None,
                                      tenant=environment.tenant_id)
        mock_request = mock.MagicMock(context=mock_context)
        self.assertRaises(exc.HTTPUnauthorized,
                          self.sessions_controller.delete, mock_request,
                          ENVIRONMENT_ID, SESSION_ID)

        with mock.patch('murano.services.states.SessionState') as mock_state:
            unit = db_session.get_session()
            session = unit.query(models.Session).get(SESSION_ID)
            mock_state.DEPLOYING = session.state
            request = self._delete(
                '/environments/{environment_id}/delete/{session_id}'
                .format(environment_id=ENVIRONMENT_ID, session_id=SESSION_ID),
                b'',
                **CREDENTIALS
            )
            self.assertRaises(exc.HTTPForbidden,
                              self.sessions_controller.delete, request,
                              ENVIRONMENT_ID, SESSION_ID)

    def test_deploy_handle_exc(self):
        """Test whether invalid user/invalid session throws exception."""
        CREDENTIALS = {'tenant': 'test_tenant_1', 'user': 'test_user_1'}
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        self.expect_policy_check('create_environment')
        request = self._post(
            '/environments',
            jsonutils.dump_as_bytes({'name': 'test_environment_1'}),
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        ENVIRONMENT_ID = response_body['id']
        request = self._post(
            '/environments/{environment_id}/configure'
            .format(environment_id=ENVIRONMENT_ID),
            b'',
            **CREDENTIALS
        )
        response_body = jsonutils.loads(request.get_response(self.api).body)
        SESSION_ID = response_body['id']

        with mock.patch('murano.db.services.sessions.SessionServices.'
                        'validate') as mock_validate:
            mock_validate.return_value = False
            request = self._post(
                '/environments/{environment_id}/sessions/'
                '{session_id}/deploy'.format(environment_id=ENVIRONMENT_ID,
                                             session_id=SESSION_ID),
                b'',
                **CREDENTIALS
            )
            self.assertRaises(exc.HTTPForbidden,
                              self.sessions_controller.deploy, request,
                              ENVIRONMENT_ID, SESSION_ID)

        with mock.patch('murano.db.services.sessions.SessionServices.'
                        'validate') as mock_validate:
            with mock.patch('murano.services.states.SessionState')\
                    as mock_state:
                mock_validate.return_value = True
                mock_state.OPENED = 'NOT OPENED STATE'
                request = self._post(
                    '/environments/{environment_id}/deploy/{session_id}'
                    .format(environment_id=ENVIRONMENT_ID,
                            session_id=SESSION_ID),
                    b'',
                    **CREDENTIALS
                )
                self.assertRaises(exc.HTTPForbidden,
                                  self.sessions_controller.deploy, request,
                                  ENVIRONMENT_ID, SESSION_ID)
