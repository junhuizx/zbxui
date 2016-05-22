# coding:utf-8

import json
from django import template
import datetime

register = template.Library()


@register.filter
def issue_age(lastchange):
    age = datetime.datetime.now() - lastchange
    age = age - datetime.timedelta(microseconds=age.microseconds)
    return age

# 0 - (default) not classified;
# 1 - information;
# 2 - warning;
# 3 - average;
# 4 - high;
# 5 - disaster.

@register.filter
def issue_color(priority):
    color = '#F0F8FF'
    if priority == '0':
        color = '#A9A9A9'
    elif priority == '1':
        color = '#6495ED'
    elif priority == '2':
        color = '#FFD700'
    elif priority == '3':
        color = '#FFA500'
    elif priority == '4':
        color = '#FF4500'
    elif priority == '5':
        color = '#FF0000'
    else:
        pass
    return color

@register.filter
def issue_priority(priority):
    if priority == '0':
        priority = 'not classified'
    elif priority == '1':
        priority = 'information'
    elif priority == '2':
        priority = 'warning'
    elif priority == '3':
        priority = 'average'
    elif priority == '4':
        priority = 'high'
    elif priority == '5':
        priority = 'disaster'
    else:
        pass
    return priority