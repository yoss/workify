from django.db import models

# Create your models here.
class Currencies(models.TextChoices):
    USD = 'USD', 'US Dollar'
    EUR = 'EUR', 'Euro'
    PLN = 'PLN', 'Polish Zloty'