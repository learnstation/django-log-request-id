from django.conf.urls import patterns, url
from testproject import views


urlpatterns = patterns(
    '',
    url(r'^$', views.test_view),
    url(r'^other_url/$', views.test_other_url_view),
)
