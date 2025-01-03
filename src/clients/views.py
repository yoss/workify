from typing import Any
from django.db.models.base import Model as Model
from django.db.models import Count, Q
from django.http import FileResponse, Http404
from django.shortcuts import redirect, render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, View
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.contrib import messages  
from django.utils.html import format_html
from dal import autocomplete

from common.helpers import Buttons as Btn
from common.mixins import BreadcrumbsAndButtonsMixin, ObjectToggle, AuditMixin, FileViewMixin
from dicts.models import Currency

from .forms import ClientForm, ContractForm, ContractItemForm, SalesInvoiceForm, SalesInvoiceSettleForm
from .models import Client, Contract, ContractItem, SalesInvoice


class ClientList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, ListView):
    model = Client
    template_name = 'clients/client_list.html'
    context_object_name = 'clients'
    permission_required = 'clients.view_client'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.listing_all = self.kwargs.get('all', False)
    
    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
    
    def set_top_buttons(self):   
        if not self.listing_all:
            self.top_buttons.append(Btn.Link('Show all', Client.get_list_all_url(), css_class='outline-primary', icon='eye'))
        if self.listing_all:
            self.top_buttons.append(Btn.Link('Only active', Client.get_list_url(), css_class='outline-primary', icon='zoeye-off'))
        if self.request.user.has_perm('clients.add_client'):
            self.top_buttons.append(Btn.Link('Add client', Client.get_create_url(), css_class='outline-success', icon='plus'))
    
    def get_queryset(self):
        if self.listing_all:
            return Client.objects.all()
        return Client.objects.filter(is_active=True)

class ClientAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Client.objects.all().filter(is_active=True).order_by('name')  
        if self.q:
            qs = qs.filter(Q(name__icontains=self.q))
        return qs

class ClientDetail(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, DetailView):
    model = Client
    object = Client()
    template_name = 'clients/client_detail.html'
    context_object_name = 'client'
    permission_required = 'clients.view_client'

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.object.get_breadcrumb()) 
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Edit', self.object.get_update_url(), css_class= 'outline-success', icon='edit'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contracts'] = self.object.contract_set.all()
        return context

class ClientCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, CreateView):
    model = Client
    template_name = 'form.html'
    form_class = ClientForm
    permission_required = 'clients.add_client'

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add('New client')
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Cancel', Client.get_list_url(), css_class= 'outline-primary'))
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        messages.success(self.request, format_html("Client {} has been created", form.instance))
        return redirect(Client.get_list_url())
    
class ClientUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, UpdateView):
    model = Client
    template_name = 'form.html'
    form_class = ClientForm
    permission_required = 'clients.change_client'
    object = Client()

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.object.get_breadcrumb())
        self.breadcrumbs.add('Edit')
        # return breadcrumbs
    
    def set_top_buttons(self):
        # buttons = []
        self.top_buttons.append(Btn.Link('Back', self.object.get_absolute_url(), css_class= 'outline-primary', icon='arrow-left'))
        if self.object.is_active:
            self.top_buttons.append(Btn.ShowPopup('Deactivate', self.object.get_deactivate_url(), css_class='outline-danger', icon='zap-off'))
        if not self.object.is_active:
            self.top_buttons.append(Btn.ShowPopup('Activate', self.object.get_activate_url(), css_class='outline-success', icon='zap'))
        # return buttons
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        messages.success(self.request, format_html("Client <strong>{}</strong> has been updated", self.object))
        return redirect(self.object.get_absolute_url())

class ClientDeactivate(ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = Client
        self.permission_required = 'clients.delete_client'
        self.object = Client()

    def get(self, request, *args, **kwargs):
        self.popup_dict = {
            'title': f"Deactivate {self.object}",
            'body': format_html("<p>Are you sure you want to deactivate <strong>{}</strong>?</p>", self.object),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Deactivate', self.object.get_deactivate_url(), css_class='danger', size=None)
            ]
        }
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.callback = self.object.deactivate
        self.success_message = "Client <strong>{}</strong> has been deactivated".format(self.object)
        self.success_url = Client.get_list_url()
        return super().post(request, *args, **kwargs)
        
