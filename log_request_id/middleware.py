import logging
import uuid
import time
import datetime
import json


try:
    from django.utils.deprecation import MiddlewareMixin
except ImportError:
    MiddlewareMixin = object
from log_request_id import local
from log_request_id import GLOBAL_REQUEST_ID_HEADER
from log_request_id import PARENT_REQUEST_ID_HEADER
from log_request_id import REQUEST_ID_NUMBER_HEADER


logger = logging.getLogger(__name__)


def get_remote_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        remote_address = request.META['HTTP_X_FORWARDED_FOR']
    else:
        remote_address = request.META['REMOTE_ADDR']
    if remote_address:
        remote_address = remote_address.split(",")[0]
    return remote_address


class RequestIDMiddleware(MiddlewareMixin):

    def process_request(self, request):
        global_request_id, parent_request_id, current_request_id, deep_num, index_num = self._get_request_id(request)

        local.request = request
        local.global_request_id = global_request_id
        local.current_request_id = current_request_id
        local.deep_num = deep_num
        local.index_num = 0

        self.parent_request_id = parent_request_id
        self.index_num = index_num
        self.global_request_id = global_request_id
        self.current_request_id = current_request_id
        self.deep_num = deep_num
        self._request_pretreatment(request)

    def process_response(self, request, response):
        try:
            self._response_pretreatment(response)
        except Exception:
            pass
        finally:
            self._local_data_handle()
            try:
                del local.request
                del local.global_request_id
                del local.current_request_id
                del local.deep_num
                del local.index_num
            except AttributeError:
                pass
        return response

    def _request_pretreatment(self, request):
        self.start_time = datetime.datetime.utcnow()
        self.remote_ip = get_remote_ip(request)
        self.path = request.path
        self.method = request.method
        self.request_data = str(request.data or request.query_params.dict())
        self.module = None
        try:
            self.module = self.path.split("/")[2]
        except Exception as e:
            print e

    def _response_pretreatment(self, response):
        self.end_time = datetime.datetime.utcnow()
        self.http_status = response.status_code
        self.response_data = ""
        self.nscloud_status = None
        try:
            self.response_data = str(response.data)
            self.nscloud_status = response.data.get("status")
        except Exception as e:
            print e

    def _get_request_id(self, request):
        try:
            global_request_id = request.META.get("HTTP_" + GLOBAL_REQUEST_ID_HEADER.replace('-', '_'), None)
            if global_request_id:
                parent_request_id = request.META.get("HTTP_" + PARENT_REQUEST_ID_HEADER.replace('-', '_'), None)
                request_id_number = request.META.get("HTTP_" + REQUEST_ID_NUMBER_HEADER.replace('-', '_'), None)
                if request_id_number:
                    deep_num = int(request_id_number[:16])
                    index_num = int(request_id_number[16:])
                return global_request_id, parent_request_id, self._generate_id(), deep_num, index_num
            else:
                return self._generate_id(), None, self._generate_id(), 0, 0
        except Exception:
            return self._generate_id(), None, self._generate_id(), 0, 0

    def _generate_id(self):
        return uuid.uuid4().hex

    def _local_data_handle(self):
        data = {
            "global_id": self.global_request_id,
            "parnet_id": self.parent_request_id,
            "current_id": self.current_request_id,
            "deep_num": self.deep_num,
            "index_num": self.index_num,
            "http_status": self.http_status,
            "nscloud_status": self.nscloud_status,
            "method": self.method,
            "path": self.path,
            "module": self.module,
            "remote_ip": self.remote_ip,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "taking": (self.end_time - self.start_time).microseconds,
            "create_time": int(time.time())
        }
        print json.dumps(data, indent=2)
