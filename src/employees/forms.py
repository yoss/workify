from django.db.models import Q
from django import forms
from django.utils.html import format_html
from .models import Employee, EmployeeDocument, EmployeeRate
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML
from crispy_forms.bootstrap import FormActions
from django.utils.text import slugify

from dicts import models as dicts

class EmployeeBaseForm(forms.Form):
    email = forms.EmailField()
    tax_id = forms.CharField(max_length=20, required=False)
    groups = forms.MultipleChoiceField( widget=forms.CheckboxSelectMultiple, required=False)
    layout = Layout()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['groups'].choices = dicts.UserGroup.get_choices()
        if not self.initial['user_can_set_user_roles']:
            self.fields['groups'].widget.attrs['disabled'] = 'disabled'
        
    def clean_email(self):
        email = self.cleaned_data['email']
        if self.initial.get('email') and email == self.initial['email']:
            return email
        if User.objects.filter(username = email).exists():
            raise forms.ValidationError("Employee " + email + " already exists.")
        return email
    
    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal'
        helper.label_class = 'col-lg-2'
        helper.field_class = 'col-lg-4'
        helper.layout = self.layout
        return helper

class EmployeeCreateForm(EmployeeBaseForm):
    first_name = forms.CharField()
    last_name = forms.CharField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout = Layout(
                'email', 
                'first_name',
                'last_name',
                'tax_id',
                'groups',
                FormActions(
                    Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                    HTML(format_html('<a class="btn btn-outline-primary btn-sm" href="{}">Cancel</a>', Employee.list_active_employees_url())),
                ),
            )
        
    def save(self, current_user, commit=True):
        employee = Employee.create_employee(self.cleaned_data['first_name'], self.cleaned_data['last_name'], self.cleaned_data['email'], self.cleaned_data['tax_id'], current_user=current_user)
        return employee    

class EmployeeUpdateForm(EmployeeBaseForm):
    slug = forms.CharField(max_length=100, required=False, label='URL Slug')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.layout= Layout(
                'email',
                'slug',
                'tax_id',
                'groups',
                FormActions(
                    Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                    HTML(format_html('<a class="btn btn-outline-primary btn-sm" href="{}">Cancel</a>', self.initial['employee'].get_absolute_url())),
                ),
            )
    
    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if  not slug or slugify(slug).isspace():
            raise forms.ValidationError("Slug cannot be empty.")
        return slug
    
    def save(self, current_user, commit=True):
        employee = self.initial['employee']
        employee.update(email = self.cleaned_data['email'], tax_id=self.cleaned_data['tax_id'], slug = self.cleaned_data['slug'], current_user=current_user)
        if self.initial['user_can_set_user_roles']:
            employee.set_groups(groups=self.cleaned_data.pop('groups' , None), current_user=current_user)
        return employee
    
class EmployeeDocumentForm(forms.ModelForm):
    # name = forms.CharField(max_length=100)
    # sign_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    # document_file = forms.FileField()
    # document_type = forms.ChoiceField(choices=EmployeeDocumentTypes.choices)
    # reference_document = forms.ModelChoiceField(queryset=EmployeeDocument.objects.none(), required=False)
    # comment = forms.CharField(widget=forms.Textarea, required=False)
    employee = Employee()

    class Meta:
        model = EmployeeDocument
        fields = ['name', 'sign_date', 'file', 'document_type', 'reference_document', 'comment']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.instance, 'employee'):
            self.employee = self.instance.employee
        if self.initial.get('employee'):
            self.employee = self.initial['employee']

        self.fields['reference_document'].queryset = EmployeeDocument.objects.filter(employee=self.employee)
        self.fields['sign_date'].widget = forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d')

        self.layout = Layout(
            'name',
            'sign_date',
            'file',
            'document_type',
            'reference_document',
            'comment',
            FormActions(
                    Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                    HTML(format_html('<a class="btn btn-outline-primary btn-sm" href="{}">Cancel</a>', self.employee.get_absolute_url()))
            ),
        )
    def save(self, current_user ,commit=True):
        document = super().save(commit=False)
        document.employee = self.employee
        if commit:
            document.save(current_user=current_user)
        return document
    
    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal'
        helper.label_class = 'col-lg-2'
        helper.field_class = 'col-lg-4'
        helper.layout = self.layout
        return helper

class EmployeeRateForm(forms.ModelForm):
    employee = Employee()
    class Meta:
        model = EmployeeRate
        fields = ['rate_type', 'chargable_rate', 'basic_rate', 'currency', 'valid_from', 'valid_to', 'reference_document', 'comment']
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'valid_to': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
        }
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        if hasattr(self.instance, 'employee'):
            self.employee = self.instance.employee
        if self.initial.get('employee'):
            self.employee = self.initial['employee']
        self.fields['reference_document'].queryset = EmployeeDocument.objects.filter(employee=self.employee)

        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-4'
        self.helper.layout = Layout(
            'rate_type',
            'chargable_rate',
            'basic_rate',
            'currency',
            'valid_from',
            'valid_to',
            'reference_document',
            'comment',
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(format_html('<a class="btn btn-outline-primary btn-sm" href="{}">Cancel</a>', self.employee.get_absolute_url()))
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get("valid_from")
        valid_to = cleaned_data.get("valid_to")
        if hasattr(self.instance, 'employee'):
            employee = self.instance.employee
        if self.initial.get('employee'):
            employee = self.initial['employee']
        
        # Ensure valid_from is not later than valid_to
        if valid_to and valid_from > valid_to:
            raise forms.ValidationError("The 'valid from' date cannot be later than the 'valid to' date.")
        
        # check for overlapping rates for rate with undefined valid to date
        if valid_to is None:
            overlapping_rates = EmployeeRate.objects.filter(
                employee=employee
            ).exclude(
                pk=self.instance.pk  # Exclude current instance if updating
            ).filter(
                Q(valid_to__isnull=True) |  # Another indefinite rate
                Q(valid_to__gte=valid_from)  # Overlaps with any rate that starts before or at the same time
            )

        # Case 2: If `valid_to` has a date
        if valid_to:
            overlapping_rates = EmployeeRate.objects.filter(
                employee=employee
            ).exclude(
                pk=self.instance.pk  # Exclude current instance if updating
            ).filter(
                Q(valid_from__lte=valid_to) & Q(valid_from__gte=valid_from) |  # Overlaps with existing rate range
                Q(valid_to__gte=valid_from) & Q(valid_to__lte=valid_to) |  # Overlaps with existing rate range
                Q(valid_to__isnull=True) & Q(valid_from__lte=valid_to)  # Overlaps with an indefinite rate
            )

        if overlapping_rates.exists():
            raise forms.ValidationError("There is an overlap with an existing rate for the selected dates.")
        
        return cleaned_data
    
    def save(self, current_user, commit=True):
        rate = super().save(commit=False)
        rate.employee = self.employee
        if commit:
            rate.save(current_user=current_user)
        return rate