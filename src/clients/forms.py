from django import forms
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Layout, Submit, HTML
from crispy_forms.bootstrap import FormActions
from dal import autocomplete

from utils.unique_slugify import unique_slugify
from .models import Client, Contract, ContractItem, SalesInvoice
# from employees.models import Employee

from common.mixins import CrispyFormMixin
from dicts.models import Currency, Dimension


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
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(f'<a class="btn btn-outline-primary btn-sm" href="{Client.get_list_url()}">Cancel</a>')
            ),
        )

    def save(self, current_user, commit=True):
        client = super().save(commit=False)
        if not client.pk or client.name != Client.objects.get(pk=client.pk).name:
            client.slug = unique_slugify(Client, client.name)
        if commit:
            client.save(current_user=current_user)
        return client

class ContractForm(CrispyFormMixin, forms.ModelForm):
    class Meta:
        model = Contract
        fields = [ 'number', 'name', 'start_date', 'end_date', 'comments', 'owner']
        widgets = {
            'owner': autocomplete.ModelSelect2(url='employees:employee-autocomplete'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            'number',
            'name',
            'start_date',
            'end_date',
            'comments',
            'owner',
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(f'<a class="btn btn-outline-primary btn-sm" href="{Client.get_list_url()}">Cancel</a>')
            ),
        )
        self.fields['start_date'].widget.input_type = 'date'
        self.fields['end_date'].widget.input_type = 'date'

    def save(self, current_user, commit=True):
        contract = super().save(commit=False)
        contract.client = self.initial.pop('client', None)
        
        if contract.owner and contract.owner.is_inactive:
            # TODO this should be a field validation, not a save instrucion
            raise forms.ValidationError("Cannot assign an inactive employee as the contract owner.")
        if not contract.pk or contract.number != Contract.objects.get(pk=contract.pk).number:
            # TODO move this to a model save method
            contract.slug = unique_slugify(Contract, contract.number)
        if commit:
            contract.save(current_user=current_user)
        return contract
    

class ContractItemForm(CrispyFormMixin, forms.ModelForm):
    dimension_fields = []
    contract = Contract()

    class Meta:
        model = ContractItem
        fields = ['name', 'value', 'currency']

    def __init__(self, *args, **kwargs):
        # Retrieve the instance if editing an existing ContractItem
        instance = kwargs.get('instance', None)
        super().__init__(*args, **kwargs)

        self.contract = self.initial.pop('contract', None)
        dimension_category = {}
        if instance:
            dimension_category = instance.get_dimension_category()

        self.helper.layout = Layout('name', 'value', 'currency',)
        # Get top-level dimensions (dimensions without a parent)
        top_level_dimensions = Dimension.objects.filter(parent__isnull=True)

        # Dynamically create a dropdown for each top-level dimension
        for dimension in top_level_dimensions:
            field_name = dimension.name.lower()
            self.dimension_fields.append(field_name)

            self.fields[field_name] = forms.ChoiceField(
                choices=self.get_indented_category_choices(dimension),
                required=False,
                label=dimension.name,
                widget=forms.Select,
                initial=dimension_category.get(dimension, None)
            )

            # Add the field to the crispy layout
            self.helper.layout.append(field_name)

        # Add form actions (Save and Cancel buttons)
        self.helper.layout.append(
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(f'<a class="btn btn-outline-primary btn-sm" href="{self.contract.get_absolute_url()}">Cancel</a>')
            )
        )

    def get_indented_category_choices(self, parent_dimension):
        """
        Recursively retrieve dimensions in a parent-child sorted order.
        """
        def get_children_sorted(dimension, level=0):
            children = Dimension.objects.filter(parent=dimension).order_by('name')
            result = []
            for child in children:
                element = (child.id, f"{'- ' * (level * 1)}{child.name}")
                result.append(element)
                result.extend(get_children_sorted(child, level + 1))
            return result

        # Initialize the result list
        result = get_children_sorted(parent_dimension)
        return [(None, '---------')] + result  # Add a blank choice at the top

    def save(self, current_user, commit=True):
        # Custom save logic to handle ManyToMany relationship for dimensions
        contract_item = super().save(commit=False)
        contract_item.contract = self.contract
        
        # Save instance first if commit is True
        if commit:
            contract_item.save(current_user=current_user)

        # Clear the existing dimensions and add the selected ones
        contract_item.dimension.clear()
        for field_name in self.dimension_fields:
            selected_dimension_id = self.cleaned_data.get(field_name)
            if selected_dimension_id:
                selected_dimension = Dimension.objects.get(id=selected_dimension_id)
                contract_item.dimension.add(selected_dimension)

        return contract_item

class SalesInvoiceForm(CrispyFormMixin, forms.ModelForm):
    contract = Contract()
    class Meta:
        model = SalesInvoice
        fields = ['number', 'date', 'due_date', 'value', 'currency', 'is_paid', 'paid_date', 'contract_item', 'file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.contract = self.initial.pop('contract', None)

        self.fields['date'].widget.input_type = 'date'
        self.fields['due_date'].widget.input_type = 'date'
        self.fields['paid_date'].widget.input_type = 'date' 
        self.fields['contract_item'].queryset = ContractItem.objects.filter(contract=self.contract)

        self.helper.layout = Layout(
            'number',
            'date',
            'due_date',
            'value',
            'currency',
            'is_paid',
            'paid_date',
            'contract_item',
            'file',
            FormActions(
                Submit('submit', 'Save', css_class='btn btn-primary btn-sm'),
                HTML(f'<a class="btn btn-outline-primary btn-sm" href="{self.contract.get_absolute_url()}">Cancel</a>')
            ),
        )

    #  check if paid_date is set and is a date if 'is_paid' is True
    def clean(self):
        cleaned_data = super().clean()
        is_paid = cleaned_data.get('is_paid')
        paid_date = cleaned_data.get('paid_date')

        if is_paid and not paid_date:
            self.add_error('paid_date', 'Paid date is required if the invoice is marked as paid.')
        if not is_paid and  paid_date:
            cleaned_data['paid_date'] = None

        return cleaned_data

    def save(self, current_user, commit=True):
        invoice = super().save(commit=False)
        # invoice.contract_item = self.initial.pop('contract_item', None)
        if commit:
            invoice.save(current_user=current_user)
        return invoice

class SalesInvoiceSettleForm(CrispyFormMixin, forms.ModelForm):
    class Meta:
        model = SalesInvoice
        fields = [ 'paid_date']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paid_date'].widget.input_type = 'date' 
        self.fields['paid_date'].required = True
        self.helper.layout = Layout('paid_date')
        self.helper.form_tag = False
        self.helper.label_class = 'col-lg-4'
        self.helper.field_class = 'col-lg-6'

    #  check if paid_date is set and is a date if 'is_paid' is True
    def clean(self):
        cleaned_data = super().clean()
        paid_date = cleaned_data.get('paid_date')
        if not paid_date:
            self.add_error('paid_date', 'Paid date is required if the invoice is marked as paid.')
        return cleaned_data

    def save(self, current_user, commit=True):
        invoice = super().save(commit=False)
        invoice.is_paid = True
        # invoice.contract_item = self.initial.pop('contract_item', None)
        if commit:
            invoice.save(current_user=current_user)
        return invoice
