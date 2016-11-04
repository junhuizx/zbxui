#coding:utf-8

from django.shortcuts import render
import json
import urllib2
import datetime
import logging
import MySQLdb

from django.forms.utils import ErrorList
from django.http import HttpResponse
from django.conf import settings
from django.template import Context, loader
from django.core.urlresolvers import reverse_lazy
from django.views.generic import FormView, RedirectView, TemplateView, ListView, DetailView,View

from forms import UserForm

from pyzabbix import ZabbixAPI


class CustomOverView(object):
    def __init__(self, overview):
        self.update_time = overview[1]
        self.vcpus = overview[2]
        self.vcpus_used = overview[3]
        self.memory = overview[4] * 1024 * 1024
        self.memory_used = overview[5] * 1024 * 1024
        self.vms = overview[6] - 4
        self.vms_running = overview[7]
        self.region = overview[8]


def get_overview():
    overviews = list()
    conn = None
    while conn is None:
        try:
            conn = MySQLdb.connect(host='127.0.0.1', user='ops', passwd='123456', db='hypervisors')
        except Exception, error:
            logging.error("Connect vm_data mysql error, and try again!(%s)" % str(error))
            conn = None

    cursor = conn.cursor()

    sql = '''SELECT * FROM hypervisors.status ORDER BY -id limit {};'''.format(2)

    cursor.execute(sql)
    overviews_sql = cursor.fetchall()

    conn.close()

    for overview_sql in overviews_sql:
        overview = CustomOverView(overview_sql)
        overviews.append(overview)

    return overviews


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
        self.address = address
        try:
            self.zbx_api = ZabbixAPI(address)
            self.zbx_api.login(username, password)
        except Exception, error:
            # logging.warning(error)
            raise Exception

    def user_logout(self):
        return self.zbx_api.user.logout()

    def trigger_get(self):
        results = self.zbx_api.trigger.get(output=["triggerid", "description", "priority", "lastchange"],
                                           filter={"value": 1},
                                           active=True,
                                           selectHosts="extend",
                                           selectItems='extend')

        triggers = []
        if results:
            for result in results:
                for host in result['hosts']:
                    trigger = {'idc': self.idc,
                               'url' : self.address,
                               'host': host['host'],
                               'itemid': result['items'][0]['itemid'],
                               'itemtype': result['items'][0]['data_type'],
                               'priority': result['priority'],
                               'description': result['description'],
                               'lastchange': datetime.datetime.fromtimestamp((int(result['lastchange'])))}
                    triggers.append(trigger)

        return triggers

    def triggerprototype_get(self):
        results = self.zbx_api.triggerprototype.get(output=["triggerid", "description", "priority", "lastchange"],
                                           filter={"value": 1},
                                           active=True,
                                           selectHosts="extend",
                                                    selectItems='extend')

        triggers = []
        if results:
            for result in results:
                for host in result['hosts']:
                    trigger = {'idc': self.idc,
                               'url' : self.address,
                               'host': host['host'],
                               'itemid': result['items'][0]['itemid'],
                               'itemtype': result['items'][0]['data_type'],
                               'priority': result['priority'],
                               'description': result['description'],
                               'lastchange': datetime.datetime.fromtimestamp((int(result['lastchange'])))}
                    triggers.append(trigger)

        return triggers

    def item_get(self, applications, keywords):
        results = self.zbx_api.item.get(output="extend",
                                        application=applications,
                                        search={'name': keywords},
                                        sortfield='name')

        return results

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

        # print user

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
            try:
                zabbix = ZabbixClinet(idc=zabbix['idc'],
                                      address=zabbix['address'],
                                      username=zabbix['username'],
                                      password=zabbix['password'])
                zabbixs.append(zabbix)
            except Exception:
                issues.append({'idc': zabbix['idc'],
                               'url' : zabbix['address'],
                               'host': 'zabbix server',
                               'itemid': '99999999',
                               'itemtype': '1',
                               'priority': '5',
                               'description': 'zabbix server API 无法正常访问',
                               'lastchange': datetime.datetime.now()})


        for zabbix in zabbixs:
            issues.extend(zabbix.trigger_get())
            zabbix.user_logout()

        issues.sort(key=lambda k:k['lastchange'], reverse=True)
        context['issues'] = issues
        context['idcs'] = settings.ZABBIX_LIST
        # context['overviews'] = get_overview()

        return context

