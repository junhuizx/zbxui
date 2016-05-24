from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from views import  IndexView, ReloadView, UserAddView

urlpatterns = [
    url(r'^$', IndexView.as_view(),name='index'),
    url(r'^adduser/$', UserAddView.as_view(),name='adduser'),
    url(r'^reload/$', ReloadView.as_view(),name='reload'),
]