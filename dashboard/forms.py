# -*- coding:utf-8 -*-
from django import forms


class UserForm(forms.Form):
    username = forms.CharField(max_length=100,
                               label='用户名',
                               required=True,
                               widget=forms.TextInput(attrs={'class' : 'form-control',
                                                             'type': 'text'}))

    name = forms.CharField(max_length=100,
                           label='姓名',
                           required=True,
                           widget=forms.TextInput(attrs={'class' : 'form-control',
                                                         'type': 'text'}))

    tele = forms.CharField(max_length=100,
                           label='电话',
                           required=True,
                           widget=forms.TextInput(attrs={'class' : 'form-control',
                                                         'type': 'text'}))

    email = forms.EmailField(label='Email',
                             required=True,
                             widget=forms.EmailInput(attrs={'class' : 'form-control',
                                                            'type': 'email'}))

    usergroups = forms.MultipleChoiceField(required=True,
                                           choices=((0, '监控管理员'),
                                                    (1, 'Ceph管理员'),
                                                    (2, 'HA管理员'),
                                                    (3, 'MySQL管理员'),
                                                    (4, 'OpenStack管理员'),
                                                    (5, 'RabbitMQ管理员'),
                                                    (6, '经理'),
                                                    (7, '运营维护'),
                                                    (8, '其他')),
                                           widget=forms.SelectMultiple(attrs={'class': 'multi-select',
                                                                              'id':"my_multi_select3",}))

    key = forms.CharField(max_length=100,
                               label='认证码',
                               required=True,
                               widget=forms.TextInput(attrs={'class' : 'form-control',
                                                             'type': 'text'}))



