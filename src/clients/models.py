from collections import defaultdict

from django.db import models
from django.urls import reverse

# from common.models import TrackableModel
# from dicts.models import Currency, Dimension
from common import models as common
from dicts import models as dicts
# from employees.models import Employee

class Client(common.TrackableModel):
    slug = models.SlugField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='ClientLogo/', blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_list_url(self): return reverse('clients:client-list')

    @classmethod
    def get_list_all_url(self): return reverse('clients:client-list-all')
    
    @classmethod
    def get_create_url(self): return reverse('clients:client-create')

    @classmethod
    def get_cls_breadcrumb(cls):
        return {'text': 'Clients', 'url': cls.get_list_url()}
    
    def get_breadcrumb(self):
        badge = 'Archived' if not self.is_active else None
        return {'text': self.name, 'url': self.get_absolute_url(), 'badge': badge}
    


    def deactivate(self): self.is_active = False; self.save()
    def activate(self): self.is_active = True; self.save()

    def get_absolute_url(self): return reverse('clients:client-detail', kwargs={'slug': self.slug})
    def get_update_url(self):   return reverse('clients:client-update', kwargs={'slug': self.slug})
    def get_deactivate_url(self): return reverse('clients:client-deactivate', kwargs={'slug': self.slug})
    def get_activate_url(self): return reverse('clients:client-activate', kwargs={'slug': self.slug})

    def get_contract_list_url(self): return reverse('clients:contract-list', kwargs={'slug': self.slug})
    def get_contract_list_all_url(self): return reverse('clients:contract-list-all', kwargs={'slug': self.slug})
    def get_create_contract_url(self): return reverse('clients:contract-create', kwargs={'slug': self.slug})

class Contract(common.TrackableModel):
    slug = models.SlugField(max_length=100, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    number = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    comments = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='contracts', null=True, blank=True)

    def __str__(self):
        return self.number + ' - ' + self.name

    @classmethod
    def get_cls_breadcrumb(cls):
        return {'text': 'Contracts'}

    def get_breadcrumb(self):
        return {'text': self.name, 'url': self.get_absolute_url()}

    def get_total_value_by_currency(self):
        """
        Returns a dictionary where the keys are currency codes and the values are
        the total sum of `ContractItem` values for each currency.
        """
        totals = defaultdict(lambda: 0)

        # Get all related ContractItems
        contract_items = self.contractitem_set.all()

        # Aggregate the values by currency
        for item in contract_items:
            currency_code = item.currency.code  
            totals[currency_code] += item.value

        return dict(totals)
    
    def get_total_invoices_by_currency(self):
        # """
        # Returns a dictionary where the keys are currency codes and the values are
        # the total sum of `ContractItem` values for each currency.
        # """
        # totals = defaultdict(lambda: 0)

        # # Get all related ContractItems
        # contract_items = self.contractitem_set.all()

        # # Aggregate the values by currency
        # for item in contract_items:
        #     currency_code = item.currency.code  # Assuming `Currency` model has a `code` field
        #     totals[currency_code] += item.value

        # return dict(totals)
        pass

    def deactivate(self): self.is_active = False; self.save()
    def activate(self): self.is_active = True; self.save()

    def get_absolute_url(self): return reverse('clients:contract-detail', kwargs={'client_slug': self.client.slug, 'slug': self.slug})
    def get_update_url(self):   return reverse('clients:contract-update', kwargs={'client_slug': self.client.slug, 'slug': self.slug})
    def get_deactivate_url(self): return reverse('clients:contract-deactivate', kwargs={'client_slug': self.client.slug, 'slug': self.slug})
    def get_activate_url(self): return reverse('clients:contract-activate', kwargs={'client_slug': self.client.slug, 'slug': self.slug})
    def get_audit_url(self): return reverse('clients:contract-audit', kwargs={'client_slug': self.client.slug, 'slug': self.slug})

    def get_create_contract_item_url(self): return reverse('clients:contract-item-create', kwargs={'client_slug': self.client.slug, 'slug': self.slug})
    def get_create_invoice_url(self): return reverse('clients:sales-invoice-create', kwargs={'client_slug': self.client.slug, 'slug': self.slug})
    def get_contract_item_list_url(self): return reverse('clients:contract-item-list', kwargs={'client_slug': self.client.slug, 'slug': self.slug})
    def get_contract_invoice_list_url(self): return reverse('clients:sales-invoice-list-contract', kwargs={'client_slug': self.client.slug, 'slug': self.slug})


class ContractItem(common.TrackableModel):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(dicts.Currency, on_delete=models.PROTECT)
    dimension = models.ManyToManyField(dicts.Dimension, blank=True)

    def __str__(self):
        return self.name
    
    @classmethod
    def get_cls_breadcrumb(cls):
        return {'text': 'Contract Items'}
    
    def get_breadcrumb(self):
        return {'text': self.name}

    def get_dimension_category(self):
        return {
                dimension.get_top_level_dimension(): dimension.id 
                for dimension in self.dimension.all()
            }
    def print_dimensions(self):
        return ' | '.join([dimension.name for dimension in self.dimension.all()])

    def get_update_url(self):   
        return reverse('clients:contract-item-update', kwargs={'client_slug': self.contract.client.slug, 'slug': self.contract.slug, 'pk': self.id})
    def get_delete_url(self):   
        return reverse('clients:contract-item-delete', kwargs={'client_slug': self.contract.client.slug, 'slug': self.contract.slug, 'pk': self.id})
    def get_audit_url(self): 
        return reverse('clients:contract-item-audit', kwargs={'client_slug': self.contract.client.slug, 'slug': self.contract.slug, 'pk': self.id})
    def get_invoice_list_url(self): 
        return reverse('clients:sales-invoice-list-contractitem', kwargs={'client_slug': self.contract.client.slug, 'slug': self.contract.slug, 'pk': self.id})
    
class SalesInvoice(common.TrackableModel, common.InvoiceModel):
    contract_item = models.ForeignKey(ContractItem, on_delete=models.PROTECT)
    file = models.FileField(upload_to='SalesInvoice/')

    def __str__(self):
        return self.number
    
    @classmethod
    def get_cls_breadcrumb(cls):
        return {'text': 'Sales Invoices'}
    
    def get_breadcrumb(self):
        return {'text': self.number}    

    def get_absolute_url(self):
        return reverse("clients:sales-invoice-view", kwargs={"pk": self.pk})
    def get_update_url(self):   
        return reverse('clients:sales-invoice-update', kwargs={'pk': self.pk})
    def get_settle_url(self):
        return reverse('clients:sales-invoice-settle', kwargs={'pk': self.pk})
    def get_delete_url(self):   
        return reverse('clients:sales-invoice-delete', kwargs={'pk': self.pk})
    
