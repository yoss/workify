from typing import Any
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages  
from django.utils.html import format_html

from common.helpers import Breadcrumbs, Button
from common.mixins import BreadcrumbsAndButtonsMixin
from django.http import Http404

from .forms import ClientForm
from .models import Client


class ClientList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    permission_required = 'clients.view_client'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.listing_all = self.kwargs.get('all', False)

    def get_breadcrumbs(self):
        return Breadcrumbs.create('Clients', active=True)
    
    def get_top_buttons(self):   
        buttons =  []
        if not self.listing_all:
            buttons.append(Button('Show all', Client.get_list_all_url(), css_class= 'outline-primary', icon=None))
        if self.listing_all:
            buttons.append(Button('Only active', Client.get_list_url(), css_class= 'outline-primary', icon=None))
        if self.request.user.has_perm('clients.add_client'):
            buttons.append(Button('Add client', Client.get_create_url(), css_class= 'success', icon='plus'))
        return buttons
    
    def get_queryset(self):
        if self.listing_all:
            return Client.objects.all()
        return Client.objects.filter(is_active=True)

class ClientDetail(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    permission_required = 'clients.view_client'
    object = Client()

    def get_breadcrumbs(self):
        breadcrumbs = Breadcrumbs.create('Clients', Client.get_list_url())
        badge = 'Archived' if not self.object.is_active else None
        breadcrumbs.add(self.object.name, active=True, badge=badge)
        return breadcrumbs
    
    def get_top_buttons(self):
        return Button('Edit', self.object.get_update_url(), css_class= 'success', icon='edit')

class ClientCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, CreateView):
    model = Client
    template_name = 'form.html'
    form_class = ClientForm
    permission_required = 'clients.add_client'

    def get_breadcrumbs(self):
        breadcrumbs = Breadcrumbs.create('Clients', Client.get_list_url())
        breadcrumbs.add('New client', active=True)
        return breadcrumbs
    
    def get_top_buttons(self):
        return Button('Cancel', Client.get_list_url(), css_class= 'outline-primary', icon=None)
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, format_html("Client {} has been created", form.instance))
        return redirect(Client.get_list_url())
    
class ClientUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, UpdateView):
    model = Client
    template_name = 'form.html'
    form_class = ClientForm
    permission_required = 'clients.change_client'
    object = Client()

    def get_breadcrumbs(self):
        breadcrumbs = Breadcrumbs.create('Clients', Client.get_list_url())
        badge = 'Archived' if not self.object.is_active else None
        breadcrumbs.add(self.object.name, url= self.object.get_absolute_url(), badge=badge)
        breadcrumbs.add('Edit', active=True)
        return breadcrumbs
    
    def get_top_buttons(self):
        buttons = []
        buttons.append(Button('Back', self.object.get_absolute_url(), css_class= 'primary', icon='arrow-left'))
        if self.object.is_active:
            buttons.append(Button('Deactivate', self.object.get_deactivate_url(), css_class='danger', icon='zap-off', type='popup'))
        if not self.object.is_active:
            buttons.append(Button('Activate', self.object.get_activate_url(), css_class='success', icon='zap', type='popup'))
        return buttons
    
    def form_valid(self, form):
        form.save()
        messages.success(self.request, format_html("Client <strong>{}</strong> has been updated", self.object))
        return redirect(self.object.get_absolute_url())

class ClientDeactivate(PermissionRequiredMixin, DetailView):
    model = Client
    permission_required = 'clients.delete_client'
    http_method_names = ['get', 'post']
    object = Client()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        if self.object is None:
            return render(request, 'error_popup.html')
        popup = {}
        popup['title'] = f"Deactivate {self.object}"
        popup['body'] = format_html("<p>Are you sure you want to deactivate <strong>{}</strong>?</p>", self.object)
        popup['buttons'] = [
            Button('Cancel', url=None, css_class='secondary', icon=None, type='popup cancel', size=None),
            Button('Deactivate', self.object.get_deactivate_url(), css_class='danger', type='submit', icon=None,  size=None)
        ]
        return render(request, 'popup.html', {'popup': popup})

    def post(self, request, *args, **kwargs):
        if self.object is None:
            raise Http404
        self.object.deactivate()
        messages.error(request, format_html("Client <strong>{}</strong> has been deactivated", self.object))
        return redirect(Client.get_list_url())
    
    
class ClientActivate(PermissionRequiredMixin, DetailView):
    model = Client
    permission_required = 'clients.delete_client'
    http_method_names = ['get', 'post']
    object = Client()

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        if self.object is None:
            return render(request, 'error_popup.html')
        popup = {}
        popup['title'] = f"Activate {self.object}"
        popup['body'] = format_html("<p>Are you sure you want to activate <strong>{}</strong>?</p>", self.object)
        popup['buttons'] = [
            Button('Cancel', url=None, css_class='secondary', icon=None, type='popup cancel', size=None),
            Button('Activate', self.object.get_activate_url(), css_class='success', type='submit', icon=None,  size=None)
        ]
        return render(request, 'popup.html', {'popup': popup})

    def post(self, request, *args, **kwargs):
        if self.object is None:
            raise Http404
        self.object.activate()
        messages.success(request, format_html("Client <strong>{}</strong> has been activated", self.object))
        return redirect(self.object.get_absolute_url())