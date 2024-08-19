from django.contrib import admin
from .models import Employee, EmployeeDocument, EmployeeRate

# Register your models here.
admin.site.register(Employee)
admin.site.register(EmployeeDocument)
admin.site.register(EmployeeRate)
