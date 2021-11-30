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
from argparse import Namespace
from unittest import mock
from io import StringIO
from kuha_common.testing import MockCoro
from kuha_common.testing.testcases import KuhaUnitTestCase
from cdcagg_docstore import (
    db_admin,
    studies_collection
)


def async_gen(values):
    async def async_generator():
        for value in values:
            await asyncio.sleep(0.2)
            yield value
    return async_generator()


@mock.patch.object(db_admin, 'conf')
class TestConfigure(KuhaUnitTestCase):

    def test_calls_load_on_conf(self, mock_conf):
        mock_conf.load.assert_not_called()
        db_admin.configure()
        self.assertEqual(mock_conf.load.call_count, 1)

    def test_calls_add_print_arg_on_conf(self, mock_conf):
        mock_conf.add_print_arg.assert_not_called()
        db_admin.configure()
        mock_conf.add_print_arg.assert_called_once_with()

    def test_calls_add_config_arg_on_conf(self, mock_conf):
        mock_conf.add_config_arg.assert_not_called()
        db_admin.configure()
        mock_conf.add_config_arg.assert_called_once_with()

    @mock.patch.object(db_admin, 'add_cli_args')
    def test_calls_add_cli_args_on_server_controller(self, mock_add_cli_args, mock_conf):
        mock_add_cli_args.assert_not_called()
        db_admin.configure()
        mock_add_cli_args.assert_called_once_with(mock_conf)

    @mock.patch.object(db_admin, 'add_cli_args')
    def test_calls_add_on_conf(self, mock_add_cli_args, mock_conf):
        mock_conf.add.assert_not_called()
        db_admin.configure()
        self.assertEqual(mock_conf.add.call_count, 3)
        calls = mock_conf.add.call_args_list
        exp_calls = {
            '--database-user-admin': {
                'help': 'Username for MongoDB administration. If not '
                        'submitted via configuration, the program will '
                        'prompt admin credentials on startup.',
                'env_var': 'DBUSER_ADMIN'},
            '--database-pass-admin': {
                'help': 'Password for MongoDB administration. If not '
                        'submitted via configuration, the program will '
                        'prompt admin credentials on startup.',
                'env_var': 'DBPASS_ADMIN'},
            'operations': {
                'nargs': '+',
                'help': 'Operations to perform',
                'choices': ['drop_collections', 'list_databases', 'initiate_replicaset',
                            'list_collections', 'setup_collections', 'remove_users',
                            'setup_database', 'list_admin_users', 'show_replicaset_config',
                            'list_users', 'drop_database', 'setup_users',
                            'list_collection_indexes', 'show_replicaset_status']
            }}
        self.assertEqual(len(calls), len(exp_calls))
        for call in calls:
            cargs, ckwargs = call
            self.assertEqual(len(cargs), 1)
            carg = cargs[0]
            self.assertIn(carg, exp_calls)
            exp_ckwargs = exp_calls.pop(carg)
            if carg == 'operations':
                self.assertIn('choices', ckwargs)
                cchoices = ckwargs.pop('choices')
                exp_choices = exp_ckwargs.pop('choices')
                self.assertCountEqual(cchoices, exp_choices)
            self.assertEqual(ckwargs, exp_ckwargs)
        self.assertEqual(exp_calls, {})

    def test_returns_result_of_conf_get(self, mock_conf):
        rval = db_admin.configure()
        self.assertEqual(rval, mock_conf.get_conf())


@mock.patch.object(db_admin, 'configure')
@mock.patch.object(db_admin, 'input', return_value='admin')
@mock.patch.object(db_admin, 'getpass', return_value='admin_pass')
class TestMain(KuhaUnitTestCase):

    def test_calls_configure(self, mock_getpass, mock_input, mock_configure):
        settings = Namespace(print_configuration=False, database_name='db', operations=[],
                             database_user_admin=None, database_pass_admin=None,
                             replica=['url', 'url2'], replicaset='replset')
        mock_configure.return_value = settings
        mock_configure.assert_not_called()
        rval = db_admin.main()
        mock_configure.assert_called_once_with()
        self.assertEqual(rval, 0)

    @mock.patch.object(db_admin, 'conf')
    def test_calls_print_conf_on_conf(self, mock_conf, mock_getpass, mock_input, mock_configure):
        mock_conf.print_conf.assert_not_called()
        mock_configure.return_value.print_configuration = True
        rval = db_admin.main()
        mock_conf.print_conf.assert_called_once_with()
        self.assertEqual(rval, 0)


