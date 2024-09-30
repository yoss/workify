from django.contrib import admin
from .models import Currency, UserGroup, Dimension, EmployeeDocumentTypes

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'default')
    search_fields = ('code', 'name')

@admin.register(EmployeeDocumentTypes)
class EmployeeDocumentTypesAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'default')
    search_fields = ('code', 'name')

@admin.register(UserGroup)
class UserGroupsAdmin(admin.ModelAdmin):
    list_display = ('name', 'group')
    search_fields = ('name', 'group')

@admin.register(Dimension)
class DimensionAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)
    list_filter = ('parent',)