import logging
import uuid
import time
import datetime
import json
import urllib3


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
        if request.path[:5] != "/api/":
            return
        global_request_id, parent_request_id, current_request_id, deep_num, index_num = self._get_request_id(request)

        local.request = request
        local.global_request_id = global_request_id
        local.current_request_id = current_request_id
        local.deep_num = deep_num
        local.index_num = 0

        request.nscloud_parent_request_id = parent_request_id
        request.nscloud_index_num = index_num
        request.nscloud_global_request_id = global_request_id
        request.nscloud_current_request_id = current_request_id
        request.nscloud_deep_num = deep_num
        self._request_pretreatment(request)

    def process_response(self, request, response):
        if request.path[:5] != "/api/":
            return response
        try:
            self._response_pretreatment(request, response)
        except Exception:
            pass
        finally:
            self._local_data_handle(request)
            try:
                del local.request
                del local.global_request_id
                del local.current_request_id
                del local.deep_num
                del local.index_num
            except AttributeError:
                pass
        return response

    def _get_request_data(self, request):
        data = {}
        try:
            data = request.data
            if data:
                return str(data)
        except Exception as e:
            pass
        try:
            data = request.query_params.dict()
            if data:
                return str(data)
        except Exception as e:
            pass
        try:
            data = dict(request.GET)
            if data:
                return str(data)
        except Exception as e:
            pass
        try:
            data = dict(request.POST)
            if data:
                return str(data)
        except Exception as e:
            pass
        return str(data)

    def _request_pretreatment(self, request):
        request.nscloud_start_time = datetime.datetime.utcnow()
        request.nscloud_remote_ip = get_remote_ip(request)
        request.nscloud_path = request.path
        request.nscloud_method = request.method
        request.nscloud_request_data = self._get_request_data(request)
        request.nscloud_module = None
        request.nscloud_api_type = "other"
        try:
            request.nscloud_module = request.path.split("/")[3]
            request.nscloud_api_type = request.path.split("/")[2]
        except Exception as e:
            pass

    def _response_pretreatment(self, request, response):
        request.nscloud_end_time = datetime.datetime.utcnow()
        request.nscloud_http_status = response.status_code
        request.nscloud_response_data = ""
        request.nscloud_nscloud_status = None
        try:
            request.nscloud_response_data = str(response.content)
            request.nscloud_nscloud_status = json.loads(response.content).get("status")
        except Exception as e:
            pass

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
        s = uuid.uuid4().hex
        return s

    def _local_data_handle(self, request):
        data = {
            "global_id": request.nscloud_global_request_id,
            "parnet_id": request.nscloud_parent_request_id,
            "current_id": request.nscloud_current_request_id,
            "deep_num": request.nscloud_deep_num,
            "index_num": request.nscloud_index_num,
            "http_status": request.nscloud_http_status,
            "nscloud_status": request.nscloud_nscloud_status,
            "method": request.nscloud_method,
            "path": request.nscloud_path,
            "module": request.nscloud_module,
            "api_type": request.nscloud_api_type,
            "remote_ip": request.nscloud_remote_ip,
            "request_data": request.nscloud_request_data,
            "response_data": request.nscloud_response_data,
            "taking": (request.nscloud_end_time - request.nscloud_start_time).microseconds,
            "child_num": local.index_num,
            "create_time": int(time.time())
        }
        print json.dumps(data, indent=2)

        http = urllib3.PoolManager()
        encoded_data = json.dumps(data).encode('utf-8')
        r = http.request(
            'POST',
            'http://127.0.0.1:8000/record',
            body=encoded_data,
            headers={'Content-Type': 'application/json'})
        print r.data
