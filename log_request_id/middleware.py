import logging
import uuid

try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object
from log_request_id import local
from log_request_id import REQUEST_ID_HEADER
from log_request_id import REQUEST_ID_ORDER_NUMBER_HEADER


logger = logging.getLogger(__name__)


class RequestIDMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request_id, request_order_number = self._get_request_id(request)
        local.request = request
        local.request_id = request_id
        local.request_order_number = request_order_number
        self._write_request_log(request)

    def process_response(self, request, response):
        try:
            self._write_response_log(response)
        except Exception:
            pass
        finally:
            try:
                del local.request
                del local.request_id
                del local.request_order_number
            except AttributeError:
                pass
        return response

    def _write_request_log(self, request):
        # write some logger here
        logger.info(request.path)

    def _write_response_log(self, response):
        # write some logger here
        logger.info(response.status_code)

    def _get_request_id(self, request):
        try:
            request_id = request.META.get("HTTP_" + REQUEST_ID_HEADER.replace('-', '_'), None)
            if request_id:
                request_order_number = request.META.get("HTTP_" + REQUEST_ID_ORDER_NUMBER_HEADER.replace('-', '_'), "0")
                return request_id, request_order_number.zfill(4)
            else:
                return self._generate_id(), "0".zfill(4)
        except Exception:
            return self._generate_id(), 0

    def _generate_id(self):
        return uuid.uuid4().hex
