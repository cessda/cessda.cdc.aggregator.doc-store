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

from unittest import mock

from kuha_common.testing.testcases import KuhaUnitTestCase
from kuha_document_store.handlers import (
    RestApiHandler,
    QueryHandler
)

from cdcagg_docstore import http_api


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
