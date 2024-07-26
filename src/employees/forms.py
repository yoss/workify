from django import forms
from django.utils.html import format_html
from .models import Employee
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML
from crispy_forms.bootstrap import FormActions
from django.utils.text import slugify



class EmployeeCreateForm(forms.Form):
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    tax_id = forms.CharField(max_length=20, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cancel_url = Employee.list_active_employees_url()

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(username = email).exists():
            raise forms.ValidationError("Employee " + email + " already exists.")
        return email

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal'
        helper.label_class = 'col-lg-2'
        helper.field_class = 'col-lg-4'
        helper.layout = Layout(
            'email',
            'first_name',
            'last_name',
            'tax_id',
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(format_html('<a class="btn btn-outline-primary btn-sm" href="{}">Cancel</a>', self.cancel_url)),
            ),
        )
        return helper
    

class EmployeeUpdateForm(forms.Form):
    email = forms.EmailField()
    slug = forms.CharField(max_length=100, required=False, label='URL Slug')
    tax_id = forms.CharField(max_length=20, required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cancel_url = self.initial['employee'].get_absolute_url()

    def clean_email(self):
        email = self.cleaned_data['email']
        if email == self.initial['email']:
            return email
        if Employee.objects.filter(user__username = email).exists():
            raise forms.ValidationError("Employee " + email + " already exists.")
        return email
    
    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if  not slug or slugify(slug).isspace():
            raise forms.ValidationError("Slug cannot be empty.")
        return slug

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal'
        helper.label_class = 'col-lg-2'
        helper.field_class = 'col-lg-4'
        helper.layout = Layout(
            'email',
            'slug',
            'tax_id',
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(format_html('<a class="btn btn-outline-primary btn-sm" href="{}">Cancel</a>', self.cancel_url)),
            ),
        )
        return helper