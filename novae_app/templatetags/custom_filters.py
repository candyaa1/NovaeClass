from django import template

register = template.Library()

@register.filter
def format_timedelta(value):
    """Formats a timedelta into HH:MM:SS"""
    if not value:
        return "00:00:00"
    total_seconds = int(value.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def dict_get(dictionary, key):
    """
    Gets a value from a dictionary safely in templates.
    Usage: {{ my_dict|dict_get:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
