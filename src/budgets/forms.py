from django import forms
from django.core.validators import URLValidator
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import Submit, HTML, Layout
from dal import autocomplete

# from employees.models import Employee
from common.mixins import CrispyFormMixin
from clients.models import Client
from .models import Budget 


class BudgetForm(CrispyFormMixin, forms.ModelForm):
    current_user = None
    class Meta:
        model = Budget
        fields = [
            'name', 'description', 'value', 'currency', 'is_active'
        ]

    def __init__(self, *args, **kwargs):
        # super(ProjectForm, self).__init__(*args, **kwargs)  
        super().__init__(*args, **kwargs)
        # self.fields['client'].queryset = Client.objects.filter(is_active=True)        
        self.helper.layout = Layout(
            'name',
            'description',
            'value',
            'currency',
            'is_active',
            FormActions(    
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(f'<a class="btn btn-outline-primary btn-sm" href="{Budget.list_active_budgets_url()}">Cancel</a>')
            )
        )
    
    def save(self, commit=True):
        if self.current_user is None:
            raise ValueError('current_user is required to save the form')
        budget = super().save(commit=False)
        if commit and self.current_user:
            budget.save(current_user=self.current_user)
            self.save_m2m()
            self.current_user = None
        return budget