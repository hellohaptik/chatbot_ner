from __future__ import absolute_import

import json
from functools import wraps

# Django
from django.http import HttpResponse

from chatbot_ner.config import ner_logger
# Local imports
from external_api.exceptions import APIHandlerException


class APIResponse(object):
    def __init__(self):
        self.success = False
        self.result = {}
        self.error = ''
        self.status_code = 200

    def toHttpResponse(self):
        """
        Generates a HttpResponse object with data in the specific response format
        and status_code as 200
        """
        body = {'success': self.success, 'result': self.result, 'error': self.error}
        return HttpResponse(json.dumps(body), content_type="application/json", status=self.status_code)


def external_api_response_wrapper(view_func):
    """
        This decorator is used to return responses for External API in a consistent format
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        response = APIResponse()
        try:
            response.result = view_func(request, *args, **kwargs)
            response.success = True

        except APIHandlerException as e:
            response.success = False
            response.error = e.error_msg

        except Exception as e:
            ner_logger.exception('General exception in external API')
            ner_logger.debug('*******************************')
            ner_logger.debug(request.path)
            ner_logger.debug(request.GET.dict())
            ner_logger.debug(request.body)
            ner_logger.debug(response.success)
            ner_logger.debug(response.result)
            ner_logger.debug(response.error)
            ner_logger.debug('*******************************')
            response.success = False
            response.error = 'Unknown error: {0}'.format(str(e))
            response.status_code = 500

        return response.toHttpResponse()

    return wrapper
