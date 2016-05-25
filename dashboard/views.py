#coding:utf-8

from django.shortcuts import render
import json
import urllib2
import datetime

from django.forms.utils import ErrorList
from django.http import HttpResponse
from django.conf import settings
from django.template import Context, loader
from django.core.urlresolvers import reverse_lazy
from django.views.generic import FormView, RedirectView, TemplateView, ListView, DetailView,View

from forms import UserForm

from pyzabbix import ZabbixAPI


def get_usergroups(group):
    if group == '0':
        return u'监控管理员'
    elif group == '1':
        return u'Ceph管理员'
    elif group == '2':
        return u'HA管理员'
    elif group == '3':
        return u'MySQL管理员'
    elif group == '4':
        return u'OpenStack管理员'
    elif group == '5':
        return u'RabbitMQ管理员'
    elif group == '6':
        return u'经理'
    elif group == '7':
        return u'运营维护'
    elif group == '8':
        return u'其他'
    else:
        pass


# Create your views here.
class ZabbixClinet(object):
    def __init__(self, idc, address, username, password):
        self.idc = idc
        try:
            self.zbx_api = ZabbixAPI(address, username, password)
        except Exception, error:
            raise Exception

    def trigger_get(self):
        results = self.zbx_api.trigger.get(output=["triggerid", "description", "priority", "lastchange"],
                                           filter={"value": 1},
                                           active=True,
                                           selectHosts="extend")

        triggers = []
        if results:
            for result in results:
                for host in result['hosts']:
                    trigger = {'idc': self.idc,
                               'host': host['host'],
                               'priority': result['priority'],
                               'description': result['description'],
                               'lastchange': datetime.datetime.fromtimestamp((int(result['lastchange'])))}
                    triggers.append(trigger)

        return triggers

    def triggerprototype_get(self):
        results = self.zbx_api.triggerprototype.get(output=["triggerid", "description", "priority", "lastchange"],
                                           filter={"value": 1},
                                           active=True,
                                           selectHosts="extend")

        triggers = []
        if results:
            for result in results:
                for host in result['hosts']:
                    trigger = {'idc': self.idc,
                               'host': host['host'],
                               'priority': result['priority'],
                               'description': result['description'],
                               'lastchange': datetime.datetime.fromtimestamp((int(result['lastchange'])))}
                    triggers.append(trigger)

        return triggers

    def item_get(self, applications, keywords):
        results = self.zbx_api.item.get(output="extend",
                                        application=applications,
                                        search={'key_': keywords},
                                        sortfield='lastvalue')

        lastvalues = []
        if results:
            for result in results:
                lastvalue={'idc': self.idc,
                           'uuid': result['name'].split(' ')[0],
                           'lastclock': result['lastclock'],
                           'lastvalue': result['lastvalue']}
                lastvalues.append(lastvalue)

        return lastvalues

    def user_create(self, user):
        '''
        Create user with media type and group
        :param user:{
                        'username':'zabbixtest',
                        'name':'Zabbix',
                        'email':'zabbix@newtouch.com',
                        'tel':'18888888888',
                        'usergroups':['Zabbix administrators']}

        :return: user id
        '''
        user_medias = []
        mediatype_email = self.zbx_api.mediatype.get(filter={'description': 'Email'})
        if len(mediatype_email) == 1:
            user_medias.append({'mediatypeid': mediatype_email[0]['mediatypeid'],
                                'sendto': user['email'],
                                'active': 0,
                                'severity': 63,
                                'period': '1-7,00:00-24:00'})

        mediatype_tel = self.zbx_api.mediatype.get(filter={'description': 'SMS-Script'})

        if len(mediatype_tel) == 1:
            user_medias.append({'mediatypeid': mediatype_tel[0]['mediatypeid'],
                                'sendto': user['tel'],
                                'active': 0,
                                'severity': 63,
                                'period': '1-7,00:00-24:00'})

        usrgrps = []

        print user

        if user.get('usergroups'):
            for usergroup in user['usergroups']:
                print usergroup
                group = self.zbx_api.usergroup.get(filter={'name': usergroup})
                if len(group) == 1:
                    usrgrps.append({'usrgrpid': group[0]['usrgrpid']})

        user_id = self.zbx_api.user.create({'alias': user['username'],
                                            'name': user['name'],
                                            'passwd': 'newtouch',
                                            'usrgrps':usrgrps,
                                            'user_medias': user_medias})

        return user_id

class IndexView(TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, *args, **kwargs):
        context = super(IndexView, self).get_context_data(*args, **kwargs)
        zabbixs = []
        issues = []
        for zabbix in settings.ZABBIX_LIST:
            zabbixs.append(ZabbixClinet(idc=zabbix['idc'], address=zabbix['address'], username=zabbix['username'], password=zabbix['password']))

        for zabbix in zabbixs:
            issues.extend(zabbix.trigger_get())
            # issues.extend(zabbix.triggerprototype_get())

        issues.sort(key=lambda k:k['lastchange'], reverse=True)
        context['issues'] = issues
        context['updatetime'] = datetime.datetime.now()
        context['idcs'] = settings.ZABBIX_LIST

        return context

class ReloadView(View):
    def get(self, request, *args, **kwargs):
        try:
            zabbixs = []
            issues = []
            for zabbix in settings.ZABBIX_LIST:
                zabbixs.append(ZabbixClinet(idc=zabbix['idc'], address=zabbix['address'], username=zabbix['username'], password=zabbix['password']))

            for zabbix in zabbixs:
                issues.extend(zabbix.trigger_get())
                # issues.extend(zabbix.triggerprototype_get())

            issues.sort(key=lambda k:k['lastchange'], reverse=True)

            context = Context({'issues':issues,'updatetime':datetime.datetime.now()})

            issues = loader.get_template('reload.html').render(context)
            data = {'flag':'success', 'issues':issues}

        except Exception, error:
            data = {'flag':'fail','issues':''}

        return HttpResponse(json.dumps(data), content_type='application/json')


class UserAddView(FormView):
    template_name = 'add_user.html'
    form_class = UserForm
    success_url = reverse_lazy('zabbix:index')

    def post(self, request, *args, **kwargs):
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            tele = form.cleaned_data['tele']
            email = form.cleaned_data['email']
            usergroups = form.cleaned_data['usergroups']
            key = form.cleaned_data['key']

            if key != 'ac5b4a2f96cc':
                errors = form._errors.setdefault("key", ErrorList())
                errors.append(u"认证码不正确，请向监控管理员索要！")
                return self.form_invalid(form=form)

            zabbixs =[]
            for zabbix in settings.ZABBIX_LIST:
                zabbixs.append(ZabbixClinet(idc=zabbix['idc'], address=zabbix['address'], username=zabbix['username'], password=zabbix['password']))

            for zabbix in zabbixs:
                zabbix.user_create(user={'username':username, 'name':name, 'tel':tele, 'email':email, 'usergroups':[get_usergroups(usergroup) for usergroup in usergroups]})

        else:
            return self.form_invalid(form=form)

        return super(UserAddView, self).post(request, *args, **kwargs)