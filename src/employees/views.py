from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseBadRequest
from django.views import generic
from django.utils.html import format_html
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages

from employees.models import Employee, EmployeeDocument
from employees.permissions import employee_detail_permission
from employees.forms import EmployeeCreateForm, EmployeeUpdateForm, EmployeeDocumentForm
from employees.mixins import EmployeeStatusMixin
from common.mixins import BreadcrumbsAndButtonsMixin

class EmployeeList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = 'employees.can_view_employee_list'
    model = Employee
    context_object_name = 'employees'

    def get_breadcrumbs(self):
        return [{'text': 'Employees', 'badge': None, 'url': None, 'active': True}]
    
    def get_top_buttons(self):   
        buttons =  []
        listing_all = self.kwargs.get('all', False)
        if not listing_all and self.request.user.has_perm('employees.can_view_archived_employees'):
            buttons.append ({'type': 'link', 'url': Employee.list_all_employees_url(), 'css_class': 'outline-primary', 'text': 'Show all'})
        if listing_all:
            buttons.append ({'type': 'link', 'url': Employee.list_active_employees_url(), 'css_class': 'outline-primary', 'text': 'Only active'})   
        if self.request.user.has_perm('employees.add_employee'):
            buttons.append ({'type': 'link', 'url': Employee.get_create_url(), 'css_class': 'success', 'text': 'Add employee', 'icon': 'plus'})
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
        badge = 'Archived' if self.object.is_inactive else None

        return [{'text': 'Employees', 'badge': None, 'url': url, 'active': False},
                {'text': self.object, 'badge': badge, 'url': None, 'active': True}]
    
    def get_top_buttons(self):
        buttons = []
        employee = self.object
        if  employee.is_active and self.request.user.has_perm('employees.change_employee'):
            buttons.append({'type': 'link', 'url': employee.get_update_url(), 'css_class': 'success', 'text': 'Edit', 'icon': 'edit'})
        if employee.is_inactive and self.request.user.has_perm('employees.delete_employee'):
            buttons.append({'type': 'popup', 'url': employee.get_activate_url(), 'css_class': 'success', 'text': 'Activate', 'icon': 'zap'})
        return buttons

class EmployeeCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.add_employee'
    form_class = EmployeeCreateForm
    template_name = 'employees/employee_create_form.html'

    def get_breadcrumbs(self):
        url = Employee.list_active_employees_url()  if self.request.user.has_perm('employees.can_view_employee_list') else None
        return [
            {'text': 'Employees', 'badge': None, 'url': url, 'active': False},
            {'text': 'Add employee', 'badge': None, 'url': None, 'active': True}
        ]
    
    def get_top_buttons(self):
        if self.request.user.has_perm('employees.can_view_employee_list'):
            url = Employee.list_active_employees_url()  
            return [{'type': 'link', 'url': url, 'css_class': 'primary', 'text': 'Back', 'icon': 'arrow-left'}]
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
        employees_url = Employee.list_active_employees_url() if self.request.user.has_perm('employees.can_view_employee_list') else None
        badge = 'Archived' if self.employee.is_inactive else None
        employee_url = self.employee.get_absolute_url()

        return [
            {'text': 'Employees', 'badge': None, 'url': employees_url, 'active': False},
            {'text': self.employee, 'badge': badge, 'url': employee_url, 'active': False},
            {'text': 'Edit', 'badge': None, 'url': None, 'active': True}
        ]
    def get_top_buttons(self):
        buttons =[]
        buttons.append({'type': 'link', 'url': self.employee.get_absolute_url(), 'css_class': 'primary', 'text': 'Back', 'icon': 'arrow-left'})
        if self.employee.is_active and self.request.user.has_perm('employees.delete_employee'):
            buttons.append({'type': 'popup', 'url': self.employee.get_deactivate_url(), 'css_class': 'danger', 'text': 'Deactivate', 'icon': 'zap-off'})
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
        badge = 'Archived' if self.employee.is_inactive else None
        employee_url = self.employee.get_absolute_url()

        return [{'text': 'Employees', 'badge': None, 'url': employees_url, 'active': False},
                {'text': self.employee, 'badge': badge, 'url': employee_url, 'active': False},
                {'text': 'Add document', 'badge': None, 'url': None, 'active': True}
        ]

    def get_top_buttons(self):
        return [{'type': 'link', 'url': self.employee.get_absolute_url(), 'css_class': 'primary', 'text': 'Back', 'icon': 'arrow-left'}]
    
    def get_initial(self, **kwargs):
        return { 'employee': self.employee}

    def form_valid(self, form):
        cd = form.cleaned_data
        self.document_name = cd['name']
        self.employee.add_document(cd['name'], cd['sign_date'], cd['document_file'], cd['document_type'], cd['reference_document'])
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Document <strong>{}</strong> has been added to {}", self.document_name, self.employee)
    
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
        badge = 'Archived' if not self.employee.user.is_active else None
        employee_url = self.employee.get_absolute_url()

        return [{'text': 'Employees', 'badge': None, 'url': employees_url, 'active': False},
                {'text': self.employee, 'badge': badge, 'url': employee_url, 'active': False},
                {'text': self.document.name, 'badge': None, 'url': None, 'active': False},
                {'text': 'Edit', 'badge': None, 'url': None, 'active': True}
        ]

    def get_top_buttons(self):
        return [
            {'type': 'link', 'url': self.employee.get_absolute_url(), 'css_class': 'primary', 'text': 'Back', 'icon': 'arrow-left'},
            {'type': 'popup', 'url': self.document.get_delete_url(), 'css_class': 'danger', 'text': 'Delete', 'icon': 'trash-2'}
            ]

    def get_initial(self, **kwargs):
        return { 'employee': self.document.employee, 
                'name': self.document.name, 
                'sign_date': self.document.sign_date, 
                'document_file': self.document.document_file, 
                'document_type': self.document.document_type, 
                'reference_document': self.document.reference_document
                }

    def form_valid(self, form):
        self.document.update(form.cleaned_data)
        return super().form_valid(form)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
    def get_success_message(self, cleaned_data):
        return format_html("Document <strong>{}</strong> has been updated", cleaned_data['name'])
    
    def get(self, request, *args, **kwargs):
        if self.document.employee.slug != kwargs.pop('slug', None):
            raise HttpResponseBadRequest('Document does not belong to employee')
        return super().get(request, *args, **kwargs)