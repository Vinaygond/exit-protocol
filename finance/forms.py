"""
Forms for Financial Management
"""
from django import forms
from finance.models import FinancialAccount, Transaction, SeparatePropertyClaim


class FinancialAccountForm(forms.ModelForm):
    """Form for creating/editing financial accounts"""
    
    class Meta:
        model = FinancialAccount
        fields = [
            'account_name', 'account_number', 'institution_name',
            'account_type', 'ownership', 'opening_date', 'closing_date'
        ]
        widgets = {
            'account_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Joint Checking'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last 4 digits only'
            }),
            'institution_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Chase Bank'
            }),
            'account_type': forms.Select(attrs={'class': 'form-select'}),
            'ownership': forms.Select(attrs={'class': 'form-select'}),
            'opening_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'closing_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'account_name': 'Account Name',
            'account_number': 'Account Number',
            'institution_name': 'Financial Institution',
            'account_type': 'Account Type',
            'ownership': 'Ownership',
            'opening_date': 'Opening Date',
            'closing_date': 'Closing Date (if applicable)',
        }
        help_texts = {
            'account_number': 'For security, only enter last 4 digits',
            'ownership': 'Who legally owns this account',
        }


class TransactionForm(forms.ModelForm):
    """Form for creating transactions"""
    
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account', None)
        super().__init__(*args, **kwargs)
    
    class Meta:
        model = Transaction
        fields = [
            'transaction_date', 'description', 'amount', 
            'transaction_type', 'category', 'memo', 'check_number'
        ]
        widgets = {
            'transaction_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Mortgage payment'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'transaction_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'memo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes...'
            }),
            'check_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Optional'
            }),
        }
        labels = {
            'transaction_date': 'Transaction Date',
            'description': 'Description',
            'amount': 'Amount ($)',
            'transaction_type': 'Type',
            'category': 'Category',
            'memo': 'Memo',
            'check_number': 'Check Number',
        }
        help_texts = {
            'amount': 'Use positive values for deposits, negative for withdrawals',
        }


class SeparatePropertyClaimForm(forms.ModelForm):
    """Form for creating separate property claims"""
    
    class Meta:
        model = SeparatePropertyClaim
        fields = [
            'claim_name', 'source_type', 'initial_deposit_date',
            'initial_amount', 'description'
        ]
        widgets = {
            'claim_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Inheritance from Grandmother'
            }),
            'source_type': forms.Select(attrs={'class': 'form-select'}),
            'initial_deposit_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'initial_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the source of these funds...'
            }),
        }
        labels = {
            'claim_name': 'Claim Name',
            'source_type': 'Source Type',
            'initial_deposit_date': 'Deposit Date',
            'initial_amount': 'Amount ($)',
            'description': 'Description',
        }
        help_texts = {
            'initial_amount': 'Enter the amount of separate property deposited',
            'source_type': 'Select the legal source of the separate property funds',
            'initial_deposit_date': 'When these funds were deposited into the account',
        }


class TransactionImportForm(forms.Form):
    """Form for importing transactions from CSV"""
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with columns: date, description, amount',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv'
        })
    )
    
    date_format = forms.ChoiceField(
        choices=[
            ('%Y-%m-%d', 'YYYY-MM-DD (2024-01-31)'),
            ('%m/%d/%Y', 'MM/DD/YYYY (01/31/2024)'),
            ('%d/%m/%Y', 'DD/MM/YYYY (31/01/2024)'),
        ],
        initial='%Y-%m-%d',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Select the date format used in your CSV file'
    )


    

class BulkTransactionForm(forms.Form):
    """Form for bulk editing transactions"""
    transactions = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    action = forms.ChoiceField(
        choices=[
            ('categorize', 'Change Category'),
            ('delete', 'Delete Selected'),
        ],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    category = forms.ChoiceField(
        choices=Transaction.CATEGORY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='New category for selected transactions'
    )
    
    def __init__(self, *args, **kwargs):
        account = kwargs.pop('account', None)
        super().__init__(*args, **kwargs)
        
        if account:
            self.fields['transactions'].queryset = account.transactions.all()    