from django.shortcuts import render
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import generic

from employees.models import Employee

# Create your views here.

class EmployeeList(PermissionRequiredMixin, generic.ListView):
    permission_required = 'employees.view_employee'
    model = Employee
    context_object_name = 'employees'
    def get_queryset(self):
        if self.kwargs['all']:
            return self.model.objects.all()
        return self.model.objects.filter(user__is_active=True)
