from django import template
import datetime

register = template.Library()

@register.filter(name='days_until')
def days_until(date):
    return (date - datetime.date.today()).days


@register.simple_tag(name='is_expired')
def is_expired(date):
    return (date - datetime.date.today()).days < 0


@register.simple_tag(name='expires_today')
def expires_today(date):
    return (date - datetime.date.today()).days == 0

@register.simple_tag(name='expires_in_days')
def expires_in_days(date, days):
    return (date - datetime.date.today()).days <= days
