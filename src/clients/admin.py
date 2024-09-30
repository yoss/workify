from django.contrib import admin
from .models import Client, Contract, ContractItem, SalesInvoice

admin.site.register(Client)
admin.site.register(Contract)
admin.site.register(ContractItem)
admin.site.register(SalesInvoice)
