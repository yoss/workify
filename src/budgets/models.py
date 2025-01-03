from django.db import models
from django.urls import reverse, reverse_lazy
from common.models import TrackableModel
from dicts import models as dicts

# Create your models here.
class Budget(TrackableModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(dicts.Currency, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)    
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self): return reverse("budgets:budget-detail", kwargs={'pk': self.pk})
    def get_update_url(self): return reverse("budgets:budget-update", kwargs={'pk': self.pk})
    def get_deactivate_url(self): return reverse("budgets:budget-deactivate", kwargs={'pk': self.pk})
    def get_activate_url(self): return reverse("budgets:budget-activate", kwargs={'pk': self.pk})

    @classmethod
    def list_all_budgets_url(cls): return reverse_lazy('budgets:budget-list-all')
    
    @classmethod
    def list_active_budgets_url(cls): return reverse_lazy('budgets:budget-list')
    
    @classmethod
    def get_create_url(cls): return reverse_lazy('budgets:budget-create')
    
    @classmethod
    def get_cls_breadcrumb(cls, *, return_url = True):
        if return_url:
            return {'text': 'Budgets', 'url': cls.list_active_budgets_url()}
        return {'text': 'Budgetss'}
    
    def get_breadcrumb(self, *, return_url = True):
        url = None
        if return_url:
            url = self.get_absolute_url()
        if not self.is_active:
            return {'text': str(self), 'badge': 'Archived', 'url': url}
        return {'text': str(self), 'url': url}
    

# class CostItem(models.Model):
#     name = models.CharField(max_length=100)
#     budget = models.ForeignKey(Budget, on_delete=models.CASCADE, blank=True, null=True) 
#     value = models.DecimalField(max_digits=10, decimal_places=2)
#     currency = models.ForeignKey(dicts.Currency, on_delete=models.PROTECT)
#     value_in_budget_currency = models.DecimalField(max_digits=10, decimal_places=2)
#     date = models.DateField()
    # time_report
    # cost_invoice