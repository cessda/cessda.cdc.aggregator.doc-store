# Copyright CESSDA ERIC 2021
#
# Licensed under the EUPL, Version 1.2 (the "License"); you may not
# use this file except in compliance with the License.
# You may obtain a copy of the License at
# https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
from unittest import mock
from argparse import Namespace

from bson import ObjectId
from tornado import testing
from tornado.escape import (
    json_encode,
    json_decode
)

from kuha_common.testing import mock_coro
from kuha_common.testing.testcases import KuhaUnitTestCase
from kuha_document_store import database
from kuha_document_store.handlers import (
    RestApiHandler,
    QueryHandler
)

from cdcagg_common.records import Study
from cdcagg_docstore import (
    http_api,
    serve,
    controller
)


class TestGetApp(KuhaUnitTestCase):

    def setUp(self):
        super().setUp()
        self._mock_WebApplication = self.init_patcher(mock.patch.object(http_api, 'WebApplication'))

    def test_returns_WebApplication(self):
        rval = http_api.get_app('api_version', ('coll1', 'coll2', 'coll3'))
        self.assertEqual(rval, self._mock_WebApplication.return_value)

    def test_calls_WebApplication_correctly(self):
        http_api.get_app('api_version', ('coll1', 'coll2', 'coll3'), keyword='argument')
        self._mock_WebApplication.assert_called_once_with(
            handlers=[
                ('/api_version/(?P<collection>coll1|coll2|coll3)/?', RestApiHandler),
                ('/api_version/(?P<collection>coll1|coll2|coll3)/(?P<resource_id>\\w+)', RestApiHandler),
                ('/api_version/query/(?P<collection>coll1|coll2|coll3)/?', QueryHandler)],
            keyword='argument')


DBNAME = 'cdcagg'


def async_generate_value(values):
    async def async_generator():
        for value in values:
            await asyncio.sleep(0.2)
            yield value
    return async_generator()


def settings():
    return Namespace(replica=['localhost:27017'],
                     replicaset='rs_kuha',
                     database_name=DBNAME,
                     database_user_reader='reader',
                     database_user_editor='editor',
                     database_pass_reader='readerpass',
                     database_pass_editor='editorpass')


class TestCaseBase(testing.AsyncHTTPTestCase):
    """Base to test the running server"""

    def setUp(self):
        self._patchers = []
        self._settings = settings()
        self._patch_db()
        super().setUp()

    def tearDown(self):
        for patcher in self._patchers:
            patcher.stop()

    def _init_patcher(self, patcher):
        self._patchers.append(patcher)
        return patcher.start()

    def _patch_db(self):
        self.mock_studies = mock.Mock()
        patcher = mock.patch.object(database, 'MotorClient',
                                    return_value={DBNAME: {'studies': self.mock_studies}})
        self._patchers.append(patcher)
        self._mock_MotorClient = patcher.start()

    def get_app(self):
        db = controller.db_from_settings(self._settings)
        return serve.get_app('v0', ['studies'], db=db)

    def _assert_response_equal(self, response, exp_code, exp_body=None):
        self.assertEqual(response.code, exp_code)
        if exp_body is not None:
            self.assertEqual(response.body, exp_body)
        return response.body