class ReloadView(View):
    def get(self, request, *args, **kwargs):
        try:
            zabbixs = []
            issues = []
            for zabbix in settings.ZABBIX_LIST:
                # zabbixs.append(ZabbixClinet(idc=zabbix['idc'], address=zabbix['address'], username=zabbix['username'], password=zabbix['password']))
                try:
                    zabbix = ZabbixClinet(idc=zabbix['idc'],
                                          address=zabbix['address'],
                                          username=zabbix['username'],
                                          password=zabbix['password'])
                    zabbixs.append(zabbix)
                except Exception:
                    issues.append({'idc': zabbix['idc'],
                                   'url': zabbix['address'],
                                   'host': 'zabbix server',
                                   'itemid': '99999999',
                                   'itemtype': '1',
                                   'priority': '5',
                                   'description': 'zabbix server API 无法正常访问',
                                   'lastchange': datetime.datetime.now()})

            for zabbix in zabbixs:
                issues.extend(zabbix.trigger_get())
                # issues.extend(zabbix.triggerprototype_get())
                zabbix.user_logout()

            issues.sort(key=lambda k:k['lastchange'], reverse=True)

            context = Context({'issues':issues})

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
                zabbix.user_logout()

        else:
            return self.form_invalid(form=form)

        return super(UserAddView, self).post(request, *args, **kwargs)

class OverView(object):
    def __init__(self, idc, total, running):
        self.idc = idc
        self.total = total
        self.running = running
        self.other = total - running

class Speed(object):
    def __init__(self, idc, uuid, clock, speed):
        self.idc = idc
        self.uuid = uuid
        self.clock = clock
        self.speed = speed

class Top(object):
    def __init__(self,speeds):
        self.disk_read = self.get_top('DiskRead', speeds)
        self.disk_write = self.get_top('DiskWrite', speeds)
        self.interface_read = self.get_top('InterfaceRead', speeds)
        self.interface_write = self.get_top('InterfaceWrite', speeds)

    def get_top(self, keyword, speeds):
        re_list = []
        for speed in speeds:
            if keyword == (speed['name'].split(' ')[1] + speed['name'].split(' ')[2]):
                re = Speed(speed['idc'], speed['name'].split(' ')[0], speed['lastclock'], speed['lastvalue'])
                re_list.append(re)

        re_list.sort(key=lambda k:k.speed, reverse=True)
        return re_list[0:10]


class StaticsView(ListView):
    template_name = 'statics.html'
    queryset = []

    def get_context_data(self, **kwargs):
        context = super(StaticsView, self).get_context_data(**kwargs)

        zabbixs =[]
        for zabbix in settings.ZABBIX_LIST:
            if zabbix['online'] is True:
                zabbixs.append(ZabbixClinet(idc=zabbix['idc'], address=zabbix['address'], username=zabbix['username'], password=zabbix['password']))

        overviews = []
        # speeds = []
        for zabbix in zabbixs:
            instances = zabbix.item_get('Instances', 'State')
            instances_running =[]
            instances_deleted = []
            for instance in instances:
                if instance['lastvalue'] == 'running':
                    instances_running.append(instance)
                elif instance['lastvalue'] == 'deleted':
                    instances_deleted.append(instance)
                else:
                    pass

            overview = OverView(zabbix.idc, len(instances) - len(instances_deleted), len(instances_running))
            overviews.append(overview)

            zabbix.user_logout()

            # speed = zabbix.item_get('Instances', 'Speed')
            # for i in range(len(speed)):
            #     speed[i]['idc'] = zabbix.idc
            #
            # speeds.extend(speed)
        #
        # top = Top(speeds)

        context['overviews'] = overviews
        # context['top'] = top

        return context


def get_vms_data():
    conn = None
    while conn is None:
        try:
            conn = MySQLdb.connect(host='localhost', user=settings.DATA_DB_USER,
                                   passwd=settings.DATA_DB_PASSWD, db='tangjinjie')
        except Exception:
            logging.error("Connect vm_data mysql error, and try again!")
            conn = None

    cursor = conn.cursor()

    yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
    yesterday = yesterday.strftime("%Y-%m-%d")

    sql = '''
    SELECT region, id, ip, system, interface_read, interface_write, disk_read, disk_write FROM vm_data where date="{}"
    '''.format(yesterday)

    cursor.execute(sql)
    vms_info = cursor.fetchall()

    vms = [{'region': vm_info[0], 'id': vm_info[1].strip(), 'ip': vm_info[2], 'system':vm_info[3],
            'interface_read': vm_info[4], 'interface_write': vm_info[5],
            'disk_read': vm_info[6], 'disk_write': vm_info[7]} for vm_info in vms_info]

    return vms


class TopView(ListView):
    template_name = 'top.html'
    queryset = []

    def get_context_data(self, **kwargs):
        context = super(TopView, self).get_context_data(**kwargs)

        vms = get_vms_data()

        top_disk_read = sorted(vms, key=lambda k: k['disk_read'], reverse=True)[:20]
        top_disk_write = sorted(vms, key=lambda k: k['disk_write'], reverse=True)[:20]
        top_interface_read = sorted(vms, key=lambda k: k['interface_read'], reverse=True)[:20]
        top_interface_write = sorted(vms, key=lambda k: k['interface_write'], reverse=True)[:20]

        context['disk_read'] = top_disk_read
        context['disk_write'] = top_disk_write
        context['interface_read'] = top_interface_read
        context['interface_write'] = top_interface_write

        return context
