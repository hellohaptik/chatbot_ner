from __future__ import absolute_import

import json
from functools import wraps

# Django
from django.http import HttpResponse

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
            response.status_code = 500
            response.error = str(e)
            raise e

        return response.toHttpResponse()

    return wrapper
