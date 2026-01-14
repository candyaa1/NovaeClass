from django import template

register = template.Library()

@register.filter
def grade_color_class(score):
    try:
        score = float(score)
    except (ValueError, TypeError):
        return ''
    
    if score >= 90:
        return 'score-high'
    elif score >= 70:
        return 'score-mid'
    else:
        return 'score-low'
