from django.contrib import messages
from django.utils.html import format_html
from django.shortcuts import redirect


class EmployeeStatusMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.employee.is_inactive:
            messages.error(request, format_html("Employee <strong>{}</strong> is inactive.", self.employee))
            return redirect(self.employee.get_absolute_url())        
        return super().dispatch(request, *args, **kwargs)