from django import template
from django import template
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

register = template.Library()

@register.inclusion_tag('templatetags/show_avatar.html')
def show_avatar(employee):
    return({'employee': employee})

@register.inclusion_tag('templatetags/popup_button.html')
def popup_button(url, css_class, text, icon = None):
    if ":" in url:
        url = reverse_lazy(url)
    return({'url': url, 'css_class': css_class, 'text': text, 'icon': icon})

@register.inclusion_tag('templatetags/link_button.html')
def link_button(url, css_class, text, icon = None, target = "_self"):
    if ":" in url:
        url = reverse_lazy(url)
    return({'url': url, 'css_class': css_class, 'text': text, 'icon': icon, 'target': target})

@register.simple_tag
def get_breadcrumbs(breadcrumbs):
    li = []
    for breadcrumb in breadcrumbs:
        active = "active" if breadcrumb['active'] else ""
        badge = f"<span class='badge bg-secondary'>{breadcrumb['badge']}</span>" if breadcrumb['badge'] else ""
        inner = f"<a href='{breadcrumb['url']}'>{breadcrumb['text']}</a> {badge}" if breadcrumb['url'] else f"{breadcrumb['text']} {badge}"
        li.append (f"<li class='breadcrumb-item {active}'>{inner}</li>")
    return mark_safe(("\n").join(li))
