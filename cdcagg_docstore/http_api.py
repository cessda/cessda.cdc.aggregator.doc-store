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
"""Defines the HTTP API for DocStore
"""

from kuha_common.server import WebApplication
from kuha_document_store.handlers import (
    RestApiHandler,
    QueryHandler
)


def get_app(api_version, collections, **kw):
    """Format and return WebApplication

    Api version and collections are used to build routes to
    handlers. The handlers and optional keyword arguments are
    passed onto the WebApplication class.

    WebApplication is a subclass of :class:`tornado.web.Application`.

    :param str api_version: DocStore API version. Gets prepended to
                            all routes.
    :param list collections: Available collections. Every collection
                             gets its own route to REST and QUERY
                             handlers.
    :returns: WebApplication object.
    :rtype: :obj:`kuha_common.server.WebApplication`
    """
    handlers = []

    def add_route(route_str, handler, **kw_):
        kw_.update({'api_version': api_version})
        full_route_str = r'/{api_version}/' + route_str
        handlers.append((full_route_str.format(**kw_), handler))

    collections = '|'.join(collections)
    add_route(r"(?P<collection>{collections})/?", RestApiHandler, collections=collections)
    add_route(r"(?P<collection>{collections})/(?P<resource_id>\w+)", RestApiHandler,
              collections=collections)
    add_route(r"query/(?P<collection>{collections})/?", QueryHandler,
              collections=collections)
    return WebApplication(handlers=handlers, **kw)
