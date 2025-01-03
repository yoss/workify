import uuid
from django.db import models
from django.forms import ValidationError
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify

from utils.unique_slugify import unique_slugify
from common.models import TrackableModel  

from employees.models import Employee  
from clients.models import Client  
from budgets.models import Budget

class Project(TrackableModel):
    name = models.CharField(max_length=255, unique=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    owner = models.ForeignKey(Employee, on_delete=models.PROTECT, related_name='owned_projects') 
    managers = models.ManyToManyField(Employee, related_name='managed_projects')  
    team_members = models.ManyToManyField(Employee, related_name='team_projects', blank=True)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    is_chargeable = models.BooleanField(default=False)
    url = models.URLField(blank=True, null=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name='projects')  # Optional

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self.__class__ ,self.name)
        # CHECK UPDATE SLUG process
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self): return reverse("projects:project-detail", kwargs={"slug": self.slug})
    def get_update_url(self): return reverse("projects:project-update", kwargs={"slug": self.slug})
    def get_deactivate_url(self): return reverse("projects:project-deactivate", kwargs={"slug": self.slug})
    def get_activate_url(self): return reverse("projects:project-activate", kwargs={"slug": self.slug})
    def get_create_budget_url(self): return reverse("projects:project-budget-create", kwargs={"slug": self.slug})
    def get_list_project_bugdets_url(self): return reverse("projects:project-budget-list", kwargs={"slug": self.slug})

    
    @classmethod
    def list_active_projects_url(cls): return reverse_lazy('projects:project-list')

    @classmethod
    def list_all_projects_url(cls): return reverse_lazy('projects:project-list-all')

    @classmethod
    def get_create_url(cls): return reverse_lazy('projects:project-create')

    @classmethod
    def get_cls_breadcrumb(cls, *, return_url = True):
        if return_url:
            return {'text': 'Projects', 'url': cls.list_active_projects_url()}
        return {'text': 'Projects'}
    
    def get_breadcrumb(self, *, return_url = True):
        url = None
        if return_url:
            url = self.get_absolute_url()
        if not self.is_active:
            return {'text': str(self), 'badge': 'Archived', 'url': url}
        return {'text': str(self), 'url': url}
    
class ProjectBudgetAssignment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # Optional field

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(end_date__isnull=True) | models.Q(end_date__gt=models.F('start_date')),
                name='check_end_date_after_start_date_or_null'
            ),
        ]

    def get_update_url(self): return reverse("projects:project-budget-update", kwargs={"slug": self.project.slug, "pk": self.pk})
    def get_delete_url(self): return reverse("projects:project-budget-delete", kwargs={"slug": self.project.slug, "pk": self.pk})
    

    @classmethod
    def get_cls_breadcrumb(cls, *, return_url = True):
        return {'text': 'Budgets'}
    
    def __str__(self):
        if self.end_date:
            return f"{self.budget.name} for {self.project.name} ({self.start_date} to {self.end_date})"
        return f"{self.budget.name} for {self.project.name} (from {self.start_date})"

    def clean(self):
        # Ensure no overlapping assignments for the same project
        overlapping_assignments = ProjectBudgetAssignment.objects.filter(
            project=self.project,
            start_date__lte=self.end_date if self.end_date else self.start_date,
            end_date__gte=self.start_date,
        ).exclude(pk=self.pk)

        if overlapping_assignments.exists():
            raise ValidationError("Overlapping budget assignment exists for this project.")

