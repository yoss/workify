from django.db import models
from django.contrib.auth.models import Group

class BaseDict(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=50)
    default = models.BooleanField(default=False)
    
    class Meta:
        abstract = True

    def __str__(self):
        return self.name
    
    @classmethod
    def get_choices(cls):
        return [(element.id, f"{element}") for element in cls.objects.all()]
    
    @classmethod
    def get_default(cls):
        return cls.objects.filter(default=True).first()
    
    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        if self.default:
            # get class of self
            cls = self.__class__
            cls.objects.filter(default=True).update(default=False)
        super().save(*args, **kwargs)

class Currency(BaseDict):
    class Meta:
        verbose_name_plural = 'Currencies'
        ordering = ['code']
        
    def __str__(self):
        return f"{self.name} ({self.code})"

class EmployeeDocumentTypes(BaseDict):
    code = models.CharField(max_length=25, unique=True)
    class Meta:
        verbose_name_plural = 'Employee Document Types'
        ordering = ['code']


class UserGroup(models.Model):
    name = models.CharField(max_length=50, unique=True)
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    
    class Meta:
        verbose_name_plural = 'User Groups'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @classmethod
    def get_choices(cls):
        return [(f"{element.group}", f"{element}") for element in cls.objects.all()]
    
class Dimension(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='children')
  
    class Meta:
        verbose_name_plural = 'Dimensions'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_top_level_dimension(self):
        """
        Recursively find the top-level dimension (the one without a parent).
        """
        if self.parent is None:
            # If the current dimension has no parent, it is the top-level dimension
            return self
        else:
            # Recursively call the method on the parent
            return self.parent.get_top_level_dimension()