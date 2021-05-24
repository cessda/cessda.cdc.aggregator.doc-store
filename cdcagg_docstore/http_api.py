from kuha_common.server import WebApplication
from kuha_document_store.handlers import (
    RestApiHandler,
    QueryHandler
)


def get_app(api_version, collections, **kw):
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
