from django import forms
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Layout, Submit, HTML
from crispy_forms.bootstrap import FormActions

from utils.unique_slugify import unique_slugify
from .models import Client   


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'logo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-4'
        self.helper.layout = Layout(
            'name',
            'logo',
            # 'is_active',
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(f'<a class="btn btn-outline-primary btn-sm" href="{Client.get_list_url()}">Cancel</a>')
            ),
        )

    def save(self, commit=True):
        client = super().save(commit=False)
        if not client.pk or client.name != Client.objects.get(pk=client.pk).name:
            client.slug = unique_slugify(Client, client.name)
        if commit:
            client.save()
        return client