class DBOperationsTestBase(KuhaUnitTestCase):

    db_name = 'database_name'

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.mock_input = self.init_patcher(mock.patch.object(db_admin, 'input'))
        self.mock_getpass = self.init_patcher(mock.patch.object(db_admin, 'getpass'))
        self.mock_MotorClient = self.init_patcher(mock.patch.object(db_admin, 'MotorClient'))
        self.mock_client = mock.MagicMock()
        self.mock_app_db = mock.MagicMock()
        self.mock_admin_db = mock.Mock()
        self.mock_client.__getitem__.side_effect = lambda name: {'database_name': self.mock_app_db,
                                                                 'admin': self.mock_admin_db}[name]
        self.mock_MotorClient.return_value = self.mock_client
        self.mock_input.return_value = 'admin_username'
        self.mock_getpass.return_value = 'admin_pass'
        self.mock_configure = self.init_patcher(mock.patch.object(db_admin, 'configure'))

    def _settings(self, **kw):
        settings = Namespace(database_name=kw.pop('database_name', self.db_name),
                             print_configuration=kw.pop('print_configuration', None),
                             replicaset=kw.pop('replicaset', 'replicaset'),
                             replica=kw.pop('replica', ['localhost:1111', 'localhost:2222', 'localhost:3333']),
                             operations=kw.pop('operations', []),
                             database_pass_admin=kw.pop('database_pass_admin', None),
                             database_user_admin=kw.pop('database_user_admin', None),
                             **kw)
        self.mock_configure.return_value = settings