class ClientActivate(ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = Client
        self.permission_required = 'clients.delete_client'
        self.object = Client()

    def get(self, request, *args, **kwargs):
        self.popup_dict = {
            'title': f"Activate {self.object}",
            'body': format_html("<p>Are you sure you want to activate <strong>{}</strong>?</p>", self.object),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Activate', self.object.get_activate_url(), css_class='success', size=None)
            ]
        }
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.callback = self.object.activate
        self.success_message = "Client <strong>{}</strong> has been activated".format(self.object)
        self.success_url = self.object.get_absolute_url()
        return super().post(request, *args, **kwargs)
    
class ContractList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, ListView):
    model = Contract
    client = Client()
    template_name = 'clients/contract_list.html'
    context_object_name = 'contracts'
    permission_required = 'clients.view_contract'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.client = Client.objects.get(slug=self.kwargs.get('slug'))
        self.listing_all = self.kwargs.get('all', False)

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Contract.get_cls_breadcrumb())
    
    def set_top_buttons(self):   
        if not self.listing_all:
            self.top_buttons.append(Btn.HtmxGet('Show all', self.client.get_contract_list_all_url(), 
                                       target='#contract-table-container', css_class= 'outline-primary', icon='zoom-in'))
        if self.listing_all:
            self.top_buttons.append(Btn.HtmxGet('Only active', self.client.get_contract_list_url(), 
                                       target='#contract-table-container', css_class= 'outline-primary', icon='zoom-out'))
        if self.request.user.has_perm('clients.add_contract'):
            self.top_buttons.append(Btn.Link('Add contract', self.client.get_create_contract_url(), css_class='outline-success', icon='plus'))
    
    def get_queryset(self):
        if self.listing_all:
            return  Contract.objects.filter( client=self.client)
        return Contract.objects.filter(is_active=True, client=self.client)

class ContractCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, CreateView):
    model = Contract
    client = Client()
    template_name = 'form.html'
    form_class = ContractForm
    permission_required = 'clients.add_contract'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.client = Client.objects.get(slug=self.kwargs.get('slug'))

    def get_initial(self):
        return {'client': self.client, 'current_user': self.request.user.employee}

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.client.get_breadcrumb()) 
        self.breadcrumbs.add('New contract')
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Cancel', self.client.get_absolute_url(), css_class='outline-primary'))
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        messages.success(self.request, format_html("Contract {} has been created", form.instance))
        return redirect(self.client.get_absolute_url())

class ContractDetail(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, DetailView):
    model = Contract
    object = Contract()
    template_name = 'clients/contract_detail.html'
    context_object_name = 'contract'
    permission_required = 'clients.view_contract'

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.object.client.get_breadcrumb())
        self.breadcrumbs.add(**self.object.get_breadcrumb())
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.ShowPopup('?', self.object.get_audit_url(), css_class= 'outline-primary', icon=None))
        self.top_buttons.append(Btn.Link('Back', self.object.client.get_absolute_url(), css_class= 'outline-primary', icon='arrow-left'))
        self.top_buttons.append(Btn.Link('Edit', self.object.get_update_url(), css_class= 'outline-success', icon='edit'))

class ContractAudit(AuditMixin, PermissionRequiredMixin, DetailView):
    model = Contract
    permission_required = 'clients.view_contract'
    # pass    

class ContractUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, UpdateView):
    model = Contract
    object = Contract()
    template_name = 'form.html'
    form_class = ContractForm
    client = Client()
    permission_required = 'clients.change_contract'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.client = Client.objects.get(slug=self.kwargs.get('client_slug'))

    def get_initial(self):
        return {'client': self.client, 'current_user': self.request.user.employee}

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.object.client.get_breadcrumb())
        self.breadcrumbs.add(**self.object.get_breadcrumb())
        self.breadcrumbs.add('Edit')
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Back', self.object.get_absolute_url(), css_class='outline-primary', icon='arrow-left'))
        if self.object.is_active:
            self.top_buttons.append(Btn.ShowPopup('Deactivate', self.object.get_deactivate_url(), css_class='outline-danger', icon='zap-off'))
        if not self.object.is_active:
            self.top_buttons.append(Btn.ShowPopup('Activate', self.object.get_activate_url(), css_class='outline-success', icon='zap'))
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        messages.success(self.request, format_html("Contract <strong>{}</strong> has been updated", self.object))
        return redirect(self.object.get_absolute_url())

class ContractDeactivate(ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = Contract
        self.permission_required = 'clients.delete_contract'
        self.object = Contract()

    def get(self, request, *args, **kwargs):
        self.popup_dict = {
            'title': f"Deactivate {self.object}",
            'body': format_html("<p>Are you sure you want to deactivate <strong>{}</strong>?</p>", self.object),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Deactivate', self.object.get_deactivate_url(), css_class='danger', size=None)
            ]
        }
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.callback = self.object.deactivate
        self.success_message = "Contract <strong>{}</strong> has been deactivated".format(self.object)
        self.success_url = self.object.client.get_absolute_url()
        return super().post(request, *args, **kwargs)

class ContractActivate(ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = Contract
        self.permission_required = 'clients.delete_contract'
        self.object = Contract()

    def get(self, request, *args, **kwargs):
        self.popup_dict = {
            'title': f"Activate {self.object}",
            'body': format_html("<p>Are you sure you want to activate <strong>{}</strong>?</p>", self.object),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Activate', self.object.get_activate_url(), css_class='success', size=None)
            ]
        }
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.callback = self.object.activate
        self.success_message = "Contract <strong>{}</strong> has been activated".format(self.object)
        self.success_url = self.object.get_absolute_url()
        return super().post(request, *args, **kwargs)

class ContractItemList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, ListView):
    model = ContractItem
    template_name = 'clients/contract_item_list.html'
    context_object_name = 'contract_items'
    permission_required = 'clients.view_contractitem'
    contract = Contract()

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.contract = Contract.objects.get(slug=self.kwargs.get('slug'))

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**ContractItem.get_cls_breadcrumb())
    
    def set_top_buttons(self):   
        if self.request.user.has_perm('clients.add_contractitem') and self.contract.is_active:
            self.top_buttons.append(Btn.Link('Add contract item', self.contract.get_create_contract_item_url(), css_class= 'outline-success', icon='plus'))
    
    def get_queryset(self):
        return ContractItem.objects.filter( contract=self.contract).annotate(invoice_count=Count('salesinvoice'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        contract_items = context['contract_items']
        for contract_item in contract_items:
            contract_item.buttons = [
                Btn.Link('Edit', contract_item.get_update_url(), css_class='outline-success', icon='edit'),
                Btn.ShowPopup('Delete', contract_item.get_delete_url(), css_class='outline-danger', icon='trash-2')
            ]
        context['contract_items'] = contract_items
        return context

class ContractItemCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, CreateView):
    model = ContractItem
    template_name = 'form.html'
    form_class = ContractItemForm
    contract = Contract()
    permission_required = 'clients.add_contractitem'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.contract = Contract.objects.get(slug=self.kwargs.get('slug'))

    def get_initial(self):
        return {'contract': self.contract, 'current_user': self.request.user.employee, 'currency': Currency.get_default()}

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.contract.client.get_breadcrumb())
        self.breadcrumbs.add(**self.contract.get_breadcrumb())
        self.breadcrumbs.add('New contract item')
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Cancel', self.contract.get_absolute_url(), css_class= 'outline-primary'))
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        messages.success(self.request, format_html("Contract item {} has been created", form.instance))
        return redirect(self.contract.get_absolute_url())

