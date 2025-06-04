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

"""MongoDB properties"""
from collections import namedtuple
from pymongo import (
    ASCENDING,
    DESCENDING
)
from cdcagg_common import (
    records,
    mdb_const
)


_COMMON_ISODATE_FIELDS = [
    records.RecordBase._metadata.attr_updated.path,
    records.RecordBase._metadata.attr_deleted.path,
    records.RecordBase._metadata.attr_created.path
]
_COMMON_INDEXES = [[(records.RecordBase._metadata.attr_updated.path, DESCENDING)]]
_COMMON_OBJECTID_FIELDS = [records.RecordBase._id.path]


def _collection_validator(collection_name, record_class, required=None):
    required = required or []
    required.extend([attr.path for attr in [
        record_class._metadata.attr_created,
        record_class._metadata.attr_updated,
        record_class._metadata.attr_deleted,
        record_class._metadata.attr_cmm_type,
        record_class._metadata.attr_schema_version,
        record_class._metadata.attr_status
    ]])
    properties = {
        record_class._metadata.attr_created.path: {
            'bsonType': mdb_const.MDB_TYPE_DATE,
            'description': 'Must be date and is required'
        },
        record_class._metadata.attr_updated.path: {
            'bsonType': mdb_const.MDB_TYPE_DATE,
            'description': 'Must be date and is required'
        },
        record_class._metadata.attr_deleted.path: {
            'bsonType': [mdb_const.MDB_TYPE_DATE, mdb_const.MDB_TYPE_NULL],
            'description': 'Must be date or null and is required'
        },
        record_class._metadata.attr_schema_version.path: {
            'bsonType': mdb_const.MDB_TYPE_STRING,
            'description': 'Must be double and is required'
        },
        record_class._metadata.attr_cmm_type.path: {
            'bsonType': mdb_const.MDB_TYPE_STRING,
            'pattern': "^{cmm_type}$".format(cmm_type=record_class.cmm_type),
            'description': 'Fixed string %s and is required' % (record_class.cmm_type,)
        }
    }
    return {
        '$jsonSchema': {
            'bsonType': 'object',
            'required': required,
            'properties': properties
        }
    }


Collection = namedtuple('Collection',
                        'name, validators, indexes_unique, '
                        'indexes, isodate_fields, object_id_fields')
"""Collection object contains properties of a MongoDB collection.

:param str name: Collection name.
:param dict validators: MongoDB validators for collection.
:param list indexes_unique: List of unique MongoDB indexes for collection.
:param list indexes: List of MongoDB indexes for collection.
:param list isodate_fields: List of isodate fields for collection.
:param list object_id_fields: List of collection's object ID fields.
"""


def _init_collection(name, validators, indexes_unique):
    return Collection(name=name, validators=validators, indexes_unique=indexes_unique,
                      indexes=list(_COMMON_INDEXES), isodate_fields=list(_COMMON_ISODATE_FIELDS),
                      object_id_fields=list(_COMMON_OBJECTID_FIELDS))


def studies_collection():
    """Initiate and return studies collection.

    :returns: Studies collection object.
    :rtype: :obj:`Collection`
    """
    validators = _collection_validator(records.Study.get_collection(),
                                       records.Study,
                                       required=[records.Study.study_number.path])
    indexes_unique = [[(records.Study.study_number.path, ASCENDING)],
                      [(records.Study._aggregator_identifier.path, ASCENDING)]]
    return _init_collection(records.Study.get_collection(), validators, indexes_unique)
