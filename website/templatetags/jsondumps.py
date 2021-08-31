from django import template
import json
from django.core import serializers

register = template.Library()

@register.filter(name='json')
def json_dumps(data):
    is_list: bool = isinstance(data, list)
    json_string: str = serializers.serialize("json", data if is_list else [data])
    data = json.loads(json_string)

    for d in data:
        del d['pk']
        del d['model']

    data = [d['fields'] for d in data]

    json_string = json.dumps(data if is_list else data[0])
    return json_string
