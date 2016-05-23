#coding:utf-8

from django.shortcuts import render
import json
import urllib2
import datetime

from urllib2 import URLError
from django.http import HttpResponse
from django.conf import settings
from django.template import Context, loader
# Create your views here.

from django.views.generic import FormView, RedirectView, TemplateView, ListView, DetailView,View

class Zabbix:
    def __init__(self, idc, address, username, password):
        self.idc = idc
        self.address = address
        self.username = username
        self.password = password

        self.url = '%s/api_jsonrpc.php' % self.address
        self.header = {"Content-Type":"application/json"}

        self.user_login()

    def user_login(self):
        data = json.dumps({
                           "jsonrpc": "2.0",
                           "method": "user.login",
                           "params": {
                                      "user": self.username,
                                      "password": self.password
                                      },
                           "id": 0
                           })

        request = urllib2.Request(self.url, data)
        for key in self.header:
            request.add_header(key, self.header[key])

        try:
            result = urllib2.urlopen(request)
        except URLError as e:
            raise URLError
        else:
            response = json.loads(result.read())
            # import pprint
            # pprint.pprint(response)
            result.close()
            self.authID = response['result']
            return self.authID

    def trigger_get(self):
        data = json.dumps({
                           "jsonrpc":"2.0",
                           "method":"trigger.get",
                           "params": {
                                      "output": [
                                                "triggerid",
                                                "description",
                                                "priority",
                                                "lastchange"
                                                ],
                                      "filter": {
                                                 "value": 1
                                                 },
                                      "active":True,
                                      "selectHosts":"extend",
                                      "sortfield": "priority",
                                      "sortorder": "DESC"
                                    },
                           "auth": self.authID,
                           "id":1
        })

        request = urllib2.Request(self.url, data)
        for key in self.header:
            request.add_header(key, self.header[key])

        try:
            result = urllib2.urlopen(request)
        except URLError as e:
            raise URLError
        else:
            response = json.loads(result.read())
            result.close()
            results = response['result']
            issues = []
            if result:
                for result in results:
                    for host in result['hosts']:
                        issue = {'idc':self.idc,
                                 'host':host['host'],
                                 'priority':result['priority'],
                                 'description':result['description'],
                                 'lastchange':datetime.datetime.fromtimestamp((int(result['lastchange'])))}
                        issues.append(issue)
            return issues

    def triggerprototype_get(self):
        data = json.dumps({
                           "jsonrpc":"2.0",
                           "method":"triggerprototype.get",
                           "params": {
                                      "output": [
                                                "triggerid",
                                                "description",
                                                "priority",
                                                "lastchange"
                                                ],
                                      "filter": {
                                                 "value": 1
                                                 },
                                      "selectHosts":"extend",
                                      "sortfield": "priority",
                                      "sortorder": "DESC"
                                    },
                           "auth": self.authID,
                           "id":1
        })

        request = urllib2.Request(self.url, data)
        for key in self.header:
            request.add_header(key, self.header[key])

        try:
            result = urllib2.urlopen(request)
        except URLError as e:
            print "Error as ", e
        else:
            response = json.loads(result.read())
            result.close()
            results = response['result']
            issues = []
            if result:
                for result in results:
                    for host in result['hosts']:
                        issue = {'idc':self.idc,
                                 'host':host['host'],
                                 'priority':result['priority'],
                                 'description':result['description'],
                                 'lastchange':datetime.datetime.fromtimestamp((int(result['lastchange'])))}
                        issues.append(issue)
            return issues

class IndexView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args, **kwargs)
        zabbixs = []
        issues = []
        for zabbix in settings.ZABBIX_LIST:
            zabbixs.append(Zabbix(idc=zabbix['idc'], address=zabbix['address'], username=zabbix['username'], password=zabbix['password']))

        for zabbix in zabbixs:
            issues.extend(zabbix.trigger_get())
            # issues.extend(zabbix.triggerprototype_get())

        issues.sort(key=lambda k:k['lastchange'], reverse=True)
        context['issues'] = issues
        context['idcs'] = settings.ZABBIX_LIST

        return context


class LoginView(TemplateView):
    template_name = 'login.html'

class ReloadView(View):

    def get(self, request, *args, **kwargs):
        try:
            zabbixs = []
            issues = []
            for zabbix in settings.ZABBIX_LIST:
                zabbixs.append(Zabbix(idc=zabbix['idc'], address=zabbix['address'], username=zabbix['username'], password=zabbix['password']))

            for zabbix in zabbixs:
                issues.extend(zabbix.trigger_get())
                # issues.extend(zabbix.triggerprototype_get())

            issues.sort(key=lambda k:k['lastchange'], reverse=True)

            context = Context({'issues':issues})

            issues = loader.get_template('reload.html').render(context)
            data = {'flag':'success', 'issues':issues}

        except Exception, error:
            data = {'flag':'fail','issues':''}

        return HttpResponse(json.dumps(data), content_type='application/json')