import logging
from py12flogging.log_formatter import (
    setup_app_logging,
    set_ctx_populator
)
from kuha_common import (
    conf,
    server
)
from cdcagg_common import list_collection_names
from .http_api import get_app
from . import controller


_logger = logging.getLogger(__name__)


def configure():
    conf.load(prog='cdcagg_docstore', package='cdcagg_docstore', env_var_prefix='CDCAGG_')
    conf.add_print_arg()
    conf.add_config_arg()
    conf.add_loglevel_arg()
    conf.add('-p', '--port',
             help='Port to listen to',
             default=6001, type=int, env_var='DOCSTORE_PORT')
    conf.add('--api-version',
             help='HTTP API version gets prepended to URLs',
             default='v0', type=str, env_var='DOCSTORE_API_VERSION')
    server.add_cli_args()
    controller.add_cli_args(conf)
    settings = conf.get_conf()
    set_ctx_populator(server.serverlog_ctx_populator)
    setup_app_logging(conf.get_package(), loglevel=settings.loglevel, port=settings.port)
    return settings


def main():
    settings = configure()
    if settings.print_configuration:
        print('Print active configuration and exit\n')
        conf.print_conf()
        return 0
    try:
        db = controller.db_from_settings(settings)
        app = get_app(settings.api_version,
                      list_collection_names(),
                      db=db)
    except:
        _logger.exception('Exception in application setup')
        raise
    try:
        server.serve(app, settings.port, on_exit=db.close)
    except KeyboardInterrupt:
        _logger.warning('Shutdown by CTRL + C', exc_info=True)
    except:
        _logger.exception('Unhandled exception in main()')
        raise
    finally:
        _logger.info('Exiting')
    return 0
