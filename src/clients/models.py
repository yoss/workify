from django.db import models
from django.urls import reverse

class Client(models.Model):
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

    def deactivate(self): self.is_active = False; self.save()
    def activate(self): self.is_active = True; self.save()

    def get_absolute_url(self): return reverse('clients:client-detail', kwargs={'slug': self.slug})
    def get_update_url(self):   return reverse('clients:client-update', kwargs={'slug': self.slug})
    def get_deactivate_url(self): return reverse('clients:client-deactivate', kwargs={'slug': self.slug})
    def get_activate_url(self): return reverse('clients:client-activate', kwargs={'slug': self.slug})