class ContractItemDelete (ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = ContractItem
        self.permission_required = 'clients.delete_contract'
        self.object = ContractItem()

    def get(self, request, *args, **kwargs):
        self.popup_dict = {
            'title': f"Delete {self.object}",
            'body': format_html("<p>Are you sure you want to delete <strong>{}</strong>?</p>", self.object),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Delete', self.object.get_delete_url(), css_class='danger', size=None)
            ]
        }
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.callback = self.object.delete
        self.success_message = "Contract <strong>{}</strong> has been deleted".format(self.object)
        self.success_url = self.object.contract.get_absolute_url()
        return super().post(request, *args, **kwargs)

class ContractItemAudit(AuditMixin, PermissionRequiredMixin, DetailView):
    model = Contract
    permission_required = 'clients.view_contract'

class ContractItemUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, UpdateView):
    model = ContractItem
    template_name = 'form.html'
    form_class = ContractItemForm
    # contract = Contract()
    object = ContractItem()
    permission_required = 'clients.change_contractitem'

    # def setup(self, request, *args, **kwargs):
    #     super().setup(request, *args, **kwargs)
    #     self.contract = Contract.objects.get(slug=self.kwargs.get('slug'))

    def get_initial(self):
        return {'contract': self.object.contract, 'current_user': self.request.user.employee}
    
    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.object.contract.client.get_breadcrumb())
        self.breadcrumbs.add(**self.object.contract.get_breadcrumb())
        self.breadcrumbs.add(**self.object.get_breadcrumb())
        self.breadcrumbs.add('Edit')
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Back', self.object.contract.get_absolute_url(), css_class= 'outline-primary', icon='arrow-left'))
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        messages.success(self.request, format_html("Contract item <strong>{}</strong> has been updated", self.object))
        return redirect(self.object.contract.get_absolute_url())

class SalesInvoiceList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, ListView):
    model = SalesInvoice
    template_name = 'clients/sales_invoice_list.html'
    context_object_name = 'sales_invoices'
    permission_required = 'clients.view_salesinvoice'
    contract = Contract()
    contract_item = ContractItem()

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        if self.kwargs.get('pk'):
            self.contract_item = ContractItem.objects.get(pk=self.kwargs.get('pk'))
            self.contract = self.contract_item.contract
            return
        self.contract_item = None
        self.contract = Contract.objects.get(slug=self.kwargs.get('slug'))

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**SalesInvoice.get_cls_breadcrumb())
        if self.contract_item:
            self.breadcrumbs.add(**self.contract_item.get_breadcrumb())
            return
        self.breadcrumbs.add("All")
    
    def set_top_buttons(self):
        if self.contract_item:
            self.top_buttons.append(Btn.HtmxGet('Back', self.contract.get_contract_invoice_list_url(), 
                                                target='#contract-invoice-table-container', css_class='outline-primary', icon='arrow-left'))
        if self.request.user.has_perm('clients.add_salesinvoice') and self.contract.is_active: 
            self.top_buttons.append(Btn.Link('Add sales invoice', self.contract.get_create_invoice_url(), css_class='outline-success', icon='plus'))
    
    def get_queryset(self):
        if self.contract_item:
            return SalesInvoice.objects.filter(contract_item=self.contract_item)
        return SalesInvoice.objects.filter(contract_item__contract=self.contract)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sales_invoices = context['sales_invoices']
        for sales_invoice in sales_invoices:
            sales_invoice.buttons = []
            if sales_invoice.status != 'Paid':
                sales_invoice.buttons.append(Btn.ShowPopup('Settle', sales_invoice.get_settle_url(), css_class='outline-primary', icon='dollar-sign'))
            sales_invoice.buttons.append(Btn.Link('Edit', sales_invoice.get_update_url(), css_class='outline-success', icon='edit'))
            sales_invoice.buttons.append(Btn.ShowPopup('Delete', sales_invoice.get_delete_url(), css_class='outline-danger', icon='trash-2'))
        context['sales_invoices'] = sales_invoices
        return context
        
class SalesInvoiceCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, CreateView):
    model = SalesInvoice
    template_name = 'form.html'
    form_class = SalesInvoiceForm
    contract = Contract()
    permission_required = 'clients.add_salesinvoice'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.contract = Contract.objects.get(slug=self.kwargs.get('slug'))

    def get_initial(self):
        return {'contract': self.contract, 'current_user': self.request.user.employee, 'currency': Currency.get_default()}

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.contract.client.get_breadcrumb())
        self.breadcrumbs.add(**self.contract.get_breadcrumb())
        self.breadcrumbs.add('New contract invoice')
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Cancel', self.contract.get_absolute_url(), css_class= 'outline-primary'))
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        messages.success(self.request, format_html("Invoice {} has been added", form.instance))
        return redirect(self.contract.get_absolute_url())

class SalesInvoiceUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, UpdateView):
    model = SalesInvoice
    object = SalesInvoice()
    template_name = 'form.html'
    form_class = SalesInvoiceForm
    contract = Contract()
    permission_required = 'clients.change_salesinvoice'

    def get_object(self, queryset=None):
        salesinvoice = super().get_object(queryset)
        self.contract = salesinvoice.contract_item.contract
        return salesinvoice

    def get_initial(self):
        return {'contract': self.contract, 'current_user': self.request.user.employee, }

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Client.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.object.contract_item.contract.client.get_breadcrumb())
        self.breadcrumbs.add(**self.object.contract_item.contract.get_breadcrumb())
        self.breadcrumbs.add(**self.object.get_breadcrumb())
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Back', self.contract.get_absolute_url(), css_class= 'outline-primary', icon='arrow-left'))
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        messages.success(self.request, format_html("Invoice <strong>{}</strong> has been updated", self.object))
        return redirect(self.contract.get_absolute_url())
    
class SalesInvoiceDelete(ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = SalesInvoice
        self.permission_required = 'clients.delete_salesinvoice'
        self.object = SalesInvoice()

    def get(self, request, *args, **kwargs):
        self.popup_dict = {
            'title': f"Delete {self.object}",
            'body': format_html("<p>Are you sure you want to delete <strong>{}</strong>?</p>", self.object),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Delete', self.object.get_delete_url(), css_class='danger', size=None)
            ]
        }
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.callback = self.object.delete
        self.success_message = "Invoice <strong>{}</strong> has been deleted".format(self.object)
        self.success_url = self.object.contract_item.contract.get_absolute_url()
        return super().post(request, *args, **kwargs)

class SalesInvoiceView(PermissionRequiredMixin, FileViewMixin):
    model = SalesInvoice
    permission_required = 'clients.view_salesinvoice'
    
    # def get(self, request, *args, **kwargs):
    #     try:
    #         invoice = self.get_object()
    #         if not invoice.file:
    #             raise Http404("File not found")
    #         response = FileResponse(invoice.file.open('rb'), content_type='application/octet-stream')
    #         response['Content-Disposition'] = f'attachment; filename="{invoice.file.name.split("/")[-1]}"'
    #         return response
    #     except SalesInvoice.DoesNotExist:
    #         raise Http404("Invoice not found")

class SalesInvoiceSettle(PermissionRequiredMixin, UpdateView):
    model = SalesInvoice
    form_class = SalesInvoiceSettleForm
    template_name = 'clients/sales_invoice_list_settle_popup.html'
    permission_required = 'clients.change_salesinvoice'
    object = SalesInvoice()

    def get(self, request, *args, **kwargs):
        super().get(request, *args, **kwargs)
        if self.object is None:
            return render(request, 'error_popup.html', {'error': 'Object not found'})
        buttons = [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.SubmitForm('Settle', css_class='primary', size=None)
            ]
        return render(request, self.template_name, {'form': self.form_class(instance=self.object), 
                                                    'buttons': buttons, 
                                                    'invoice': self.object})
    
    def post(self, request, *args, **kwargs):
        if self.object is None:
            raise Http404
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        messages.success(self.request, format_html("Invoice <strong>{}</strong> has been settled", self.object))
        return redirect(self.object.contract_item.contract.get_absolute_url())
