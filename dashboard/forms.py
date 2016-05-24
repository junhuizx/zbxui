# -*- coding:utf-8 -*-
from django import forms


class UserForm(forms.Form):
    username = forms.CharField(max_length=100,
                               label='Username',
                               required=True,
                               widget=forms.TextInput(attrs={'class' : 'form-control',
                                                             'type': 'text'}))

    name = forms.CharField(max_length=100,
                           label='Name',
                           required=True,
                           widget=forms.TextInput(attrs={'class' : 'form-control',
                                                         'type': 'text'}))

    tele = forms.CharField(max_length=100,
                           label='Tel',
                           required=True,
                           widget=forms.TextInput(attrs={'class' : 'form-control',
                                                         'type': 'text'}))

    email = forms.EmailField(label='Email',
                             widget=forms.EmailInput(attrs={'class' : 'form-control',
                                                            'type': 'text',
                                                            'placeholder':'Email',}))


