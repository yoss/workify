from django import forms
from django.utils.html import format_html
from .models import Employee, EmployeeGroups, EmployeeDocument, EmployeeDocumentTypes
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, HTML
from crispy_forms.bootstrap import FormActions
from django.utils.text import slugify


class EmployeeBaseForm(forms.Form):
    email = forms.EmailField()
    tax_id = forms.CharField(max_length=20, required=False)
    groups = forms.MultipleChoiceField(choices=EmployeeGroups.choices, widget=forms.CheckboxSelectMultiple, required=False)
    layout = Layout()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    
class EmployeeDocumentForm(forms.Form):
    name = forms.CharField(max_length=100)
    sign_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'))
    document_file = forms.FileField()
    document_type = forms.ChoiceField(choices=EmployeeDocumentTypes.choices)
    reference_document = forms.ModelChoiceField(queryset=EmployeeDocument.objects.none(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reference_document'].queryset = EmployeeDocument.objects.filter(employee=self.initial['employee'])

        self.layout = Layout(
            'name',
            'sign_date',
            'document_file',
            'document_type',
            'reference_document',
            FormActions(
                    Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                    HTML(format_html('<a class="btn btn-outline-primary btn-sm" href="{}">Cancel</a>', self.initial['employee'] .get_absolute_url()))
            ),
        )

    @property
    def helper(self):
        helper = FormHelper()
        helper.form_class = 'form-horizontal'
        helper.label_class = 'col-lg-2'
        helper.field_class = 'col-lg-4'
        helper.layout = self.layout
        return helper
