import datetime
from django.db import models
# from dicts.models import Currency
from dicts import models as dicts
# from employees.models import Employee

# Create your models here.
class Currencies(models.TextChoices):
    USD = 'USD', 'US Dollar'
    EUR = 'EUR', 'Euro'
    PLN = 'PLN', 'Polish Zloty'

class TrackableModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='%(class)s_created', null=True)
    updated_by = models.ForeignKey('employees.Employee', on_delete=models.CASCADE, related_name='%(class)s_updated', null=True)
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        if not current_user:
            return super().save(*args, **kwargs)
        if not self.pk:
            self.created_by = current_user
        self.updated_by = current_user
        return super().save(*args, **kwargs)

    def get_audit_trail(self):
        return {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "created_by": self.created_by,
            "updated_by:": self.updated_by
        }
    
    def get_mini_audit(self):
        return f'Created {self.created_at.strftime("%d-%m-%Y %H:%M")} by {self.created_by} | Updated {self.updated_at.strftime("%d-%m-%Y %H:%M")} by {self.updated_by}'
    
class InvoiceModel(models.Model):
    number = models.CharField(max_length=100)
    date = models.DateField()
    due_date = models.DateField()
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(dicts.Currency, on_delete=models.PROTECT)
    
    class Meta:
        abstract = True

    @property
    def status(self):
        if self.is_paid:
            return 'Paid'
        if self.due_date > datetime.date.today():
            return 'Unpaid'
        return 'Overdue'
    
    def settle(self):
        self.is_paid = True
        self.paid_date = datetime.date.today()
        self.save()