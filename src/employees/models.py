import hashlib
from io import BytesIO
from django.contrib import messages
from django.utils.html import format_html
from django.shortcuts import redirect
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse, reverse_lazy
from django.core.files.base import ContentFile
from PIL import Image
from utils.unique_slugify import unique_slugify


class Employee(models.Model):    
    slug = models.SlugField(max_length=100, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    tax_id = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='EmployeeAvatar/', blank=True)
    avatar_checksum = models.CharField(blank=True, max_length=50)

    @classmethod
    def create_employee(cls, first_name, last_name, email, password, tax_id, avatar=None):
        user = User.objects.create_user(username=email, email=email, password=password, first_name=first_name, last_name=last_name)
        slug = unique_slugify(cls, first_name + ' ' + last_name)
        employee = cls(user=user, tax_id=tax_id, slug=slug, avatar=avatar)
        employee.save()
        return employee

    @classmethod
    def list_active_employees_url(cls):
        return reverse_lazy('employees:employee-list')
    
    def __str__(self):
        return self.user.get_full_name()

    def email(self):
        return self.user.email 

    def sso_update_avatar(self, avatar_content):
        if not avatar_content:
            return        
        avatar_content_checksum = hashlib.md5(avatar_content).hexdigest()
        if self.avatar_checksum != avatar_content_checksum:
            resized_avatar = Image.open(ContentFile(avatar_content)).resize((256, 256), Image.LANCZOS)
            avatar_bytes = BytesIO()
            resized_avatar.save(avatar_bytes, format='PNG')
            avatar_bytes.seek(0)
            # Save the BytesIO object to the avatar field
            self.avatar.save('avatar_' + str(self.user.id) + '.png', ContentFile(avatar_bytes.read()))
            self.avatar_checksum = avatar_content_checksum
            self.save()
        return
    
    def update(self, email, tax_id, slug = None):
        self.user.email = email
        self.user.username = email
        self.tax_id = tax_id
        if slug and self.slug != slug:
            self.slug = unique_slugify(self.__class__, slug)
        self.user.save()    
        self.save()
        return

    def deactivate(self, request):
        self.user.is_active = False
        self.user.save()
        messages.error(request, format_html("Employee <strong>{}</strong> has been deactivated", self))
        return
    
    def activate(self, request):
        self.user.is_active = True
        self.user.save()
        messages.success(request, format_html("Employee <strong>{}</strong> has been activated", self))
        return

    def redirect_if_inactive(self, request, callback):
        if not self.user.is_active:
            messages.error(request, format_html("Employee <strong>{}</strong> is inactive.", self))
            return redirect(self.get_absolute_url())
        return callback


    def get_absolute_url(self): return reverse('employees:employee-detail', kwargs={'slug': self.slug})
    def get_update_url(self):   return reverse('employees:employee-update', kwargs={'slug': self.slug})
    def get_deactivate_url(self): return reverse('employees:employee-deactivate', kwargs={'slug': self.slug})
    def get_activate_url(self): return reverse('employees:employee-activate', kwargs={'slug': self.slug})