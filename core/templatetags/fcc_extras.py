from django import template
from django.template.defaulttags import register

register = template.Library()

@register.filter
def get_item(dictionary, key):
    try:
        if dictionary.get(key):
            return dictionary.get(key)
        elif dictionary.get(str(key)):
            return dictionary.get(str(key))
        else:
            return ""
    except:
        return ""
