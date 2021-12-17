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

"""Admin operations to setup and manage CDC OAI Aggregator MongoDB.

For initial setup run the following against a mongodb replicaset::

    python -m cdcagg_docstore.db_admin initiate_replicaset setup_database setup_collections setup_users

Setup an empty database into an existing replicaset::

    python -m cdcagg_docstore.db_admin setup_database setup_collections setup_users

Drop & re-create collections, for example when indexes have been altered::

    python -m cdcagg_docstore.db_admin drop_collections setup_collections

"""
# STD
import sys
from collections import namedtuple
from pprint import pprint
from getpass import getpass
from argparse import RawDescriptionHelpFormatter
# PyPI
from tornado.ioloop import IOLoop
from tornado.gen import multi
from motor.motor_tornado import MotorClient
# Kuha
from kuha_common import conf
from kuha_document_store.database import mongodburi
# CDC Aggregator
from . import iter_collections
from .controller import add_cli_args


OperationsSetup = namedtuple('OperationsSetup', 'admin_credentials, settings, client, app_db, admin_db')
"""Operations setup variables.

These are used for setup and operations
performed in this module

:param tuple admin_credentials: DB Admin credentials.
:param settings: Loaded settings
:type settings: :obj:`argparse.Namespace`
:param client: MotorClient instance with valid connection uri.
:type client: :obj:`motor.motor_tornado.MotorClient`
:param app_db: Application database connection.
:type app_db: :obj:`motor.motor_tornado.MotorDatabase`
:param admin_db: Admin database connection.
:type admin_db: :obj:`motor.motor_tornado.MotorDatabase`
"""


class DBOperations:
    """DBOperations class used as a singleton to load arguments and
    setup connections. Use with @cli_operation decorated functions."""

    def __init__(self):
        """Initiate DBOperations class into an object.
        """
        self.operations = {}
        self.settings = None

    def setup(self, admin_username, admin_password, settings):
        """Setup the object for operations.

        :param str admin_username: MongoDB admin username
        :param str admin_password: MongoDB admin password
        :param settings: Loaded settings
        :type settings: :obj:`argparse.Namespace`
        """
        conn_uri = mongodburi(*settings.replica, database='admin',
                              credentials=(admin_username, admin_password),
                              options=[('replicaSet', settings.replicaset)])
        client = MotorClient(conn_uri)
        self.settings = OperationsSetup(admin_credentials=(admin_username, admin_password),
                                        settings=settings, client=client,
                                        app_db=client[settings.database_name],
                                        admin_db=client['admin'])

    def get(self, name):
        """Return the wrapped operations function.

        :param str name: function name.
        :returns: function
        """
        return self.operations[name]


_ops = DBOperations()


def cli_operation(func):
    """Decorator for CLI operation functions.

    :param function func: Decorated function
    :returns: Wrapper callable without arguments. Calls the
              decorated function and prints out the result.

    """
    op_str = func.__name__

    async def wrapper():
        print('Running operation %s ...' % (op_str,))
        result = await func(_ops.settings)
        print('%s result:' % (op_str,))
        pprint(result)
        return result
    # For sphinx autodoc:
    # Assign the docstring of the wrapped function
    # to docstring of the wrapper.
    wrapper.__doc__ = func.__doc__
    _ops.operations[op_str] = wrapper
    return wrapper


# MANAGE REPLICAS

@cli_operation
async def initiate_replicaset(ops_setup):
    """CLI operation to initiate replicaset.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Result of 'repsSetInitiate'
    """
    replset_members = [{'_id': index, 'host': host} for index, host in enumerate(ops_setup.settings.replica)]
    client = MotorClient(mongodburi(ops_setup.settings.replica[0], database='admin',
                                    credentials=ops_setup.admin_credentials))
    return await client.admin.command('replSetInitiate', {
        '_id': ops_setup.settings.replicaset,
        'members': replset_members})


@cli_operation
async def show_replicaset_status(ops_setup):
    """CLI operations to print out replicaset status.

    :param ops_setup: Setup variables.
    :type: :obj:`OperationsSetup`
    :returns: Result of 'repsSetGetStatus'
    """
    return await ops_setup.admin_db.command('replSetGetStatus')


@cli_operation
async def show_replicaset_config(ops_setup):
    """CLI operation to print out replicaset configs.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Result of 'repsSetGetConfig'
    """
    return await ops_setup.admin_db.command('replSetGetConfig')


# MANAGE DATABASES

@cli_operation
async def setup_database(ops_setup):
    """CLI operation to setup the application database.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Result of MotorClient.get_database()
    """
    return ops_setup.client.get_database(name=ops_setup.settings.database_name)


@cli_operation
async def list_databases(ops_setup):
    """CLI operation to list database names.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Result of MotorClient.list_database_names()
    """
    return await ops_setup.client.list_database_names()


@cli_operation
async def drop_database(ops_setup):
    """CLI operation to drop (remove) database.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Result of MotorClient.drop_database()
    """
    await ops_setup.client.drop_database(ops_setup.settings.database_name)


