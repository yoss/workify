from typing import Any
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseBadRequest
from django.views import generic
from django.utils.html import format_html
from django.shortcuts import get_object_or_404, redirect, render
from django.db import models
from django.contrib import messages
from dal import autocomplete

from employees.models import Employee, EmployeeDocument, EmployeeRate
from employees.permissions import employee_detail_permission
from employees.forms import EmployeeCreateForm, EmployeeUpdateForm, EmployeeDocumentForm, EmployeeRateForm
from employees.mixins import EmployeeStatusMixin
from common.mixins import BreadcrumbsAndButtonsMixin, ObjectToggle, FileViewMixin
# from common.helpers import Breadcrumbs, Button
from common.helpers import Buttons as Btn

class EmployeeList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = 'employees.can_view_employee_list'
    model = Employee
    context_object_name = 'employees'

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Employee.get_cls_breadcrumb())
    
    def set_top_buttons(self):   
        listing_all = self.kwargs.get('all', False)
        if not listing_all and self.request.user.has_perm('employees.can_view_archived_employees'):
            self.top_buttons.append(Btn.Link('Show all', Employee.list_all_employees_url(), css_class= 'outline-primary', icon='eye'))
        if listing_all:
            self.top_buttons.append(Btn.Link('Only active', Employee.list_active_employees_url(), css_class= 'outline-primary', icon='eye-off'))
        if self.request.user.has_perm('employees.add_employee'):
            self.top_buttons.append(Btn.Link('Add employee', Employee.get_create_url(), css_class= 'outline-success', icon='plus'))

    def get_queryset(self):
        if self.kwargs.get('all', False) and self.request.user.has_perm('employees.can_view_archived_employees'):
            return self.model.objects.all()
        return self.model.objects.filter(user__is_active=True)

class EmployeeAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Employee.objects.all().filter(user__is_active=True).order_by('user__last_name')
        if self.q:
            qs = qs.filter(models.Q(user__first_name__icontains=self.q) | models.Q(user__last_name__icontains=self.q))
        return qs

class EmployeeDetail(BreadcrumbsAndButtonsMixin, UserPassesTestMixin, generic.DetailView):
    model = Employee
    object = Employee()
    context_object_name = 'employee'
    
    def test_func(self): return employee_detail_permission(self, self.object)

    def set_breadcrumbs(self):
        can_user_access_employee_list = self.request.user.has_perm('employees.can_view_employee_list')
        self.breadcrumbs.add(**Employee.get_cls_breadcrumb(return_url=can_user_access_employee_list))
        self.breadcrumbs.add(**self.object.get_breadcrumb())
    
    def set_top_buttons(self):
        employee = self.object
        if  employee.is_active and self.request.user.has_perm('employees.change_employee'):
            self.top_buttons.append(Btn.Link('Edit', employee.get_update_url(), css_class='outline-success', icon='edit'))
        if employee.is_inactive and self.request.user.has_perm('employees.delete_employee'):
            self.top_buttons.append(Btn.ShowPopup('Activate', employee.get_activate_url(), css_class='outline-success', icon='zap'))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['new_rate_button'] = Btn.Link('Add rate', self.object.get_new_rate_url(), css_class='outline-success', icon='plus')
        rates = context['employee'].employeerate_set.all().order_by('-valid_from')
        for rate in rates:
            rate.buttons = [
                Btn.Link('Edit', rate.get_update_url(), css_class='outline-success', icon='edit'),
                Btn.ShowPopup('Delete', rate.get_delete_url(), css_class='outline-danger', icon='trash-2')
            ]
        context['rates'] = rates

        return context

class EmployeeCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.add_employee'
    form_class = EmployeeCreateForm
    template_name = 'form.html'
    employee = Employee()

    def set_breadcrumbs(self):
        can_user_access_employee_list = self.request.user.has_perm('employees.can_view_employee_list')
        self.breadcrumbs.add(**Employee.get_cls_breadcrumb(return_url=can_user_access_employee_list))
        self.breadcrumbs.add('Add employee')
    
    def set_top_buttons(self):
        if self.request.user.has_perm('employees.can_view_employee_list'):
            self.top_buttons.append(Btn.Link('Back', Employee.list_active_employees_url(), css_class='outline-primary', icon='arrow-left'))

    def get_initial(self):
        user_can_set_user_roles = self.request.user.has_perm('employees.can_set_user_roles')
        return {'user_can_set_user_roles': user_can_set_user_roles}

    def form_valid(self, form):
        self.employee = form.save(self.request.user.employee)
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return format_html("Employee <strong>{}</strong> has been created", self.employee)
    
    def get_success_url(self):
        return self.employee.get_absolute_url()
    
class EmployeeUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin,  EmployeeStatusMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeUpdateForm
    template_name = 'form.html'
    employee = Employee()

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)

    def set_breadcrumbs(self):
        can_user_access_employee_list = self.request.user.has_perm('employees.can_view_employee_list')
        self.breadcrumbs.add(**Employee.get_cls_breadcrumb(return_url=can_user_access_employee_list))
        self.breadcrumbs.add(**self.employee.get_breadcrumb())
        self.breadcrumbs.add('Edit')
    
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Back', self.employee.get_absolute_url(), css_class='outline-primary', icon='arrow-left'))
        if self.employee.is_active and self.request.user.has_perm('employees.delete_employee'):
            self.top_buttons.append(Btn.ShowPopup('Deactivate', self.employee.get_deactivate_url(), css_class='outline-danger', icon='zap-off'))

    def get_initial(self, **kwargs):
        employee_groups = list(self.employee.user.groups.values_list('name', flat=True))
        user_can_set_user_roles = self.request.user.has_perm('employees.can_set_user_roles')
        return {
            'email': self.employee.email, 
            'slug': self.employee.slug, 
            'tax_id': self.employee.tax_id, 
            'employee': self.employee, 
            'groups': employee_groups, 
            'user_can_set_user_roles': user_can_set_user_roles}

    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        return super().form_valid(form)
    
    def get_success_message(self, cleaned_data):
        return format_html("Employee <strong>{}</strong> has been updated", self.employee)

    def get_success_url(self):
        return self.employee.get_absolute_url()

class EmployeeActivate(ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = Employee
        self.permission_required = 'employees.delete_employee'
        self.object = Employee()

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
        # self.callback = self.object.activate
        self.object.activate(current_user=request.user.employee)
        self.success_message = "Employee <strong>{}</strong> has been activated".format(self.object)
        self.success_url = self.object.get_absolute_url()
        return super().post(request, *args, **kwargs)

class EmployeeDeactivate(ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = Employee
        self.permission_required = 'employees.delete_employee'
        self.object = Employee()

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
        # self.callback = self.object.deactivate
        self.object.deactivate(current_user=request.user.employee)

        # self.success_message = "Employee <strong>{}</strong> has been deactivated".format(self.object)
        # self.success_url = Employee.list_active_employees_url()
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        return Employee.list_active_employees_url()
    
    def get_success_message(self):
        return format_html("Employee <strong>{}</strong> has been deactivated", self.object)
    
class EmployeeDocumentList(BreadcrumbsAndButtonsMixin, UserPassesTestMixin, generic.ListView):
    model = Employee
    context_object_name = 'employee'
    template_name = 'employees/employee_document_list.html'
    employee = Employee()

    def test_func(self): return employee_detail_permission(self, self.employee)

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**EmployeeDocument.get_cls_breadcrumb())

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Add document', self.employee.get_new_document_url(), css_class='outline-success', icon='plus'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_can_change_employee'] = self.request.user.has_perm('employees.change_employee')
        documents = self.employee.employeedocument_set.all().order_by('sign_date')
        for document in documents:
            document.buttons = [
                # Btn.Link('Open', document.get_absolute_url(), css_class='outline-primary', icon='external-link', target='_blank'),
                Btn.Link('Edit', document.get_update_url(), css_class='outline-success', icon='edit'),
                Btn.ShowPopup('Delete', document.get_delete_url(), css_class='outline-danger', icon='trash-2')
            ]
        context['documents'] = documents
        return context
    
