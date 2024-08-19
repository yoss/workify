from django.http import Http404
from django.shortcuts import redirect, render
from django.views.generic import DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.utils.html import format_html

class Breadcrumbs:
    def __init__(self):
        self.items = []

    def add(self, text, url=None, active=False, badge=None):
        """
        Adds a breadcrumb to the list.

        :param text: The display text for the breadcrumb.
        :param url: The URL the breadcrumb should link to.
        :param active: Whether the breadcrumb is the current/active page.
        :param badge: A badge to display next to the breadcrumb.
        """
        breadcrumb = {
            'text': text,
            'url': url,
            'active': active,
            'badge': badge
        }
        self.items.append(breadcrumb)

    @classmethod
    def create(cls, text, url=None, active=False):
        """
        Creates an instance of Breadcrumbs with the first breadcrumb already added.

        :param text: The display text for the breadcrumb.
        :param url: The URL the breadcrumb should link to.
        :param active: Whether the breadcrumb is the current/active page.
        :param badge: A badge to display next to the breadcrumb.
        """

        breadcrumbs = cls()
        breadcrumbs.add(text, url, active)
        return breadcrumbs
    
    def __iter__(self):
        """
        Allows iteration over breadcrumb items in a template.
        """
        return iter(self.items)
    
class Button():
    def __init__(self, text, url, css_class, type = 'link', icon='link-2', target='_self', size = 'btn-sm'):
        """
        Creates a button object.
        
        :param text: The display text for the button.
        :param url: The URL the button should link to.
        :param css_class: The CSS class to apply to the button. "btn-" class sufix from Bootstrap 5, if "outline-" profix is provided outline class wqill be added to both text buttoin and icon, if standard class will be added (e.g. 'primary), the class will be added to icon button, and outline version will be added to text button.
        :param type: The type of button to create (link or popup). Defaults to 'link'.
        :param icon: The icon to display next to the button text. Defaults to 'link-2'.
        :param target: The target attribute for the button. Defaults to '_self'.
        :param size: The size of the button. Defaults to 'btn-sm'.
        """

        if type not in ['link', 'popup', 'submit', 'popup cancel']:
            raise ValueError("Button type must be 'link', 'popup', 'submit' or 'popup cancel'.")
        
        if target not in ['_self', '_blank']:
            raise ValueError("Button target must be '_self' or '_blank'.")
        
        button_classes = ["primary", "secondary", "success", "danger", "warning", "info", "light", "dark"]
        outline_classes = ["outline-primary", "outline-secondary", "outline-success", "outline-danger", "outline-warning", "outline-info", "outline-light", "outline-dark"]

        if css_class not in button_classes and css_class not in outline_classes:
            raise ValueError("Button class must be a valid Bootstrap 5 button class sufix.")
        if icon:
            self.icon_class = css_class
            if css_class in outline_classes:
                self.text_class = css_class
            if css_class in button_classes:
                self.text_class = f"outline-{css_class}"

        if icon is None:
            self.text_class = css_class

        self.text = text
        self.url = url
        self.type = type
        self.icon = icon
        self.target = target
        self.size = '' if size is None or size == '' else size

class ObjectToggle(PermissionRequiredMixin, DetailView):
    """
    A view that toggles an object's status (e.g. active/inactive) based on a popup confirmation.
    """
    model = None
    object = None
    permission_required = None
    callback = None
    popup_dict = None
    success_message = None
    success_url = None

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        if request.method.lower() == 'get' and self.object is None:
            return render(request, 'error_popup.html', {'error': 'Object not found'})
        if request.method.lower() == 'post' and self.object is None:
            raise Http404
        return super().dispatch(request, *args, **kwargs)   
    
    def get(self, request, *args, **kwargs):
        return render(request, 'popup.html', {'popup': self.popup_dict})
    
    def post(self, request, *args, **kwargs):
        self.callback()
        messages.success(request, format_html(self.success_message))
        return redirect(self.success_url)