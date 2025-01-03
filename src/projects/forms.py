from django import forms
from django.core.validators import URLValidator
from crispy_forms.bootstrap import FormActions
from crispy_forms.layout import Submit, HTML, Layout
from dal import autocomplete

# from employees.models import Employee
from clients.models import Client
from common.mixins import CrispyFormMixin
from .models import Project, ProjectBudgetAssignment

class ProjectForm(CrispyFormMixin, forms.ModelForm):
    current_user = None
    class Meta:
        model = Project
        fields = [
            'name', 'owner', 'managers', 'team_members', 
            'is_public', 'is_chargeable', 'url', 'client'
        ]
        widgets = {
            
            'client': autocomplete.ModelSelect2(url='clients:client-autocomplete'),
            'owner': autocomplete.ModelSelect2(url='employees:employee-autocomplete'),
            'managers': autocomplete.ModelSelect2Multiple(url='employees:employee-autocomplete'),
            'team_members': autocomplete.ModelSelect2Multiple(url='employees:employee-autocomplete'),
            # 'members': forms.CheckboxSelectMultiple(),


            # 'managers': forms.SelectMultiple(attrs={'class': 'form-control'}),
            # 'team_members': forms.SelectMultiple(attrs={'class': 'form-control'}),
            # 'owner': forms.Select(attrs={'class': 'form-control'}),
            # 'client': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)  
        self.fields['client'].queryset = Client.objects.filter(is_active=True)        
        self.helper.layout = Layout(
            'name',
            'owner',
            'managers',
            'team_members',
            'is_public',
            'is_chargeable',
            'url',
            'client',
            FormActions(    
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(f'<a class="btn btn-outline-primary btn-sm" href="{Client.get_list_url()}">Cancel</a>')
            )
        )

# method to clean url field
    def clean_url(self):
        url = self.cleaned_data.get('url')
        if url:
            validate = URLValidator()
            try:
                validate(url)
            except:
                raise forms.ValidationError('Invalid URL')
        return url
    
    def save(self, commit=True):
        if self.current_user is None:
            raise ValueError('current_user is required to save the form')
        project = super().save(commit=False)
        if commit and self.current_user:
            project.save(current_user=self.current_user)
            self.save_m2m()
            self.current_user = None
        return project
    

class ProjectBudgetAssignmentForm(CrispyFormMixin, forms.ModelForm):
    class Meta:
        model = ProjectBudgetAssignment
        fields = [ 'project', 'budget' , 'start_date', 'end_date']
        
        widgets = {
            'budget': autocomplete.ModelSelect2(url='budgets:budget-autocomplete'),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cancel_url = self.initial['project'].get_absolute_url()
        self.helper.layout = Layout(
            'project',
            'budget', 
            'start_date', 
            'end_date',
            FormActions(    
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(f'<a class="btn btn-outline-primary btn-sm" href="{cancel_url}">Cancel</a>')
            ))
        self.fields['project'].widget = forms.HiddenInput()
