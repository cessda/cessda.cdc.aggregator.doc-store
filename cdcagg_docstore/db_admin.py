"""Admin operations to setup and manage CDC OAI Aggregator MongoDB.

For initial setup run the following against a mongodb replicaset::

    python -m cdcagg_docstore.db_admin initiate_replicaset setup_database setup_collections setup_users

Setup an empty database into an existing replicaset::

    python -m cdcagg_docstore.db_admin setup_database setup_collections setup_users
"""
# STD
import sys
from collections import namedtuple
from pprint import pprint
from getpass import getpass
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


OperationsSetup = namedtuple('client', 'admin_credentials, settings, client, app_db, admin_db')


class DBOperations:

    def __init__(self):
        self.operations = {}
        self.settings = None

    def setup(self, admin_username, admin_password, settings):
        conn_uri = mongodburi(*settings.replica, database='admin',
                              credentials=(admin_username, admin_password),
                              options=[('replicaSet', settings.replicaset)])
        client = MotorClient(conn_uri)
        self.settings = OperationsSetup(admin_credentials=(admin_username, admin_password),
                                        settings=settings, client=client,
                                        app_db=client[settings.database_name],
                                        admin_db=client['admin'])

    def get(self, name):
        return self.operations[name]


_ops = DBOperations()


def cli_operation(func):
    op_str = func.__name__

    async def wrapper():
        print('Running operation %s ...' % (op_str,))
        result = await func(_ops.settings)
        print('%s result:' % (op_str,))
        pprint(result)
        return result
    _ops.operations[op_str] = wrapper
    return wrapper


# MANAGE REPLICAS

@cli_operation
async def initiate_replicaset(ops_setup):
    replset_members = [{'_id': index, 'host': host} for index, host in enumerate(ops_setup.settings.replica)]
    client = MotorClient(mongodburi(ops_setup.settings.replica[0], database='admin',
                                    credentials=ops_setup.admin_credentials))
    return await client.admin.command('replSetInitiate', {
        '_id': ops_setup.settings.replicaset,
        'members': replset_members})


@cli_operation
async def show_replicaset_status(ops_setup):
    return await ops_setup.admin_db.command('replSetGetStatus')


@cli_operation
async def show_replicaset_config(ops_setup):
    return await ops_setup.admin_db.command('replSetGetConfig')


# MANAGE DATABASES

@cli_operation
async def setup_database(ops_setup):
    return ops_setup.client.get_database(name=ops_setup.settings.database_name)


@cli_operation
async def list_databases(ops_setup):
    return await ops_setup.client.list_database_names()


@cli_operation
async def drop_database(ops_setup):
    await ops_setup.client.drop_database(ops_setup.settings.database_name)


# MANAGE COLLECTIONS

@cli_operation
async def setup_collections(ops_setup):
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
    return await ops_setup.app_db.list_collection_names()


@cli_operation
async def list_collection_indexes(ops_setup):
    result = {}
    for collname in await ops_setup.app_db.list_collection_names():
        indexes = []
        result.update({collname: indexes})
        async for index in ops_setup.app_db[collname].list_indexes():
            indexes.append(index)
    return result


@cli_operation
async def drop_collections(ops_setup):
    tasks = []
    for collection in iter_collections():
        tasks.append(ops_setup.app_db.drop_collection(collection.name))
    return await multi(tasks)


# MANAGE USERS

@cli_operation
async def list_admin_users(ops_setup):
    return await ops_setup.admin_db.command('usersInfo')


@cli_operation
async def setup_users(ops_setup):
    tasks = [ops_setup.app_db.command('createUser', ops_setup.settings.database_user_reader,
                                      pwd=ops_setup.settings.database_pass_reader,
                                      roles=['read']),
             ops_setup.app_db.command('createUser', ops_setup.settings.database_user_editor,
                                      pwd=ops_setup.settings.database_pass_editor,
                                      roles=['readWrite'])]
    return await multi(tasks)


@cli_operation
async def list_users(ops_setup):
    return await ops_setup.app_db.command('usersInfo')


@cli_operation
async def remove_users(ops_setup):
    tasks = [ops_setup.app_db.command('dropUser', ops_setup.settings.database_user_reader),
             ops_setup.app_db.command('dropUser', ops_setup.settings.database_user_editor)]
    return await multi(tasks)


def configure():
    parser = conf.load(prog='cdcagg_docstore.db_admin',
                       description=__doc__)
    conf.add_print_arg()
    conf.add_config_arg()
    add_cli_args(parser)
    conf.add('operations', nargs='+', help='Operations to perform',
             choices=list(_ops.operations.keys()))
    return conf.get_conf()


def main():
    settings = configure()
    if settings.print_configuration:
        print('Print active configuration and exit\n')
        conf.print_conf()
        return 0
    print('Give database administrator credentials')
    admin_username = input('Admin username: ')
    admin_password = getpass('Admin password: ')
    _ops.setup(admin_username, admin_password, settings)
    for operation in settings.operations:
        op_fun = _ops.get(operation)
        IOLoop.current().run_sync(lambda fun=op_fun: fun())
    return 0


if __name__ == '__main__':
    sys.exit(main())
