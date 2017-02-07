import logging
import time

from log_request_id import local


class RequestIDFilter(logging.Filter):

    def filter(self, record):
        record.request_id = getattr(local, 'request_id', None)
        return True


class UnixTimeFilter(logging.Filter):

    def filter(self, record):
        record.unix_time = str(time.time())
        return True


class RequestOrderNumberFilter(logging.Filter):

    def filter(self, record):
        record.request_order_number = getattr(local, 'request_order_number', None)
        return True
