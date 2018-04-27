from django import template

register = template.Library()

@register.filter('username')
def username(user):
    return user._metadata.get('username')
