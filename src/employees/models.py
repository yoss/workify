import hashlib
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
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
    def list_employees(cls):
        return reverse('employees:employee-list')
    
    def sso_update_avatar(self, avatar_content):
        if not avatar_content:
            return        
        avatar_content_checksum = hashlib.md5(avatar_content).hexdigest()
        if self.avatar_checksum != avatar_content_checksum:
            resized_avatar = Image.open(ContentFile(avatar_content)).resize((256, 256), Image.LANCZOS)
            self.avatar.save('avatar_' + str(self.user.id) + '.jpg', resized_avatar)
            self.avatar_checksum = avatar_content_checksum
            self.save()
        return
    
    def deactivate(self):
        self.user.is_active = False
        self.user.save()
        return
    
    def activate(self):
        self.user.is_active = True
        self.user.save()
        return