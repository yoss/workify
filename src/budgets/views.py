from django.contrib.auth.mixins import PermissionRequiredMixin, UserPassesTestMixin, LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.views import generic
from django.db import models
from django.utils.html import format_html
from django.shortcuts import get_object_or_404, redirect, render

from dal import autocomplete


from common.mixins import BreadcrumbsAndButtonsMixin
from common.helpers import Buttons as Btn

from .models import Budget
from .forms import BudgetForm



class BudgetList(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, generic.ListView):
    permission_required = 'budgets.view_budget'
    model = Budget

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Budget.get_cls_breadcrumb())
    
    def set_top_buttons(self):   
        listing_all = self.kwargs.get('all', False)
        if not listing_all:
            self.top_buttons.append(Btn.Link('Show all', Budget.list_all_budgets_url(), css_class= 'outline-primary', icon='eye'))
        if listing_all:
            self.top_buttons.append(Btn.Link('Only active', Budget.list_active_budgets_url(), css_class= 'outline-primary', icon='eye-off'))
        if self.request.user.has_perm('projects.add_project'):
            self.top_buttons.append(Btn.Link('Add budget', Budget.get_create_url(), css_class= 'outline-success', icon='plus'))

    def get_queryset(self):
        if self.kwargs.get('all', False):
            return self.model.objects.all()
        return self.model.objects.filter(is_active=True)
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_can_change_budget'] = self.request.user.has_perm('budgets.change_budget')
        budgets = context['object_list']
        for budget in budgets:
            budget.buttons = []
            if context['user_can_change_budget']:
                budget.buttons.append(
                    Btn.Link('Edit', budget.get_update_url(), css_class='outline-success', icon='edit'),
                )
        context['budgets'] = budgets
        return context
    
class BudegetCreate(BreadcrumbsAndButtonsMixin, PermissionRequiredMixin, SuccessMessageMixin, generic.CreateView):
    permission_required = 'budgets.add_budget'
    model = Budget
    form_class = BudgetForm
    template_name = 'form.html'
    success_message = 'Budget was created successfully.'
    success_url = Budget.list_active_budgets_url()

    def set_breadcrumbs(self):
        self.breadcrumbs.add(**Budget.get_cls_breadcrumb())
        self.breadcrumbs.add(text='Add budget', active=True)
        
    def set_top_buttons(self):
        self.top_buttons.append(Btn.Link('Cancel', Budget.list_active_budgets_url(), css_class= 'outline-primary'))

    def form_valid(self, form):
        form.current_user = self.request.user.employee
        return super().form_valid(form)
    
class BudgetAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Budget.objects.all().filter(is_active=True)
        if self.q:
            qs = qs.filter(models.Q(name__icontains=self.q))
        return qs