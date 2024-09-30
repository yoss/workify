from django.db import models
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