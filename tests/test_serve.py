# Copyright CESSDA ERIC 2021-2025
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
from cdcagg_docstore import serve


class TestConfigure(KuhaUnitTestCase):

    def setUp(self):
        super().setUp()
        self._mock_conf = self.init_patcher(mock.patch.object(serve, 'conf'))
        self._mock_controller_add_cli_args = self.init_patcher(mock.patch.object(serve.controller, 'add_cli_args'))
        self._mock_server_add_cli_args = self.init_patcher(mock.patch.object(serve.server, 'add_cli_args'))
        self._mock_setup_app_logging = self.init_patcher(mock.patch.object(serve, 'setup_app_logging'))
        self._mock_set_ctx_populator = self.init_patcher(mock.patch.object(serve, 'set_ctx_populator'))

    def test_calls_conf_load(self):
        serve.configure()
        self._mock_conf.load.assert_called_once_with(
            prog='cdcagg_docstore', package='cdcagg_docstore', env_var_prefix='CDCAGG_')

    def test_calls_add_cli_args(self):
        serve.configure()
        self._mock_server_add_cli_args.assert_called_once_with()
        self._mock_controller_add_cli_args.assert_called_once_with(self._mock_conf)

    def test_calls_conf_add_correctly(self):
        serve.configure()
        self.assert_mock_meth_has_calls(
            self._mock_conf.add,
            mock.call('-p', '--port', help='Port to listen to', default=6001, type=int, env_var='DOCSTORE_PORT'),
            mock.call('--api-version', help='HTTP API version gets prepended to URLs', default='v0', type=str,
                      env_var='DOCSTORE_API_VERSION'))

    def test_returns_settings(self):
        rval = serve.configure()
        self.assertEqual(rval, self._mock_conf.get_conf.return_value)

    def test_calls_set_ctx_populator(self):
        serve.configure()
        self._mock_set_ctx_populator.assert_called_once_with(serve.server.serverlog_ctx_populator)

    def test_calls_setup_app_logging(self):
        serve.configure()
        self._mock_setup_app_logging.assert_called_once_with(
            self._mock_conf.get_package.return_value,
            loglevel=self._mock_conf.get_conf.return_value.loglevel,
            port=self._mock_conf.get_conf.return_value.port)
