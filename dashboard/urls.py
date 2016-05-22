from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from views import  IndexView,LoginView,ReloadView

urlpatterns = [
    url(r'^$', IndexView.as_view(),name='index'),
    url(r'^login/$', LoginView.as_view(),name='login'),
    url(r'^reload/$', ReloadView.as_view(),name='reload'),
]