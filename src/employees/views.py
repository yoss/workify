from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views import generic
# from django.contrib.auth.models import User
from django.utils.html import format_html
from django.shortcuts import get_object_or_404, redirect, render
# from django.contrib import messages

from employees.models import Employee
from employees.permissions import employee_detail_permission
from .forms import EmployeeCreateForm, EmployeeUpdateForm


class EmployeeList(PermissionRequiredMixin, generic.ListView):
    permission_required = 'employees.can_view_employee_list'
    model = Employee
    context_object_name = 'employees'

    def get_queryset(self):
        if self.kwargs.get('all', False) and self.request.user.has_perm('employees.can_view_archived_employees'):
            return self.model.objects.all()
        return self.model.objects.filter(user__is_active=True)

class EmployeeDetail(UserPassesTestMixin, generic.DetailView):
    model = Employee
    context_object_name = 'employee'

    def test_func(self): return employee_detail_permission(self)

class EmployeeCreate(PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.add_employee'
    form_class = EmployeeCreateForm
    template_name = 'employees/employee_create_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        cd = form.cleaned_data
        self.employee = Employee.create_employee(cd['first_name'], cd['last_name'], cd['email'], None, cd['tax_id'])
        return super().form_valid(form)   
    
    def get_success_message(self, cleaned_data):
        return format_html("Employee <strong>{}</strong> has been created", self.employee)

    def get_success_url(self):
        return self.employee.get_absolute_url()
    
class EmployeeUpdate(PermissionRequiredMixin, SuccessMessageMixin, generic.FormView):
    permission_required = 'employees.change_employee'
    form_class = EmployeeUpdateForm
    template_name = 'employees/employee_update_form.html'
    employee = Employee()

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def setup(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, slug=kwargs['slug'])
        return super().setup(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        return self.employee.redirect_if_inactive(request, callback=super().dispatch(request, *args, **kwargs))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["employee"] = self.employee
        return context
    
    def form_valid(self, form):
        cd = form.cleaned_data
        if not self.request.user.has_perm('employees.can_set_user_roles'):
            cd.pop('groups')
        self.employee.update(email = cd['email'], tax_id=cd['tax_id'], slug = cd['slug'], groups = cd.get('groups'))
        return super().form_valid(form)
    
    def get_initial(self, **kwargs):
        employee_groups = list(self.employee.user.groups.values_list('name', flat=True))
        return {'email': self.employee.user.email, 'slug': self.employee.slug, 'tax_id': self.employee.tax_id, 'employee': self.employee, 'groups': employee_groups}
    
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
        self.employee.deactivate(request)
        return redirect(Employee.list_active_employees_url())
        
class EmployeeActivate(EmployeeToogle):
    def get(self, request, *args, **kwargs):
        return render(request, 'employees/employee_activate_popup.html', {'employee': self.employee})

    def post(self, request, *args, **kwargs):
        self.employee.activate(request)
        return redirect(self.employee.get_absolute_url())
