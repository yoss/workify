from typing import Any
from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404, HttpResponseBadRequest
from django.views import generic
from django.utils.html import format_html
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect, render
from django.db import models
from django.contrib import messages
from dal import autocomplete

from .models import Project, ProjectBudgetAssignment
from .forms import ProjectForm, ProjectBudgetAssignmentForm
from common.mixins import BreadcrumbsAndButtonsMixin

from common.helpers import Buttons as Btn


class ProjectList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = 'projects.view_project'
    model = Project
    # context_object_name = 'projects'

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Project.get_cls_breadcrumb())
    
    def set_top_buttons(self):   
        listing_all = self.kwargs.get('all', False)
        if not listing_all:
            self.top_buttons.append(Btn.Link('Show all', Project.list_all_projects_url(), css_class= 'outline-primary', icon='eye'))
        if listing_all:
            self.top_buttons.append(Btn.Link('Only active', Project.list_active_projects_url(), css_class= 'outline-primary', icon='eye-off'))
        if self.request.user.has_perm('projects.add_project'):
            self.top_buttons.append(Btn.Link('Add project', Project.get_create_url(), css_class= 'outline-success', icon='plus'))

    def get_queryset(self):

        # TODO - depending on the permissions, show all or only public projects and projects current user is assigned to
        if self.kwargs.get('all', False):
            return self.model.objects.all()
        return self.model.objects.filter(is_active=True)
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_can_change_project'] = self.request.user.has_perm('projects.change_project')
        projects = context['object_list']
        for project in projects:
            project.buttons = []
            if context['user_can_change_project']:
                project.buttons.append(
                    Btn.Link('Edit', project.get_update_url(), css_class='outline-success', icon='edit'),
                )
        context['projects'] = projects
        return context

class ProjectEditBaseView(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin):
    model = Project
    form_class = ProjectForm
    template_name = 'form.html'

    def form_valid(self, form):
        form.current_user = self.request.user.employee
        return super().form_valid(form)

class ProjectCreate(ProjectEditBaseView, generic.CreateView):
    permission_required = 'projects.add_project'
    success_message = 'Project was created successfully.'
    success_url = Project.list_active_projects_url()

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Project.get_cls_breadcrumb())
        self.breadcrumbs.add(text='Add project', active=True)

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Cancel', Project.list_active_projects_url(), css_class= 'outline-primary'))
    
class ProjectUpdate(ProjectEditBaseView, generic.UpdateView):
    permission_required = 'projects.change_project'
    success_message = 'Project was updated successfully.'
    object = Project()

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Project.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.object.get_breadcrumb())
        self.breadcrumbs.add(text='Edit', active=True)

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Cancel', self.object.get_absolute_url(), css_class= 'outline-primary', icon='arrow-left'))
        if self.object.is_active:
            self.top_buttons.append(Btn.ShowPopup('Deactivate', self.object.get_deactivate_url(), css_class= 'outline-danger', icon='zap-off'))
        if not self.object.is_active:
            self.top_buttons.append(Btn.ShowPopup('Activate', self.object.get_activate_url(), css_class= 'outline-success', icon='zap'))
    
    def get_success_url(self):
        return self.object.get_absolute_url()

class ProjectDeactivate(PermissionRequiredMixin, generic.DetailView):
    permission_required = 'projects.change_project'
    model = Project

    def get(self, request, *args, **kwargs):
        project = self.get_object()
        popup_dict = {
            'title': 'Deactivate project',
            'body': format_html(f'Are you sure you want to deactivate project <strong>{project}</strong>?'),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Deactivate', project.get_deactivate_url(), css_class='danger', size=None)
            ]
        }
        return render(request, 'popup.html', {'popup': popup_dict})   

    def post (self, request, *args, **kwargs):
        project = self.get_object()
        project.is_active = False
        project.save(current_user=request.user.employee)
        messages.success(request, format_html(f'Project <strong>{project}</strong> was deactivated successfully.'))
        return redirect(Project.list_active_projects_url())
    
class ProjectActivate(PermissionRequiredMixin, generic.DetailView):
    permission_required = 'projects.change_project'
    model = Project

    def get(self, request, *args, **kwargs):
        project = self.get_object()
        popup_dict = {
            'title': 'Activate project',
            'body': format_html(f'Are you sure you want to activate project <strong>{project}</strong>?'),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Activate', project.get_activate_url(), css_class='success', size=None)
            ]
        }
        return render(request, 'popup.html', {'popup': popup_dict})   

    def post (self, request, *args, **kwargs):
        project = self.get_object()
        project.is_active = True
        project.save(current_user=request.user.employee)
        messages.success(request, format_html(f'Project <strong>{project}</strong> was activated successfully.'))
        return redirect(Project.list_active_projects_url())
    
