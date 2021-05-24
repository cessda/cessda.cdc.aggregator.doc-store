from cdcagg_common.records import Study
from .mdb import studies_collection


_COLLECTIONS = {Study.get_collection(): studies_collection}


def iter_collections():
    for coll in _COLLECTIONS.values():
        yield coll()
