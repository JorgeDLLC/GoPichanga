from django import template
register = template.Library()

@register.filter
def index(sequence, i):
    return sequence[i]

@register.filter
def range(n):
    return range(n)
