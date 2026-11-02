from django import template

register = template.Library()


@register.filter
def dictget(mapping, key):
    try:
        return mapping.get(key)
    except AttributeError:
        return None
