from typing import Any
import urllib.parse
from django.views.generic import DetailView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.utils.html import format_html
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render

from crispy_forms.helper import FormHelper
from .helpers import  Breadcrumbs, Buttons as Btn

class BreadcrumbsAndButtonsMixin:
    breadcrumbs = Breadcrumbs()
    top_buttons = []
    
    def __init__(self):
        self.breadcrumbs = Breadcrumbs()
        self.top_buttons = []
    
    def set_breadcrumbs(self):
        pass

    def set_top_buttons(self):
        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.set_breadcrumbs()
        self.set_top_buttons()
        context['breadcrumbs'] = self.breadcrumbs
        context['top_buttons'] = self.top_buttons
        return context


class CrispyFormMixin():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-4'


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
        if self.callback is not None:
            self.callback()
        if hasattr(self, 'get_success_message'):
            self.success_message = self.get_success_message()
        messages.success(request, format_html(self.success_message))
        if hasattr(self, 'get_success_url'):
            self.success_url = self.get_success_url()
        return redirect(self.success_url)
    
    
class AuditMixin:
    def __init__(self):
        self.template_name = 'popup.html'
        
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the context
        context = super().get_context_data(**kwargs)

        # Add extra context for the audit popup
        context['popup'] = {
            'title': f"Audit trail for {self.object}",
            'body': self.object.get_mini_audit(),
            'buttons': Btn.HidePopup('Cancel', css_class='secondary', size=None)
        }
        return context
    
class FileViewMixin(DetailView):
    def get(self, request, *args, **kwargs):
        try:
            if not hasattr(self, 'object') or self.object is None:
                self.object = self.get_object()
            if not self.object.file:
                raise Http404("File not found")
            response = FileResponse(self.object.file.open('rb'), content_type='application/octet-stream')
            filename = self.object.file.name.split("/")[-1]
            ascii_filename = filename.encode('ascii', 'ignore').decode()
            encoded_filename = urllib.parse.quote(filename)
        
            response['Content-Disposition'] = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{encoded_filename}'
            return response
        except FileNotFoundError:
            raise Http404("File not found")