class TestRESTApi(TestCaseBase):

    @staticmethod
    def _valid_study_dict():
        study = Study()
        study.add_study_number('some_study_number')
        study.set_direct_base_url('some.url')
        study.set_aggregator_identifier(
            '6eb05b9342cc92e9a09de18df0a34318b9913c69e3d78b0222fb2f7cdf0ba9a3')
        return study.export_dict()

    def test_GET_studies(self):
        self.mock_studies.find.return_value = async_generate_value([{'some': 'record'}, {'another': 'record'}])
        self._assert_response_equal(self.fetch('/v0/studies'), 200,
                                    b'{"some": "record"}{"another": "record"}')
        self.mock_studies.find.assert_called_once_with({}, projection=None, skip=0, limit=0)

    def test_POST_returns_400_on_validation_fail(self):
        resp_body = self._assert_response_equal(self.fetch('/v0/studies',
                                                           method='POST',
                                                           headers={'Content-Type': 'application/json'},
                                                           body=json_encode({'key': 'value'})), 400)
        self.assertEqual(json_decode(resp_body),
                         {'code': 400,
                          'message': "HTTP 400: Bad Request (('Validation of studies failed', "
                          "{'_aggregator_identifier': ['required field'], "
                          "'_direct_base_url': ['required field'], "
                          "'key': ['unknown field'], "
                          "'study_number': ['required field']}))"})

    def test_POST_validation_rec_status_fail(self):
        study_dict = self._valid_study_dict()
        study_dict['_metadata']['status'] = 'invalid'
        resp_body = self._assert_response_equal(self.fetch('/v0/studies',
                                                           method='POST',
                                                           headers={'Content-Type': 'application/json'},
                                                           body=json_encode(study_dict)), 400)
        self.assertEqual(json_decode(resp_body),
                         {'code': 400,
                          'message': "HTTP 400: Bad Request (('Validation of studies failed', "
                          "{'_metadata': [{'status': ['unallowed value invalid']}]}))"})

    def test_POST_validation_schema_version_fail(self):
        study_dict = self._valid_study_dict()
        study_dict['_metadata']['schema_version'] = 'invalid'
        resp_body = self._assert_response_equal(self.fetch('/v0/studies',
                                                           method='POST',
                                                           headers={'Content-Type': 'application/json'},
                                                           body=json_encode(study_dict)), 400)
        self.assertEqual(json_decode(resp_body),
                         {'code': 400,
                          'message': "HTTP 400: Bad Request (('Validation of studies failed', "
                          "{'_metadata': [{'schema_version': ['unallowed value "
                          "invalid']}]}))"})

    def test_POST_validation_cmm_type_fail(self):
        study_dict = self._valid_study_dict()
        study_dict['_metadata']['cmm_type'] = 'invalid'
        resp_body = self._assert_response_equal(self.fetch('/v0/studies',
                                                           method='POST',
                                                           headers={'Content-Type': 'application/json'},
                                                           body=json_encode(study_dict)), 400)
        self.assertEqual(json_decode(resp_body),
                         {'code': 400,
                          'message': "HTTP 400: Bad Request (('Validation of studies failed', "
                          "{'_metadata': [{'cmm_type': ['unallowed value invalid']}]}))"})

    def test_POST_validation_direct_base_url_fail(self):
        study_dict = self._valid_study_dict()
        study_dict['_direct_base_url'] = None
        resp_body = self._assert_response_equal(self.fetch('/v0/studies',
                                                           method='POST',
                                                           headers={'Content-Type': 'application/json'},
                                                           body=json_encode(study_dict)), 400)
        body_dict = json_decode(resp_body)
        self.assertEqual(body_dict['code'], 400)
        self.assertEqual(body_dict['message'],
                         "HTTP 400: Bad Request (('Validation of studies failed', "
                         "{'_direct_base_url': ['null value not allowed']}))")

    def test_POST_returns_201_on_success(self):
        self.mock_studies.insert_one.side_effect = mock_coro(mock.Mock(inserted_id='new_id'))
        study_dict = self._valid_study_dict()
        resp_body = self._assert_response_equal(self.fetch('/v0/studies',
                                                           method='POST',
                                                           headers={'Content-Type': 'application/json'},
                                                           body=json_encode(study_dict)),
                                                201)
        self.assertEqual(json_decode(resp_body), {'affected_resource': 'new_id',
                                                  'error': None,
                                                  'result': 'insert_successful'})

    def test_DELETE_physical_returns_200_on_success(self):
        self.mock_studies.delete_many.side_effect = mock_coro(mock.Mock(deleted_count=1))
        resp_body = self._assert_response_equal(self.fetch('/v0/studies/619f95dff13cfc3ed67ff0f6?delete_type=hard',
                                                           method='DELETE'), 200)
        self.assertEqual(json_decode(resp_body), {'affected_resource': '619f95dff13cfc3ed67ff0f6',
                                                  'error': None,
                                                  'result': 'delete_successful'})
        self.mock_studies.delete_many.assert_called_once_with({'_id': ObjectId('619f95dff13cfc3ed67ff0f6')})

    def test_DELETE_logical_returns_200_on_success(self):
        self.mock_studies.update_many.side_effect = mock_coro(mock.Mock(modified_count=1))
        resp_body = self._assert_response_equal(self.fetch('/v0/studies/619f95dff13cfc3ed67ff0f6',
                                                           method='DELETE'), 200)
        self.assertEqual(json_decode(resp_body), {'affected_resource': '619f95dff13cfc3ed67ff0f6',
                                                  'error': None,
                                                  'result': 'delete_successful'})

    def test_PUT_returns_200_on_success(self):
        self.mock_studies.replace_one.side_effect = mock_coro(mock.Mock(upserted_id='619f95dff13cfc3ed67ff0f6'))
        self.mock_studies.find_one.side_effect = mock_coro(Study().export_dict())
        resp_body = self._assert_response_equal(self.fetch('/v0/studies/619f95dff13cfc3ed67ff0f6',
                                                           method='PUT',
                                                           headers={'Content-Type': 'application/json'},
                                                           body=json_encode({'study_number': 'value'})),
                                                200)
        self.assertEqual(json_decode(resp_body), {'affected_resource': '619f95dff13cfc3ed67ff0f6',
                                                  'error': None,
                                                  'result': 'replace_successful'})

    def test_PUT_returns_400_on_validation_error(self):
        self.mock_studies.replace_one.side_effect = mock_coro(mock.Mock(upserted_id='619f95dff13cfc3ed67ff0f6'))
        self.mock_studies.find_one.side_effect = mock_coro(Study().export_dict())
        resp_body = self._assert_response_equal(self.fetch('/v0/studies/619f95dff13cfc3ed67ff0f6',
                                                           method='PUT',
                                                           headers={'Content-Type': 'application/json'},
                                                           body=json_encode({'key': 'value'})),
                                                400)
        self.assertEqual(json_decode(resp_body), {
            'code': 400,
            'message': "HTTP 400: Bad Request (('Validation of studies failed', {'key': "
            "['unknown field']}))"})
