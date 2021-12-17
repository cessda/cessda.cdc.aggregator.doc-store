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
"""This package contains modules that build the DocStore server.

DocStore provides HTTP APIs for full CRUD support via REST API and
flexible query support via Query API. The use of the DocStore HTTP
APIs are documented in OpenAPI 3.0 format. OpenAPI documentation
resides in package root folder in file `openapi.json`.

All responses from DocStore are streamed to the requester. Care must
be taken to handle the streaming requests correctly. The Aggregator
components use Kuha Common client
(:mod:`kuha_common.document_store.client`) internally to support
streaming responses. Python programs can use the same approach to
support streaming responses.
"""
from cdcagg_common.records import Study
from .mdb import studies_collection


_COLLECTIONS = {Study.get_collection(): studies_collection}


def iter_collections():
    """Iterates every defined mdb collection.

    Currently only collection that is defines is :func:`cdcagg_docstore.mdb.studies_collection`

    :returns: Generator that yields collections.
    :rtype: iterable
    """
    for coll in _COLLECTIONS.values():
        yield coll()