class EmployeeDocumentDetail(UserPassesTestMixin, FileViewMixin):
    model = EmployeeDocument

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        self.object = get_object_or_404(EmployeeDocument, pk=kwargs['pk'])
        return super().setup(request, *args, **kwargs)

    def test_func(self): 
        if not employee_detail_permission(self, self.employee):
            return False
        if self.object.employee != self.request.user.employee:
            return False
        return True

class EmployeeDocumentCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeDocumentForm
    template_name = 'form.html'
    employee = Employee()
    document_name = None

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)
    
    def set_breadcrumbs(self):
        can_user_access_employee_list = self.request.user.has_perm('employees.can_view_employee_list')
        self.breadcrumbs.add(**Employee.get_cls_breadcrumb(return_url=can_user_access_employee_list))
        self.breadcrumbs.add(**self.employee.get_breadcrumb())
        self.breadcrumbs.add('Add document')

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Back', self.employee.get_absolute_url(), css_class='outline-primary', icon='arrow-left'))
    
    def get_initial(self, **kwargs):
        return { 'employee': self.employee}
    
    def form_valid(self, form):
        form.save(current_user=self.request.user.employee)
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Document <strong>{}</strong> has been added to {}", cleaned_data['name'], self.employee)
    
class EmployeeDocumentUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeDocumentForm
    template_name = 'form.html'
    employee = Employee()
    document = EmployeeDocument()

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        self.document = get_object_or_404(EmployeeDocument, pk=kwargs['pk'])
        return super().setup(request, *args, **kwargs)
    
    def set_breadcrumbs(self):
        can_user_access_employee_list = self.request.user.has_perm('employees.can_view_employee_list')
        self.breadcrumbs.add(**Employee.get_cls_breadcrumb(return_url=can_user_access_employee_list))
        self.breadcrumbs.add(**self.employee.get_breadcrumb())
        self.breadcrumbs.add(**self.document.get_breadcrumb())
        self.breadcrumbs.add('Edit')

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Back', self.employee.get_absolute_url(), css_class='outline-primary', icon='arrow-left'))
        self.top_buttons.append(Btn.ShowPopup('Delete', self.document.get_delete_url(), css_class='outline-danger', icon='trash-2'))
            # Button('Delete', self.document.get_delete_url(), css_class='danger', icon='trash-2', type='popup')
            # ]

    def get_initial(self, **kwargs):
        return { 'employee': self.document.employee}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.document  
        return kwargs

    def form_valid(self, form):
        self.document = form.save(current_user=self.request.user.employee)
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Document <strong>{}</strong> has been updated", self.document.name)
    
    def get(self, request, *args, **kwargs):
        if self.document.employee.slug != kwargs.pop('slug', None):
            raise HttpResponseBadRequest('Document does not belong to employee')
        return super().get(request, *args, **kwargs)
 
class EmployeeDocumentDelete(ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = EmployeeDocument
        self.permission_required = 'employees.change_employee'
        self.object = EmployeeDocument()

    def get(self, request, *args, **kwargs):
        self.popup_dict = {
            'title': f"Delete {self.object}",
            'body': format_html("<p>Are you sure you want to delete <strong>{}</strong>?</p>", self.object),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Delete', self.object.get_delete_url(), css_class='danger',size=None)
            ]
        }
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.callback = self.object.delete
        self.success_message = "Document <strong>{}</strong> has been deleted".format(self.object)
        self.success_url = self.object.employee.get_absolute_url()
        return super().post(request, *args, **kwargs)
   