class TestCredentialsPrompt(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self.mock_client.admin.command = mock.Mock(side_effect=MockCoro('result'))

    def _settings(self, **kw):
        kw['operations'] = kw.get('operations', ['initiate_replicaset'])
        super()._settings(**kw)

    def test_prompts_credentials(self):
        self._settings()
        db_admin.main()
        self.mock_input.assert_called_once_with('Admin username: ')
        self.mock_getpass.assert_called_once_with('Admin password: ')

    def test_does_not_prompt_credentials(self):
        self._settings(database_user_admin='adminuser', database_pass_admin='password')
        db_admin.main()
        self.mock_input.assert_not_called()
        self.mock_getpass.assert_not_called()

    def test_prompts_username(self):
        self._settings(database_pass_admin='password')
        db_admin.main()
        self.mock_input.assert_called_once_with('Admin username: ')
        self.mock_getpass.assert_not_called()

    def test_prompts_password(self):
        self._settings(database_user_admin='adminuser')
        db_admin.main()
        self.mock_input.assert_not_called()
        self.mock_getpass.assert_called_once_with('Admin password: ')


class TestInitiateReplicaset(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self._settings(operations=['initiate_replicaset'])
        self.mock_command = mock.Mock(side_effect=MockCoro('result'))
        self.mock_client.admin.command = self.mock_command

    def test_calls_command_on_client_admin(self):
        self.mock_command.assert_not_called()
        db_admin.main()
        self.mock_command.assert_called_once_with(
            'replSetInitiate',
            {'_id': 'replicaset',
             'members': [{'_id': 0, 'host': 'localhost:1111'},
                         {'_id': 1, 'host': 'localhost:2222'},
                         {'_id': 2, 'host': 'localhost:3333'}]})

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation initiate_replicaset ...\n"
                    "initiate_replicaset result:\n"
                    "'result'\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestShowReplicasetStatus(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self._settings(operations=['show_replicaset_status'])
        self.mock_admin_db.command.side_effect = MockCoro('replicaset status')

    def test_calls_command_on_admin_db(self):
        self.mock_admin_db.command.assert_not_called()
        db_admin.main()
        self.mock_admin_db.command.assert_called_once_with('replSetGetStatus')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation show_replicaset_status ...\n"
                    "show_replicaset_status result:\n"
                    "'replicaset status'\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestShowReplicasetConfig(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self._settings(operations=['show_replicaset_config'])
        self.mock_admin_db.command.side_effect = MockCoro('replicaset configuration')

    def test_calls_command_on_admin_db(self):
        self.mock_admin_db.command.assert_not_called()
        db_admin.main()
        self.mock_admin_db.command.assert_called_once_with('replSetGetConfig')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation show_replicaset_config ...\n"
                    "show_replicaset_config result:\n"
                    "'replicaset configuration'\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestSetupDatabase(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self._settings(operations=['setup_database'])

    def test_calls_get_database_on_client(self):
        self.mock_client.get_database.assert_not_called()
        db_admin.main()
        self.mock_client.get_database.assert_called_once_with(name=self.db_name)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation setup_database ...\n"
                    "setup_database result:\n"
                    "'mydatabase'\n")
        self.mock_client.get_database.return_value = 'mydatabase'
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestListDatabases(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self._settings(operations=['list_databases'])
        self.mock_client.list_database_names.side_effect = MockCoro(['my', 'databases'])

    def test_calls_list_database_names_on_client(self):
        self.mock_client.list_database_names.assert_not_called()
        db_admin.main()
        self.mock_client.list_database_names.assert_called_once_with()

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation list_databases ...\n"
                    "list_databases result:\n"
                    "['my', 'databases']\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestDropDatabase(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self._settings(operations=['drop_database'])
        self.mock_client.drop_database.side_effect = MockCoro('dropped')

    def test_calls_drop_database_on_client(self):
        self.mock_client.drop_database.assert_not_called()
        db_admin.main()
        self.mock_client.drop_database.assert_called_once_with(self.db_name)


class TestSetupCollections(DBOperationsTestBase):

    studies_coll = studies_collection()

    def setUp(self):
        super().setUp()
        self._settings(operations=['setup_collections'])
        self.mock_create_index = mock.Mock(side_effect=MockCoro())
        self.mock_app_db.create_collection.side_effect = MockCoro(mock.Mock(create_index=self.mock_create_index))

    def test_calls_create_collection_on_app_db(self):
        self.mock_app_db.create_collection.assert_not_called()
        db_admin.main()
        self.assertEqual(self.mock_app_db.create_collection.call_count, 1)
        self.mock_app_db.create_collection.assert_has_calls([
            mock.call(self.studies_coll.name, validator=self.studies_coll.validators)
        ], any_order=True)

    def test_calls_create_index_on_created_collections(self):
        self.mock_create_index.assert_not_called()
        db_admin.main()
        calls = []
        for coll in (self.studies_coll,):
            calls.extend([mock.call(index, unique=True) for index in coll.indexes_unique])
            calls.extend([mock.call(index) for index in coll.indexes])
        self.assertEqual(self.mock_create_index.call_count, len(calls))
        self.mock_create_index.assert_has_calls(calls, any_order=True)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        async def _side_eff(collname, *args, **kwargs):
            return collname

        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation setup_collections ...\n"
                    "setup_collections result:\n"
                    "{'studies': [[('study_number', 1)],\n"
                    "             [('_aggregator_identifier', 1)],\n"
                    "             [('_metadata.updated', -1)]]}\n")
        self.mock_create_index.side_effect = MockCoro(func=_side_eff)
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestListCollections(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self.mock_app_db.list_collection_names.side_effect = MockCoro(['list', 'of', 'collections'])
        self._settings(operations=['list_collections'])

    def test_calls_list_collection_names_on_app_db(self):
        self.mock_app_db.list_collection_names.assert_not_called()
        db_admin.main()
        self.mock_app_db.list_collection_names.assert_called_once_with()

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation list_collections ...\n"
                    "list_collections result:\n"
                    "['list', 'of', 'collections']\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestListCollectionIndexes(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self.mock_app_db.list_collection_names.side_effect = MockCoro(['coll_1', 'coll_2', 'coll_3'])
        self.mock_collection_1 = mock.Mock()
        self.mock_collection_1.list_indexes.return_value = async_gen(['index1', 'index2'])
        self.mock_collection_2 = mock.Mock()
        self.mock_collection_2.list_indexes.return_value = async_gen(['index3', 'index4'])
        self.mock_collection_3 = mock.Mock()
        self.mock_collection_3.list_indexes.return_value = async_gen(['index5'])
        self.mock_app_db.__getitem__.side_effect = lambda coll: {'coll_1': self.mock_collection_1,
                                                                 'coll_2': self.mock_collection_2,
                                                                 'coll_3': self.mock_collection_3}[coll]
        self._settings(operations=['list_collection_indexes'])

    def test_calls_list_indexes_on_collections(self):
        for mock_coll in (self.mock_collection_1, self.mock_collection_2, self.mock_collection_3):
            mock_coll.list_indexes.assert_not_called()
        db_admin.main()
        for mock_coll in (self.mock_collection_1, self.mock_collection_2, self.mock_collection_3):
            mock_coll.list_indexes.assert_called_once_with()

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation list_collection_indexes ...\n"
                    "list_collection_indexes result:\n"
                    "{'coll_1': ['index1', 'index2'],\n"
                    " 'coll_2': ['index3', 'index4'],\n"
                    " 'coll_3': ['index5']}\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestDropCollections(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self._settings(operations=['drop_collections'])
        self.mock_app_db.drop_collection.side_effect = MockCoro('dropped')

    def test_calls_drop_collection_on_app_db(self):
        self.mock_app_db.drop_collection.assert_not_called()
        db_admin.main()
        # called once for each collection.
        self.assertEqual(self.mock_app_db.drop_collection.call_count, 1)
        self.mock_app_db.drop_collection.assert_has_calls([
            mock.call('studies')], any_order=True)

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_print_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation drop_collections ...\n"
                    "drop_collections result:\n"
                    "['dropped']\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestListAdminUsers(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self.mock_admin_db.command.side_effect = MockCoro(['list', 'admin', 'users'])
        self._settings(operations=['list_admin_users'])

    def test_calls_command_on_admin_db(self):
        self.mock_admin_db.command.assert_not_called()
        db_admin.main()
        self.mock_admin_db.command.assert_called_once_with('usersInfo')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation list_admin_users ...\n"
                    "list_admin_users result:\n"
                    "['list', 'admin', 'users']\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestSetupUsers(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self.mock_app_db.command.side_effect = MockCoro('created')
        self._settings(operations=['setup_users'],
                       database_user_reader='reader',
                       database_user_editor='editor',
                       database_pass_reader='reader_pass',
                       database_pass_editor='editor_pass')

    def test_calls_command_on_app_db(self):
        self.mock_app_db.command.assert_not_called()
        db_admin.main()
        self.assertEqual(self.mock_app_db.command.call_count, 2)
        self.mock_app_db.command.assert_has_calls([
            mock.call('createUser', 'reader', pwd='reader_pass', roles=['read']),
            mock.call('createUser', 'editor', pwd='editor_pass', roles=['readWrite'])
        ])

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation setup_users ...\n"
                    "setup_users result:\n"
                    "['created', 'created']\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestListUsers(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self.mock_app_db.command.side_effect = MockCoro(['list', 'users'])
        self._settings(operations=['list_users'])

    def test_calls_command_on_app_db(self):
        self.mock_app_db.command.assert_not_called()
        db_admin.main()
        self.mock_app_db.command.assert_called_once_with('usersInfo')

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation list_users ...\n"
                    "list_users result:\n"
                    "['list', 'users']\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)


class TestRemoveUsers(DBOperationsTestBase):

    def setUp(self):
        super().setUp()
        self._settings(operations=['remove_users'],
                       database_user_reader='reader',
                       database_user_editor='editor')
        self.mock_app_db.command.side_effect = MockCoro('removed')

    def test_calls_command_on_app_db(self):
        self.mock_app_db.command.assert_not_called()
        db_admin.main()
        self.assertEqual(self.mock_app_db.command.call_count, 2)
        self.mock_app_db.command.assert_has_calls([
            mock.call('dropUser', 'reader'),
            mock.call('dropUser', 'editor')])

    @mock.patch('sys.stdout', new_callable=StringIO)
    def test_prints_output(self, mock_stdout):
        expected = ("Give database administrator username\n"
                    "Give database administrator password\n"
                    "Running operation remove_users ...\n"
                    "remove_users result:\n"
                    "['removed', 'removed']\n")
        db_admin.main()
        self.assertEqual(mock_stdout.getvalue(), expected)
