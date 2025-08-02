from django import template

register = template.Library()

@register.filter
def percentage(value, max_value):
    """Calculate percentage of value relative to max_value"""
    try:
        if value is None or max_value is None:
            return 0
        return round((float(value) / float(max_value)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Multiply the value by the argument"""
    try:
        if value is None or arg is None:
            return 0
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None
