import collections
import logging
import django.dispatch
import structlog
from typing import Optional, Dict, Any, NamedTuple, List, Union
from django.http import HttpRequest
from django_structlog.middlewares.request import get_request_header
from django_structlog.signals import bind_extra_request_metadata


class _LoggingKey(NamedTuple):
    namespace: str
    bind_key: str
    header_key: str
    meta_key: str


class LoggingKeys(object):
    # Copied attributes from django-structlog
    REQUEST_ID = _LoggingKey(namespace='default', bind_key='request_id',
                             header_key='x-request-id', meta_key='HTTP_X_REQUEST_ID')
    CORRELATION_ID = _LoggingKey(namespace='default', bind_key='correlation_id',
                                 header_key='x-correlation-id', meta_key='HTTP_X_CORRELATION_ID')
    # Things haptik wants bound to log lines for filtering
    BUSINESS_ID = _LoggingKey(namespace='haptik', bind_key='business_id',
                              header_key='x-haptik-business-id', meta_key='HTTP_X_HAPTIK_BUSINESS_ID')
    BOT_NAME = _LoggingKey(namespace='haptik', bind_key='bot_name',
                           header_key='x-haptik-bot-name', meta_key='HTTP_X_HAPTIK_BOT_NAME')

    @classmethod
    def members(cls) -> List[_LoggingKey]:
        return [getattr(cls, attr) for attr in cls.__dict__ if isinstance(getattr(cls, attr), _LoggingKey)]


ALLOWED_BIND_KEYS = set()
NAMESPACE_TO_LOGGING_KEYS: Dict[str, List[_LoggingKey]] = collections.defaultdict(list)
for loggingkey in LoggingKeys.members():
    ALLOWED_BIND_KEYS.add(loggingkey.bind_key)
    NAMESPACE_TO_LOGGING_KEYS[loggingkey.namespace].append(loggingkey)
ALLOWED_BIND_KEYS = frozenset(ALLOWED_BIND_KEYS)


def add_module_and_lineno(logger: Union[logging.Logger, structlog.stdlib.BoundLogger],
                          name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add module and line number to the event dict
    Args:
        logger (structlog.stdlib.BoundLogger): stuctlog logger
        name (str): logger method (info/debug/..)
        event_dict (dict): log event dict
    Returns:
        event_dict (dict)
    """
    # see https://github.com/hynek/structlog/issues/253 for a feature request to get this done better
    # noinspection PyProtectedMember,PyUnresolvedReferences
    frame, module_str = structlog._frames._find_first_app_frame_and_name(additional_ignores=[__name__, 'logging'])
    event_dict['modline'] = f'{module_str}:{frame.f_lineno}'
    return event_dict


def unbind_extras(logger):
    # TODO: disabled to avoid too much logging, discuss with team
    logger.try_unbind('ip', 'user_id', 'username', 'request_path', 'task_id', 'parent_task_id')


def update_request_metadata(
        signal: django.dispatch.Signal,
        sender: Any,
        request: HttpRequest,
        logger: structlog.stdlib.BoundLogger,
        **kwargs
) -> None:
    """
    Receive signal bind_extra_request_metadata from django_structlog to bind haptik specific vars
    if they are available in the request headers

    Args:
        signal: reference to signal itself
        sender: reference to sender of the signal
        request: django HttpRequest instance
        logger: structlog logger instance
        **kwargs:
    """
    unbind_extras(logger)
    context = {}
    for loggingkey in NAMESPACE_TO_LOGGING_KEYS.get('haptik', []):
        request_header = get_request_header(request, loggingkey.header_key, loggingkey.meta_key)
        if request_header:
            context[loggingkey.bind_key] = request_header
    logger.bind(**context)


FOREIGN_PRE_CHAIN_PROCESSORS = (  # For logs being emitted from logging.Logger but use structlog's ProcessFormatter
    structlog.processors.TimeStamper(fmt='iso'),
    structlog.stdlib.add_log_level,
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
    structlog.processors.UnicodeDecoder(),
    add_module_and_lineno,
)


def configure_structlog_and_django_structlog():
    """
    Configure structlog settings
    """
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt='iso'),
            # structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(remove_positional_args=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            add_module_and_lineno,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    bind_extra_request_metadata.connect(update_request_metadata)
