#coding:utf-8

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from views import *

urlpatterns = [
    url(r'^$', IndexView.as_view(),name='index'),
    url(r'^adduser/$', UserAddView.as_view(),name='adduser'),
    url(r'^reload/$', ReloadView.as_view(),name='reload'),

    url(r'^top/$', TopView.as_view(),name='top'),
    url(r'^top-reload/$', TopReloadView.as_view(),name='top-reload'),
]