class ProjectDetail(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, generic.DetailView):
    permission_required = 'projects.view_project'
    model = Project

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Project.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.object.get_breadcrumb(return_url=False))

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Back', Project.list_active_projects_url(), css_class= 'outline-primary', icon='arrow-left'))
        self.top_buttons.append(Btn.Link('Edit', self.object.get_update_url(), css_class= 'outline-success', icon='edit'))
        # self.top_buttons.append(Btn.ShowPopup('add budget', self.object.get_add_budget_url(), css_class= 'outline-success', icon='plus'))

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['user_can_change_project'] = self.request.user.has_perm('projects.change_project')
    #     return context
    # TODO: return all project details / update template

class ProjectBudgetList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = 'projects.view_projectbudgetassignment'
    model = ProjectBudgetAssignment
    template_name = 'projects/project_budget_list.html'
    context_object_name = 'project_budgets'
    project = Project()

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.project = get_object_or_404(Project, slug=self.kwargs.get('slug'))

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**ProjectBudgetAssignment.get_cls_breadcrumb())
    
    def set_top_buttons(self):   
        self.top_buttons.append(Btn.Link('Assign budget', self.project.get_create_budget_url(), css_class= 'outline-success', icon='plus'))

    def get_queryset(self):
        return self.model.objects.filter(project=self.project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_budgets = context['project_budgets']
        for project_budget in project_budgets:
            # check if current date is between start and stop date of budget assignment, if yes than flag budger as current
            project_budget.is_current = project_budget.start_date <= timezone.now().date() and (project_budget.end_date is None or project_budget.end_date >= timezone.now().date())
            project_budget.buttons = []
            project_budget.buttons.append(Btn.Link('Edit', project_budget.get_update_url(), css_class='outline-success', icon='edit'))
            project_budget.buttons.append(Btn.ShowPopup('Delete', project_budget.get_delete_url(), css_class='outline-danger', icon='trash-2'))
        context['project_budgets'] = project_budgets
        return context
    
class ProjectBudgetBaseView(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin):
    model = ProjectBudgetAssignment
    permission_required = 'projects.change_project'
    object = ProjectBudgetAssignment()
    form_class = ProjectBudgetAssignmentForm
    template_name = 'form.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.project = get_object_or_404(Project, slug=self.kwargs.get('slug'))

    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Cancel', self.project.get_absolute_url(), css_class= 'outline-primary'))
        
    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Project.get_cls_breadcrumb())
        self.breadcrumbs.add(**self.project.get_breadcrumb())   
        
    def get_initial(self):
        return {'project': self.project}

    def get_success_url(self):
        return self.project.get_absolute_url()
    
    def form_valid(self, form):
        form.instance.project = self.project
        return super().form_valid(form)

class ProjectBudgetCreate(ProjectBudgetBaseView, generic.CreateView): 
    success_message = 'Budget added.'

    def set_breadcrumbs(self):
        super().set_breadcrumbs()
        self.breadcrumbs.add(text='Assign budget', active=True)
    
class ProjectBudgetUpdate(ProjectBudgetBaseView, generic.UpdateView):
    success_message = 'Budget has been updated.'
    
    def set_breadcrumbs(self):
        super().set_breadcrumbs()
        self.breadcrumbs.add(text='Edit assigned budget', active=True)

class ProjectBudgetDelete(generic.DeleteView):
    model = ProjectBudgetAssignment
    permission_required = 'projects.change_project'
    project_budget = ProjectBudgetAssignment()

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.project_budget = self.get_object()

    def get(self, request, *args, **kwargs):
        popup_dict = {
            'title': 'Remove budget assignment',
            'body': format_html(f'Are you sure you want to remove budget <strong>{self.project_budget.budget}</strong> from <strong>{self.project_budget.project}</strong>?'),
            'buttons': [
                Btn.HidePopup('Cancel', css_class='secondary', size=None),
                Btn.PostCall('Delete', self.project_budget.get_delete_url(), css_class='danger', size=None)
            ]
        }
        return render(request, 'popup.html', {'popup': popup_dict})   

    def post (self, request, *args, **kwargs):
        messages.success(request, format_html(f'Budget <strong>{self.project_budget.budget}</strong> was removed from project.'))
        self.project_budget.delete()
        return redirect(self.project_budget.project.get_absolute_url())