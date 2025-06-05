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
"""Controller is responsible for handling the backend of Document Store.
"""
from kuha_common.document_store.records import (
    REC_STATUS_CREATED,
    REC_STATUS_DELETED
)
from kuha_document_store.database import (
    DocumentStoreDatabase,
    mongodburi
)
from kuha_document_store import validation

from cdcagg_common import record_by_collection_name
from cdcagg_common.records import Study

from cdcagg_docstore import iter_collections


class CDCAggDatabase(DocumentStoreDatabase):
    """CDC Aggregator Database class.

    Subclass of DocumentStoreDatabase. Overrides methods
    :meth:`_get_record_by_collection_name()` and :meth:`_prepare_validation_schema()`
    to support different records that parent class.
    """

    @staticmethod
    def _get_record_by_collection_name(name):
        return record_by_collection_name(name)

    @staticmethod
    async def _prepare_validation_schema(rec_class):
        if rec_class.get_collection() is not Study.get_collection():
            raise ValueError("Unsupported record class '%s'" % (rec_class,))
        metadata_schema_items = {
            **validation.default_schema_item(rec_class._metadata.attr_created.name),
            **validation.default_schema_item(rec_class._metadata.attr_updated.name),
            **validation.default_schema_item(rec_class._metadata.attr_deleted.name, nullable=True),
            **validation.str_enum_item(rec_class._metadata.attr_status.name, [REC_STATUS_CREATED,
                                                                              REC_STATUS_DELETED]),
            **validation.str_enum_item(rec_class._metadata.attr_schema_version.name, [rec_class.schema_version]),
            **validation.str_enum_item(rec_class._metadata.attr_cmm_type.name, [rec_class.cmm_type])
        }
        provenance_schema_items = {
            **validation.default_schema_item(rec_class._provenance.attr_base_url.name),
            **validation.default_schema_item(rec_class._provenance.attr_identifier.name),
            **validation.default_schema_item(rec_class._provenance.attr_datestamp.name),
            **validation.default_schema_item(rec_class._provenance.attr_metadata_namespace.name),
            **validation.default_schema_item(rec_class._provenance.sub_name.name),
            **validation.bool_schema_item(rec_class._provenance.attr_altered.name),
            **validation.bool_schema_item(rec_class._provenance.attr_direct.name)
        }
        base_schema = {
            **validation.identifier_schema_item(rec_class._aggregator_identifier.path),
            **validation.dict_schema_item(rec_class._metadata.path, metadata_schema_items),
            **validation.container_schema_item(rec_class._provenance.path, provenance_schema_items),
            **validation.default_schema_item(rec_class._direct_base_url.path, nullable=False, required=True)}
        return validation.RecordValidationSchema(
            rec_class,
            base_schema,
            validation.identifier_schema_item(rec_class.study_number.path),
            validation.uniquelist_schema_item(rec_class.persistent_identifiers.path),
            validation.bool_schema_item(rec_class.universes.attr_included.path)
        )


def db_from_settings(settings):
    """Instantiate CDCAggDatabase from loaded settings

    :param settings: loaded settings
    :type settings: :obj:`argparse.Namespace`
    :returns: Instance of CDCAggDatabase
    :rtype: :obj:`CDCAggDatabase`
    """
    reader_uri = mongodburi(*settings.replica, database=settings.database_name,
                            credentials=(settings.database_user_reader,
                                         settings.database_pass_reader))
    editor_uri = mongodburi(*settings.replica, database=settings.database_name,
                            credentials=(settings.database_user_editor,
                                         settings.database_pass_editor))
    return CDCAggDatabase(collections=list(iter_collections()),
                          name=settings.database_name,
                          reader_uri=reader_uri, editor_uri=editor_uri)


def add_cli_args(parser):
    """Adds CLI arguments to argument parser.

    :param parser: Argument parser
    :type parser: :obj:`configargparse.ArgumentParser`
    """
    parser.add('--replica',
               help='MongoDB replica replica host + port. Repeat for multiple replicas. For example: localhost:27017',
               env_var='DBREPLICAS',
               action='append',
               required=True,
               type=str)
    parser.add('--replicaset',
               help='MongoDB replica set name',
               env_var='DBREPLICASET',
               default='rs_cdcagg',
               type=str)
    parser.add('--database-name',
               help='Database name',
               default='cdcagg',
               env_var='DBNAME',
               type=str)
    parser.add('--database-user-reader',
               help='Username for reading from the database',
               default='reader',
               env_var='DBUSER_READER',
               type=str)
    parser.add('--database-pass-reader',
               help='Password for database-user-reader',
               default='reader',
               env_var='DBPASS_READER',
               type=str)
    parser.add('--database-user-editor',
               help='Username for editing the database',
               default='editor',
               env_var='DBUSER_EDITOR',
               type=str)
    parser.add('--database-pass-editor',
               help='Password for database-user-editor',
               default='editor',
               env_var='DBPASS_EDITOR',
               type=str)
