from django.contrib import admin
from .models import Employee, EmployeeDocument, EmployeeRate

# Register your models here.
class EmployeeAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Employee, EmployeeAdmin)
admin.site.register(EmployeeDocument)
admin.site.register(EmployeeRate)
