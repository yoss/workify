from typing import Any
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseBadRequest
from django.views import generic
from django.utils.html import format_html
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from employees.models import Employee, EmployeeDocument, EmployeeRate
from employees.permissions import employee_detail_permission
from employees.forms import EmployeeCreateForm, EmployeeUpdateForm, EmployeeDocumentForm, EmployeeRateForm
from employees.mixins import EmployeeStatusMixin
from common.mixins import BreadcrumbsAndButtonsMixin
from common.helpers import Breadcrumbs, Button

class EmployeeList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = 'employees.can_view_employee_list'
    model = Employee
    context_object_name = 'employees'

    def get_breadcrumbs(self):
        return Breadcrumbs.create('Employees', active=True)
    
    def get_top_buttons(self):   
        buttons =  []
        listing_all = self.kwargs.get('all', False)
        if not listing_all and self.request.user.has_perm('employees.can_view_archived_employees'):
            buttons.append(Button('Show all', Employee.list_all_employees_url(), css_class= 'outline-primary', icon=None))
        if listing_all:
            buttons.append(Button('Only active', Employee.list_active_employees_url(), css_class= 'outline-primary', icon=None))
        if self.request.user.has_perm('employees.add_employee'):
            buttons.append(Button('Add employee', Employee.get_create_url(), css_class= 'success', icon='plus'))
        return buttons

    def get_queryset(self):
        if self.kwargs.get('all', False) and self.request.user.has_perm('employees.can_view_archived_employees'):
            return self.model.objects.all()
        return self.model.objects.filter(user__is_active=True)

class EmployeeDetail(BreadcrumbsAndButtonsMixin, UserPassesTestMixin, generic.DetailView):
    model = Employee
    context_object_name = 'employee'

    def test_func(self): return employee_detail_permission(self)

    def get_breadcrumbs(self):
        url = Employee.list_active_employees_url() if self.request.user.has_perm('employees.can_view_employee_list') else None
        breadcrumbs = Breadcrumbs.create('Employees', url=url)

        badge = 'Archived' if self.object.is_inactive else None
        breadcrumbs.add(self.object, url=None, active=True, badge=badge)

        return breadcrumbs
    
    def get_top_buttons(self):
        buttons = []
        employee = self.object
        if  employee.is_active and self.request.user.has_perm('employees.change_employee'):
            buttons.append(Button('Edit', employee.get_update_url(), css_class='success', icon='edit'))
        if employee.is_inactive and self.request.user.has_perm('employees.delete_employee'):
            buttons.append(Button('Activate', employee.get_activate_url(), css_class='success', icon='zap', type='popup'))
        return buttons
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_can_change_employee'] = self.request.user.has_perm('employees.change_employee')
        context['new_document_button'] = Button('Add document', self.object.get_new_document_url(), css_class='success', icon='plus')
        documents = context['employee'].employeedocument_set.all().order_by('sign_date')
        # empl = Employee()
        # empl.rate_set.all()
        for document in documents:
            document.buttons = [
                Button('Open', document.document_file.url, css_class='primary', icon='external-link', target='_blank'),
                Button('Edit', document.get_update_url(), css_class='success', icon='edit'),
                Button('Delete', document.get_delete_url(), css_class='danger', icon='trash-2', type='popup')
            ]
        context['documents'] = documents
        context['new_rate_button'] = Button('Add rate', self.object.get_new_rate_url(), css_class='success', icon='plus')
        rates = context['employee'].employeerate_set.all().order_by('-valid_from')
        for rate in rates:
            rate.buttons = [
                Button('Edit', rate.get_update_url(), css_class='success', icon='edit'),
                Button('Delete', rate.get_delete_url(), css_class='danger', icon='trash-2', type='popup')
            ]
        context['rates'] = rates

        return context

class EmployeeCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.add_employee'
    form_class = EmployeeCreateForm
    template_name = 'employees/employee_create_form.html'

    def get_breadcrumbs(self):
        url = Employee.list_active_employees_url()  if self.request.user.has_perm('employees.can_view_employee_list') else None
        breadcrumbs = Breadcrumbs.create('Employees', url=url)
        breadcrumbs.add('Add employee', url=None, active=True)
        return breadcrumbs
    
    def get_top_buttons(self):
        if self.request.user.has_perm('employees.can_view_employee_list'):
            return [Button('Back', Employee.list_active_employees_url()  , css_class='primary', icon='arrow-left')]
        return []

    def get_initial(self):
        user_can_set_user_roles = self.request.user.has_perm('employees.can_set_user_roles')
        return {'user_can_set_user_roles': user_can_set_user_roles}

    def form_valid(self, form):
        cd = form.cleaned_data
        self.employee = Employee.create_employee(cd['first_name'], cd['last_name'], cd['email'], None, cd['tax_id'])
        return super().form_valid(form)   
    
    def get_success_message(self, cleaned_data):
        return format_html("Employee <strong>{}</strong> has been created", self.employee)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
class EmployeeUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin,  EmployeeStatusMixin,SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeUpdateForm
    template_name = 'employees/employee_update_form.html'
    employee = Employee()

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)

    def get_breadcrumbs(self):
        url = Employee.list_active_employees_url() if self.request.user.has_perm('employees.can_view_employee_list') else None
        breadcrumbs = Breadcrumbs.create('Employees', url=url)
        
        badge = 'Archived' if self.employee.is_inactive else None
        breadcrumbs.add(self.employee, url=self.employee.get_absolute_url(), active=False, badge=badge)
        breadcrumbs.add('Edit', url=None, active=True)
        return breadcrumbs
    
    def get_top_buttons(self):
        buttons =[]
        buttons.append(Button('Back', self.employee.get_absolute_url(), css_class='primary', icon='arrow-left'))
        if self.employee.is_active and self.request.user.has_perm('employees.delete_employee'):
            buttons.append(Button('Deactivate', self.employee.get_deactivate_url(), css_class='danger', icon='zap-off', type='popup'))
        return buttons

    def form_valid(self, form):
        cd = form.cleaned_data
        if not self.request.user.has_perm('employees.can_set_user_roles'):
            cd.pop('groups')
        self.employee.update(email = cd['email'], tax_id=cd['tax_id'], slug = cd['slug'], groups = cd.get('groups'))
        return super().form_valid(form)
    
    def get_initial(self, **kwargs):
        employee_groups = list(self.employee.user.groups.values_list('name', flat=True))
        user_can_set_user_roles = self.request.user.has_perm('employees.can_set_user_roles')
        return {'email': self.employee.email, 'slug': self.employee.slug, 'tax_id': self.employee.tax_id, 'employee': self.employee, 'groups': employee_groups, 'user_can_set_user_roles': user_can_set_user_roles}
    
    def get_success_message(self, cleaned_data):
        return format_html("Employee <strong>{}</strong> has been updated", self.employee)

    def get_success_url(self):
        return self.employee.get_absolute_url()

class EmployeeToogle(PermissionRequiredMixin, generic.View):
    permission_required = 'employees.delete_employee'
    http_method_names = ['post', 'get']

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)

    def http_method_not_allowed(self, request, *args, **kwargs):
        return redirect(self.employee.get_absolute_url())

class EmployeeDeactivate(EmployeeToogle):
    def get(self, request, *args, **kwargs):
        return render(request, 'employees/employee_deactivate_popup.html', {'employee': self.employee})

    def post(self, request, *args, **kwargs):
        self.employee.deactivate()
        messages.error(request, format_html("Employee <strong>{}</strong> has been deactivated", self.employee))
        return redirect(Employee.list_active_employees_url())
        
class EmployeeActivate(EmployeeToogle):
    def get(self, request, *args, **kwargs):
        return render(request, 'employees/employee_activate_popup.html', {'employee': self.employee})

    def post(self, request, *args, **kwargs):
        self.employee.activate()
        messages.success(request, format_html("Employee <strong>{}</strong> has been activated", self.employee))
        return redirect(self.employee.get_absolute_url())
    
class EmployeeDocumentCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeDocumentForm
    template_name = 'employees/employee_document_form.html'
    employee = Employee()
    document_name = None

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)
    
    def get_breadcrumbs(self):
        employees_url = Employee.list_active_employees_url() if self.request.user.has_perm('employees.can_view_employee_list') else None
        breadcrumbs = Breadcrumbs.create('Employees', url=employees_url)

        badge = 'Archived' if self.employee.is_inactive else None
        breadcrumbs.add(self.employee, url=self.employee.get_absolute_url(), active=False, badge=badge)
        breadcrumbs.add('Add document', url=None, active=True)
        return breadcrumbs

    def get_top_buttons(self):
        return [Button('Back', self.employee.get_absolute_url(), css_class='primary', icon='arrow-left')]
    
    def get_initial(self, **kwargs):
        return { 'employee': self.employee}

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Document <strong>{}</strong> has been added to {}", cleaned_data['name'], self.employee)
    
