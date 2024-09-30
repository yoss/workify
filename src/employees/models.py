import hashlib
from io import BytesIO

from django.contrib import messages
from django.contrib.auth.models import Group, User
from django.utils.html import format_html
from django.shortcuts import redirect
from django.db import models
from django.urls import reverse, reverse_lazy
from django.core.files.base import ContentFile
from PIL import Image
from utils.unique_slugify import unique_slugify
from common.models import TrackableModel
from dicts import models as dicts


class Employee(TrackableModel):    
    slug = models.SlugField(max_length=100, unique=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    tax_id = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='EmployeeAvatar/', blank=True)
    avatar_checksum = models.CharField(blank=True, max_length=50)

    class Meta:
        permissions = [
            ('can_view_employee_list', 'Can view employee list'),
            ('can_view_archived_employees', 'Can view archived employee list'),
            ('view_all_employee_details', 'Can view all employee details'),
            ('can_set_user_roles', 'Can set user roles'),
        ]

    @classmethod
    def create_employee(cls, first_name, last_name, email, tax_id, current_user):
        user = User.objects.create_user(username=email, email=email, password=None, first_name=first_name, last_name=last_name)
        slug = unique_slugify(cls, first_name + ' ' + last_name)
        employee = cls(user=user, tax_id=tax_id, slug=slug)
        employee.created_by = current_user
        employee.save(current_user=current_user)
        return employee

    @classmethod
    def list_active_employees_url(cls): return reverse_lazy('employees:employee-list')

    @classmethod
    def list_all_employees_url(cls): return reverse_lazy('employees:employee-list-all')

    @classmethod
    def get_create_url(cls): return reverse_lazy('employees:employee-create')
    
    def __str__(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email 
    
    @property
    def is_inactive(self):
        return not self.user.is_active
    
    @property
    def is_active(self):
        return self.user.is_active

    @classmethod
    def get_cls_breadcrumb(cls, *, return_url = True):
        if return_url:
            return {'text': 'Employees', 'url': cls.list_active_employees_url()}
        return {'text': 'Employees'}

    def get_breadcrumb(self):
        if not self.user.is_active:
            return {'text': str(self), 'url': self.get_absolute_url(), 'badge': 'Archived'}
        return {'text': str(self), 'url': self.get_absolute_url()}

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
    
    def set_groups(self, groups, current_user):
        self.user.groups.clear()
        for group_name in groups:
            group = Group.objects.get(name=group_name)
            self.user.groups.add(group) 
        self.save(current_user=current_user)
        return
        

    def update(self, email, tax_id, slug, current_user):
        self.user.email = email
        self.user.username = email
        self.user.save()
        self.tax_id = tax_id
        if slug and self.slug != slug:
            self.slug = unique_slugify(self.__class__, slug)
        self.save(current_user=current_user)    
        return

    def get_groups(self):
        groups =  self.user.groups.all()
        groups_name = [group.name for group in groups]
        dicts.UserGroup.objects.filter(group__in=groups).values_list('name', flat=True)

    def deactivate(self, current_user):
        self.user.is_active = False
        self.user.save()
        self.save(current_user=current_user)
        return
    
    def activate(self, current_user):
        self.user.is_active = True
        self.user.save()
        self.save(current_user=current_user)
        return

    def get_absolute_url(self): return reverse('employees:employee-detail', kwargs={'slug': self.slug})
    def get_update_url(self):   return reverse('employees:employee-update', kwargs={'slug': self.slug})
    def get_deactivate_url(self): return reverse('employees:employee-deactivate', kwargs={'slug': self.slug})
    def get_activate_url(self): return reverse('employees:employee-activate', kwargs={'slug': self.slug})

    def get_documents_list_url(self): return reverse('employees:employee-document-list', kwargs={'slug': self.slug})
    def get_new_document_url(self): return reverse('employees:employee-document-create', kwargs={'slug': self.slug})

    def get_rates_list_url(self): return reverse('employees:employee-rate-list', kwargs={'slug': self.slug})
    def get_new_rate_url(self): return reverse('employees:employee-rate-create', kwargs={'slug': self.slug})


# class EmployeeDocumentTypes(models.TextChoices):
#     CONTRACT = 'contract', 'Contract'
#     AMENDMENT = 'amendment', 'Amendment'
#     TERMINATION = 'termination', 'Termination Notice'
#     OTHER = 'other', 'Other'

class EmployeeDocument(TrackableModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    sign_date = models.DateField()
    file = models.FileField(upload_to='EmployeeDocuments/')
    document_type = models.ForeignKey(dicts.EmployeeDocumentTypes, on_delete=models.PROTECT)
    # document_type = models.CharField(max_length=20, choices=EmployeeDocumentTypes.choices)
    reference_document = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.sign_date.strftime('%d.%m.%Y')}" 
    
    @classmethod
    def get_cls_breadcrumb(cls, *, return_url = True):
        return {'text': 'Documents'}
    
    def get_breadcrumb(self, *, return_url = True):
        return {'text': self.name}

    def get_absolute_url(self):   return reverse('employees:employee-document-detail', kwargs={'slug': self.employee.slug, 'pk': self.pk})
    def get_update_url(self):   return reverse('employees:employee-document-update', kwargs={'slug': self.employee.slug, 'pk': self.pk})
    def get_delete_url(self):   return reverse('employees:employee-document-delete', kwargs={'slug': self.employee.slug, 'pk': self.pk})

class EmployeeRateTypes(models.TextChoices):
    B2B = 'hourly', 'Hourly (B2B)'
    PERMANENT = 'monthly', 'Monthly (Employment Contract)'

class BaseEmployeeRate(TrackableModel):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    currency = models.ForeignKey(dicts.Currency, on_delete=models.PROTECT)
    valid_from = models.DateField()
    valid_to = models.DateField(blank=True, null=True)
    reference_document = models.ForeignKey(EmployeeDocument, on_delete=models.CASCADE, blank=True, null=True)
    comment = models.TextField(blank=True, null=True)

    class Meta:
        abstract = True

    @classmethod
    def get_cls_breadcrumb(cls, *, return_url = True):
        return {'text': 'Rates'}
    
    def get_breadcrumb(self, *, return_url = True):
        return {'text': self.__str__()}

    def get_update_url(self):   return reverse('employees:employee-rate-update', kwargs={'slug': self.employee.slug, 'pk': self.pk})
    def get_delete_url(self):   return reverse('employees:employee-rate-delete', kwargs={'slug': self.employee.slug, 'pk': self.pk})

class EmployeeRate(BaseEmployeeRate):
    rate_type = models.CharField(max_length=20, choices=EmployeeRateTypes.choices)
    chargable_rate = models.DecimalField(max_digits=10, decimal_places=2)
    basic_rate = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        if self.chargable_rate == self.basic_rate:
            rate = f"{self.chargable_rate} {self.currency}"   
        if self.chargable_rate != self.basic_rate:
            rate = f"{self.chargable_rate} | {self.basic_rate} {self.currency}"
        if self.valid_to and self.valid_from.strftime('%b %Y') == self.valid_to.strftime('%b %Y'):
            return f"{rate} - {self.valid_from.strftime('%b %Y')}"
        return f"{rate} - {self.valid_from.strftime('%b %Y')} → {self.valid_to.strftime('%b %Y') if self.valid_to else 'current'}"


# class EmployeeProjectRate(BaseEmployeeRate):
#     project = 
#     rate = models.DecimalField(max_digits=10, decimal_places=2)
    
#     def __str__(self):
#         if self.chargable_rate == self.basic_rate:
#             rate = f"{self.chargable_rate} {self.currency}"   
#         if self.chargable_rate != self.basic_rate:
#             rate = f"{self.chargable_rate} | {self.basic_rate} {self.currency}"
#         if self.valid_to and self.valid_from.strftime('%b %Y') == self.valid_to.strftime('%b %Y'):
#             return f"{rate} - {self.valid_from.strftime('%b %Y')}"
#         return f"{rate} - {self.valid_from.strftime('%b %Y')} → {self.valid_to.strftime('%b %Y') if self.valid_to else 'current'}"