# MANAGE COLLECTIONS

@cli_operation
async def setup_collections(ops_setup):
    """CLI operation to setup database collections.

    Creates every collection and sets up it's indexes and validation.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Operations results in dict, where each key is a name of
              a collection, value is a list of task results:
              {<coll_name>: [<task_result_1>, <task_result_2>]}
    """
    result = {}
    for collection in iter_collections():
        tasks = []
        new_coll = await ops_setup.app_db.create_collection(collection.name,
                                                            validator=collection.validators)
        for coll_index in collection.indexes_unique:
            tasks.append(new_coll.create_index(coll_index, unique=True))
        for coll_index in collection.indexes:
            tasks.append(new_coll.create_index(coll_index))
        result.update({collection.name: await multi(tasks)})
    return result


@cli_operation
async def list_collections(ops_setup):
    """CLI operation to list collection names.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Result of MotorClient[<db_name>].list_collection_names()
    """
    return await ops_setup.app_db.list_collection_names()


@cli_operation
async def list_collection_indexes(ops_setup):
    """CLI operation to list collection indexes.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Operation results in dict format, where each key is a
              collection name and it's value is a list of indexes.
    """
    result = {}
    for collname in await ops_setup.app_db.list_collection_names():
        indexes = []
        result.update({collname: indexes})
        async for index in ops_setup.app_db[collname].list_indexes():
            indexes.append(index)
    return result


@cli_operation
async def drop_collections(ops_setup):
    """CLI operation to drop (remove) collections.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Operation results.
    """
    tasks = []
    for collection in iter_collections():
        tasks.append(ops_setup.app_db.drop_collection(collection.name))
    return await multi(tasks)


# MANAGE USERS

@cli_operation
async def list_admin_users(ops_setup):
    """CLI operation to list admin users.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Result of command 'usersInfo' against the admin-database.
    """
    return await ops_setup.admin_db.command('usersInfo')


@cli_operation
async def setup_users(ops_setup):
    """CLI operation to setup application db users.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Results of commands 'createUser' against the application-database.
    """
    tasks = [ops_setup.app_db.command('createUser', ops_setup.settings.database_user_reader,
                                      pwd=ops_setup.settings.database_pass_reader,
                                      roles=['read']),
             ops_setup.app_db.command('createUser', ops_setup.settings.database_user_editor,
                                      pwd=ops_setup.settings.database_pass_editor,
                                      roles=['readWrite'])]
    return await multi(tasks)


@cli_operation
async def list_users(ops_setup):
    """CLI operation to list application database users.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Results of commands 'usersInfo' against the application-database.
    """
    return await ops_setup.app_db.command('usersInfo')


@cli_operation
async def remove_users(ops_setup):
    """CLI operation to remove application database users.

    :param ops_setup: Setup variables.
    :type ops_setup: :obj:`OperationsSetup`
    :returns: Results of commands 'dropUser' against the
              application-database with reader and editor credentials.
    """
    tasks = [ops_setup.app_db.command('dropUser', ops_setup.settings.database_user_reader),
             ops_setup.app_db.command('dropUser', ops_setup.settings.database_user_editor)]
    return await multi(tasks)


def configure():
    """Define and load configuration.

    :returns: Loaded configuration
    :rtype: :obj:`argparse.Namespace`
    """
    conf.load(prog='cdcagg_docstore.db_admin',
              env_var_prefix='CDCAGG_',
              description=__doc__,
              formatter_class=RawDescriptionHelpFormatter)
    conf.add_print_arg()
    conf.add_config_arg()
    add_cli_args(conf)
    conf.add('--database-user-admin', help='Username for MongoDB administration. If not '
             'submitted via configuration, the program will prompt admin credentials on '
             'startup.', env_var='DBUSER_ADMIN')
    conf.add('--database-pass-admin', help='Password for MongoDB administration. If not '
             'submitted via configuration, the program will prompt admin credentials on '
             'startup.', env_var='DBPASS_ADMIN')
    conf.add('operations', nargs='+', help='Operations to perform',
             choices=list(_ops.operations.keys()))
    return conf.get_conf()


def main():
    """Starts db_admin script from command line.

    Define configuration arguments & load them. Run every operation in
    IOLoop.

    :returns: 0 on success
    """
    settings = configure()
    if settings.print_configuration:
        print('Print active configuration and exit\n')
        conf.print_conf()
        return 0
    admin_username = settings.database_user_admin
    admin_password = settings.database_pass_admin
    if admin_username is None:
        print('Give database administrator username')
        admin_username = input('Admin username: ')
    if admin_password is None:
        print('Give database administrator password')
        admin_password = getpass('Admin password: ')
    _ops.setup(admin_username, admin_password, settings)
    for operation in settings.operations:
        op_fun = _ops.get(operation)
        IOLoop.current().run_sync(lambda fun=op_fun: fun())
    return 0


if __name__ == '__main__':
    sys.exit(main())
