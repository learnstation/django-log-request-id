import logging
from django.http import HttpResponse
import requests

logger = logging.getLogger("log_request_id.middleware")


def test_view(request):
    requests.get("http://127.0.0.1:8000/other_url/?other_url=123", headers={"self_header": "value"})
    logger.debug("A wild log message appears index!")
    return HttpResponse('ok')


def test_other_url_view(request):
    logger.debug("A wild log message appears other url!")
    return HttpResponse('other_url')