class EmployeeDocumentDelete(PermissionRequiredMixin, generic.View):
    permission_required = 'employees.change_employee'
    http_method_names = ['post', 'get']

    def setup(self, request, *args, **kwargs):
        self.document = get_object_or_404(EmployeeDocument, pk=kwargs['pk'])
        return super().setup(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        if self.document.employee.slug != kwargs.pop('slug', None):
            return render(request, 'error_popup.html', {'error': 'Document does not belong to employee'})
        return render(request, 'employees/employee_document_delete_popup.html', {'document': self.document})

    def post(self, request, *args, **kwargs):
        if self.document.employee.slug != kwargs.pop('slug', None):
            messages.error(request, 'Document does not belong to employee')
            return redirect(self.document.employee.get_absolute_url())

        self.document.delete()
        messages.success(request, 'Document deleted')
        return redirect(self.document.employee.get_absolute_url())
    
class EmployeeDocumentUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeDocumentForm
    template_name = 'employees/employee_document_form.html'
    employee = Employee()
    document = EmployeeDocument()

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        self.document = get_object_or_404(EmployeeDocument, pk=kwargs['pk'])
        return super().setup(request, *args, **kwargs)
    
    def get_breadcrumbs(self):
        employees_url = Employee.list_active_employees_url() if self.request.user.has_perm('employees.can_view_employee_list') else None
        breadcrumbs = Breadcrumbs.create('Employees', url=employees_url)

        badge = 'Archived' if self.employee.is_inactive else None
        breadcrumbs.add(self.employee, url=self.employee.get_absolute_url(), active=False, badge=badge)
        breadcrumbs.add(self.document.name, url=None, active=False)
        breadcrumbs.add('Edit', url=None, active=True)

        return breadcrumbs

    def get_top_buttons(self):
        return [
            Button('Back', self.employee.get_absolute_url(), css_class='primary', icon='arrow-left'),
            Button('Delete', self.document.get_delete_url(), css_class='danger', icon='trash-2', type='popup')
            ]

    def get_initial(self, **kwargs):
        return { 'employee': self.document.employee}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.document  
        return kwargs
    

    def form_valid(self, form):
        self.document = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Document <strong>{}</strong> has been updated", self.document.name)
    
    def get(self, request, *args, **kwargs):
        if self.document.employee.slug != kwargs.pop('slug', None):
            raise HttpResponseBadRequest('Document does not belong to employee')
        return super().get(request, *args, **kwargs)
    
class EmployeeRateCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeRateForm
    template_name = 'employees/employee_rate_form.html'
    employee = Employee()
    rate = None

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)
    
    def get_breadcrumbs(self):
        employees_url = Employee.list_active_employees_url() if self.request.user.has_perm('employees.can_view_employee_list') else None
        breadcrumbs = Breadcrumbs.create('Employees', url=employees_url)

        badge = 'Archived' if self.employee.is_inactive else None
        breadcrumbs.add(self.employee, url=self.employee.get_absolute_url(), active=False, badge=badge)
        breadcrumbs.add('Add rate', url=None, active=True)

        return breadcrumbs

    def get_top_buttons(self):
        return [Button('Back', self.employee.get_absolute_url(), css_class='primary', icon='arrow-left')]
    
    def get_initial(self, **kwargs):
        return { 'employee': self.employee}

    def form_valid(self, form):
        self.rate = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Rate <strong>{}</strong> has been added to {}", self.rate, self.employee)
    
class EmployeeRateUpdate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeRateForm
    template_name = 'employees/employee_document_form.html'
    employee = Employee()
    rate = EmployeeRate()

    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        self.rate = get_object_or_404(EmployeeRate, pk=kwargs['pk'])
        return super().setup(request, *args, **kwargs)
    
    def get_breadcrumbs(self):
        employees_url = Employee.list_active_employees_url() if self.request.user.has_perm('employees.can_view_employee_list') else None
        breadcrumbs = Breadcrumbs.create('Employees', url=employees_url)

        badge = 'Archived' if self.employee.is_inactive else None
        breadcrumbs.add(self.employee, url=self.employee.get_absolute_url(), active=False, badge=badge)
        breadcrumbs.add(self.rate, url=None, active=False)
        breadcrumbs.add('Edit', url=None, active=True)

        return breadcrumbs

    def get_top_buttons(self):
        return [
            Button('Back', self.employee.get_absolute_url(), css_class='primary', icon='arrow-left'),
            Button('Delete', self.rate.get_delete_url(), css_class='danger', icon='trash-2', type='popup')
            ]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.rate  
        return kwargs
    
    def form_valid(self, form):
        self.rate = form.save()
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Rate <strong>{}</strong> has been updated", self.rate)
    
    def get(self, request, *args, **kwargs):
        if self.rate.employee.slug != kwargs.pop('slug', None):
            raise HttpResponseBadRequest('Document does not belong to employee')
        return super().get(request, *args, **kwargs)

class EmployeeRateDelete(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    http_method_names = ['post', 'get']

    def setup(self, request, *args, **kwargs):
        self.rate = get_object_or_404(EmployeeRate, pk=kwargs['pk'])
        return super().setup(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        if self.rate.employee.slug != kwargs.pop('slug', None):
            return render(request, 'error_popup.html', {'error': 'Document does not belong to employee'})
        return render(request, 'employees/employee_rate_delete_popup.html', {'rate': self.rate})

    def post(self, request, *args, **kwargs):
        if self.rate.employee.slug != kwargs.pop('slug', None):
            messages.error(request, 'Rate does not belong to employee')
            return redirect(self.rate.employee.get_absolute_url())

        self.rate.delete()
        messages.success(request, 'Rate deleted')
        return redirect(self.rate.employee.get_absolute_url())