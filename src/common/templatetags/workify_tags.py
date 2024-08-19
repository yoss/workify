from collections.abc import Iterable
from django import template
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

register = template.Library()

@register.inclusion_tag('templatetags/render_avatar.html')
def render_avatar(employee):
    return({'employee': employee})

@register.inclusion_tag('templatetags/render_logo.html')
def render_logo(client):
    return({'client': client})

@register.simple_tag
def render_breadcrumbs(breadcrumbs):
    li = []
    for breadcrumb in breadcrumbs:
        active = "active" if breadcrumb['active'] else ""
        badge = f"<span class='badge bg-secondary'>{breadcrumb['badge']}</span>" if breadcrumb['badge'] else ""
        inner = f"<a href='{breadcrumb['url']}'>{breadcrumb['text']}</a> {badge}" if breadcrumb['url'] else f"{breadcrumb['text']} {badge}"
        li.append (f"<li class='breadcrumb-item {active}'>{inner}</li>")
    return mark_safe(("\n").join(li))

@register.inclusion_tag('templatetags/render_button.html')
def render_button(button):
    if isinstance(button, Iterable) and not isinstance(button, str):
        return {'buttons': button}
    else:
        return {'buttons': [button]}
    
@register.simple_tag(takes_context=True)
def render_sidebar_link(context, title, permission, link, icon = 'arrow-right-circle'):
    request = context['request']
    if not request.user.has_perm(permission):
        return ""
    url = reverse_lazy(link)
    active = 'active' if request.resolver_match.app_name == link.split(":")[0] else ''
    return mark_safe(f"<li class='nav-item'><a class='nav-link {active}' aria-current='page' href='{url}'><span data-feather='{icon}'></span>{title}</a></li>")