class EmployeeRateList(BreadcrumbsAndButtonsMixin, UserPassesTestMixin, generic.ListView):
    model = Employee
    context_object_name = 'employee'
    template_name = 'employees/employee_rate_list.html'
    employee = Employee()

    def test_func(self): return employee_detail_permission(self, self.employee)

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**EmployeeRate.get_cls_breadcrumb())

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Add rate', self.employee.get_new_rate_url(), css_class='outline-success', icon='plus'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # context['user_can_change_employee'] = self.request.user.has_perm('employees.change_employee')
        rates = self.employee.employeerate_set.all().order_by('-valid_from')

        # documents = self.employee.employeedocument_set.all().order_by('sign_date')
        for rate in rates:
            rate.buttons = [
                Btn.Link('Edit', rate.get_update_url(), css_class='outline-success', icon='edit'),
                Btn.ShowPopup('Delete', rate.get_delete_url(), css_class='outline-danger', icon='trash-2')
            ]
        context['rates'] = rates
        return context

class EmployeeRateCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeRateForm
    template_name = 'form.html'
    employee = Employee()
    rate = None

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)
    
    def set_breadcrumbs(self):
        can_user_access_employee_list = self.request.user.has_perm('employees.can_view_employee_list')
        self.breadcrumbs.add(**Employee.get_cls_breadcrumb(return_url=can_user_access_employee_list))
        self.breadcrumbs.add(**self.employee.get_breadcrumb())
        self.breadcrumbs.add('Add rate')

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Back', self.employee.get_absolute_url(), css_class='outline-primary', icon='arrow-left'))
    
    def get_initial(self, **kwargs):
        return { 'employee': self.employee}

    def form_valid(self, form):
        self.rate = form.save(current_user=self.request.user.employee)
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Rate <strong>{}</strong> has been added to {}", self.rate, self.employee)
    
class EmployeeRateUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeRateForm
    template_name = 'form.html'
    employee = Employee()
    rate = EmployeeRate()

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        self.rate = get_object_or_404(EmployeeRate, pk=kwargs['pk'])
        return super().setup(request, *args, **kwargs)
    
    def set_breadcrumbs(self):
        can_user_access_employee_list = self.request.user.has_perm('employees.can_view_employee_list')
        self.breadcrumbs.add(**Employee.get_cls_breadcrumb(return_url=can_user_access_employee_list))
        self.breadcrumbs.add(**self.employee.get_breadcrumb())
        self.breadcrumbs.add(**self.rate.get_breadcrumb())
        self.breadcrumbs.add('Edit')

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Back', self.employee.get_absolute_url(), css_class='outline-primary', icon='arrow-left'))
        self.top_buttons.append(Btn.ShowPopup('Delete', self.rate.get_delete_url(), css_class='outline-danger', icon='trash-2'))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.rate  
        return kwargs
    
    def form_valid(self, form):
        self.rate = form.save(current_user=self.request.user.employee)
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Rate <strong>{}</strong> has been updated", self.rate)
    
    def get(self, request, *args, **kwargs):
        if self.rate.employee.slug != kwargs.pop('slug', None):
            raise HttpResponseBadRequest('Document does not belong to employee')
        return super().get(request, *args, **kwargs)
    
# ObjectToggle is overkill for this use case TODO - refactor
class EmployeeRateDelete(ObjectToggle):
    def __init__(self, *args, **kwargs):
        self.model = EmployeeRate
        self.permission_required = 'employees.change_employee'
        self.object = EmployeeRate()

    def get(self, request, *args, **kwargs):
        self.popup_dict = {
            'title': f"Delete {self.object}",
            'body': format_html("<p>Are you sure you want to delete <strong>{}</strong>?</p>", self.object),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Delete', self.object.get_delete_url(), css_class='danger',  size=None)
            ]
        }
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.callback = self.object.delete
        self.success_message = "Rate <strong>{}</strong> has been deleted".format(self.object)
        self.success_url = self.object.employee.get_absolute_url()
        return super().post(request, *args, **kwargs)
    