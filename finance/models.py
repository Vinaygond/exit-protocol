"""
Financial Models for Exit Protocol
Implements forensic accounting and LIBR calculation
"""
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class FinancialAccount(models.Model):
    """
    Represents a financial account (bank, investment, credit card, etc.)
    """
    ACCOUNT_TYPE_CHOICES = [
        ('checking', 'Checking Account'),
        ('savings', 'Savings Account'),
        ('investment', 'Investment Account'),
        ('retirement', 'Retirement Account (401k, IRA)'),
        ('credit_card', 'Credit Card'),
        ('loan', 'Loan Account'),
        ('mortgage', 'Mortgage'),
        ('real_estate', 'Real Estate'),
        ('business', 'Business Account'),
        ('other', 'Other'),
    ]
    
    OWNERSHIP_CHOICES = [
        ('joint', 'Joint'),
        ('petitioner', 'Petitioner Only'),
        ('respondent', 'Respondent Only'),
        ('business', 'Business Entity'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='accounts')
    
    # Account identification
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Last 4 digits only for security'
    )
    institution_name = models.CharField(max_length=255)
    
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    ownership = models.CharField(max_length=20, choices=OWNERSHIP_CHOICES, default='joint')
    
    # Account details
    opening_date = models.DateField(null=True, blank=True)
    closing_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Current balances (cached, recalculated from transactions)
    current_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    last_reconciled_date = models.DateField(null=True, blank=True)
    
    # External integration
    plaid_account_id = models.CharField(max_length=255, blank=True)
    external_data = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'financial_accounts'
        verbose_name = 'Financial Account'
        verbose_name_plural = 'Financial Accounts'
        ordering = ['institution_name', 'account_name']
        indexes = [
            models.Index(fields=['case', '-updated_at']),
            models.Index(fields=['account_type']),
        ]
    
    def __str__(self):
        return f"{self.institution_name} - {self.account_name}"
    
    def get_balance_at_date(self, target_date):
        """Calculate account balance at specific date"""
        transactions = self.transactions.filter(
            transaction_date__lte=target_date
        ).aggregate(total=models.Sum('amount'))
        return transactions['total'] or Decimal('0.00')


class Transaction(models.Model):
    """
    Individual financial transaction
    Core unit for LIBR calculations
    """
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('interest', 'Interest'),
        ('dividend', 'Dividend'),
        ('fee', 'Fee'),
        ('adjustment', 'Adjustment'),
    ]
    
    CATEGORY_CHOICES = [
        ('income_salary', 'Salary/Wages'),
        ('income_business', 'Business Income'),
        ('income_investment', 'Investment Income'),
        ('income_other', 'Other Income'),
        ('expense_housing', 'Housing'),
        ('expense_utilities', 'Utilities'),
        ('expense_food', 'Food/Groceries'),
        ('expense_transportation', 'Transportation'),
        ('expense_healthcare', 'Healthcare'),
        ('expense_childcare', 'Childcare'),
        ('expense_education', 'Education'),
        ('expense_entertainment', 'Entertainment'),
        ('expense_personal', 'Personal'),
        ('expense_business', 'Business Expense'),
        ('expense_legal', 'Legal Fees'),
        ('transfer', 'Transfer'),
        ('uncategorized', 'Uncategorized'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='transactions')
    account = models.ForeignKey(
        FinancialAccount,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Transaction details
    transaction_date = models.DateField(db_index=True)
    post_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date transaction posted to account'
    )
    
    description = models.CharField(max_length=512)
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text='Positive for deposits, negative for withdrawals'
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPE_CHOICES,
        default='withdrawal'
    )
    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='uncategorized'
    )
    
    # Additional details
    memo = models.TextField(blank=True)
    check_number = models.CharField(max_length=20, blank=True)
    
    # LIBR tracking
    is_separate_property = models.BooleanField(
        default=False,
        help_text='Mark as separate property deposit'
    )
    separate_property_claim = models.ForeignKey(
        'SeparatePropertyClaim',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='source_transactions'
    )
    
    # Running balance (calculated)
    running_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Account balance after this transaction'
    )
    
    # External data
    external_id = models.CharField(max_length=255, blank=True, db_index=True)
    external_data = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    imported_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['case', '-transaction_date']),
            models.Index(fields=['account', '-transaction_date']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['category']),
        ]
        unique_together = [['account', 'external_id']]
    
    def __str__(self):
        return f"{self.transaction_date} - {self.description} - ${self.amount}"


class SeparatePropertyClaim(models.Model):
    """
    Tracks separate property claims and LIBR calculations
    This is the core model for forensic tracing
    """
    SOURCE_CHOICES = [
        ('inheritance', 'Inheritance'),
        ('gift', 'Gift'),
        ('premarital', 'Pre-marital Asset'),
        ('personal_injury', 'Personal Injury Settlement'),
        ('trust', 'Trust Distribution'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE, related_name='separate_claims')
    account = models.ForeignKey(
        FinancialAccount,
        on_delete=models.CASCADE,
        related_name='separate_property_claims'
    )
    
    # Claim details
    claim_name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES)
    
    # Initial deposit information
    initial_deposit_date = models.DateField(db_index=True)
    initial_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    # Documentation
    source_documentation = models.ManyToManyField(
        'evidence.EvidenceDocument',
        blank=True,
        related_name='separate_property_claims'
    )
    description = models.TextField(blank=True)
    
    # LIBR calculation results (cached)
    current_traceable_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text='Current amount traceable under LIBR'
    )
    lowest_balance_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when account hit lowest intermediate balance'
    )
    lowest_balance_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Calculation metadata
    last_calculated_at = models.DateTimeField(null=True, blank=True)
    calculation_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending Calculation'),
            ('calculating', 'Calculating'),
            ('complete', 'Complete'),
            ('error', 'Error'),
        ],
        default='pending'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    class Meta:
        db_table = 'separate_property_claims'
        verbose_name = 'Separate Property Claim'
        verbose_name_plural = 'Separate Property Claims'
        ordering = ['-initial_deposit_date']
        indexes = [
            models.Index(fields=['case', '-initial_deposit_date']),
            models.Index(fields=['account', '-initial_deposit_date']),
        ]
    
    def __str__(self):
        return f"{self.claim_name} - ${self.initial_amount}"


class BalanceSnapshot(models.Model):
    """
    Daily snapshots of account composition
    Critical for LIBR tracking and visualization
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case = models.ForeignKey('cases.Case', on_delete=models.CASCADE)
    account = models.ForeignKey(
        FinancialAccount,
        on_delete=models.CASCADE,
        related_name='balance_snapshots'
    )
    
    snapshot_date = models.DateField(db_index=True)
    
    # Balance composition
    total_balance = models.DecimalField(max_digits=15, decimal_places=2)
    separate_property_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    marital_property_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # LIBR tracking
    is_dip_point = models.BooleanField(
        default=False,
        help_text='True if this is a lowest intermediate balance point'
    )
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'balance_snapshots'
        verbose_name = 'Balance Snapshot'
        verbose_name_plural = 'Balance Snapshots'
        unique_together = [['account', 'snapshot_date']]
        ordering = ['-snapshot_date']
        indexes = [
            models.Index(fields=['account', '-snapshot_date']),
            models.Index(fields=['case', '-snapshot_date']),
        ]
    
    def __str__(self):
        return f"{self.account} - {self.snapshot_date} - ${self.total_balance}"