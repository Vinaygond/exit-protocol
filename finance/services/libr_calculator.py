from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Sum
import logging

from finance.models import (
    FinancialAccount, 
    Transaction, 
    SeparatePropertyClaim, 
    BalanceSnapshot
)

logger = logging.getLogger(__name__)

class LIBRCalculator:
    """
    Calculate separate property traceability using LIBR.
    """
    
    def __init__(self, account: FinancialAccount):
        self.account = account
        self.case = account.case
    
    def calculate_all_claims(self):
        claims = SeparatePropertyClaim.objects.filter(account=self.account).order_by('initial_deposit_date')
        results = []
        for claim in claims:
            result = self.calculate_claim(claim)
            results.append(result)
        return results
    
    @transaction.atomic
    def calculate_claim(self, claim: SeparatePropertyClaim):
        claim.calculation_status = 'calculating'
        claim.save(update_fields=['calculation_status'])
        
        try:
            transactions = Transaction.objects.filter(
                account=self.account,
                transaction_date__gte=claim.initial_deposit_date
            ).order_by('transaction_date', 'created_at')
            
            result = self._trace_separate_property(
                claim.initial_amount,
                claim.initial_deposit_date,
                transactions
            )
            
            claim.current_traceable_amount = result['current_traceable']
            claim.lowest_balance_amount = result['lowest_balance']
            claim.lowest_balance_date = result['lowest_balance_date']
            claim.calculation_status = 'complete'
            claim.last_calculated_at = datetime.now()
            claim.save()
            
            self._create_balance_snapshots(result['daily_balances'])
            logger.info(f"LIBR Complete: Claim {claim.id} reduced to ${claim.current_traceable_amount}")
            return result
            
        except Exception as e:
            claim.calculation_status = 'error'
            claim.save(update_fields=['calculation_status'])
            logger.error(f"LIBR Failed for Claim {claim.id}: {str(e)}")
            return None

    def _trace_separate_property(self, initial_amount, start_date, transactions):
        balance_start_of_day = self.account.get_balance_at_date(start_date - timedelta(days=1))
        running_total = balance_start_of_day
        current_claim_limit = initial_amount 
        lowest_balance = initial_amount
        lowest_balance_date = start_date
        
        dip_events = []
        daily_balances = {}
        current_date = start_date
        
        for txn in transactions:
            while current_date < txn.transaction_date:
                daily_balances[current_date] = {
                    'total': running_total,
                    'separate': min(current_claim_limit, running_total),
                    'marital': max(Decimal(0), running_total - min(current_claim_limit, running_total)),
                    'is_dip': False
                }
                current_date += timedelta(days=1)

            running_total += txn.amount
            is_dip = False
            
            if running_total < current_claim_limit:
                current_claim_limit = running_total
                lowest_balance = current_claim_limit
                lowest_balance_date = txn.transaction_date
                is_dip = True
                
                dip_events.append({
                    'date': txn.transaction_date,
                    'balance': current_claim_limit,
                    'transaction_desc': txn.description
                })

            txn.running_balance = running_total
            txn.save(update_fields=['running_balance'])
            
            daily_balances[txn.transaction_date] = {
                'total': running_total,
                'separate': max(Decimal(0), current_claim_limit),
                'marital': max(Decimal(0), running_total - max(Decimal(0), current_claim_limit)),
                'is_dip': is_dip
            }

        final_traceable = max(current_claim_limit, Decimal('0.00'))
        
        return {
            'current_traceable': final_traceable,
            'lowest_balance': lowest_balance,
            'lowest_balance_date': lowest_balance_date,
            'dip_events': dip_events,
            'daily_balances': daily_balances
        }

    def _create_balance_snapshots(self, daily_balances):
        snapshots = []
        for date, balances in daily_balances.items():
            snapshot = BalanceSnapshot(
                case=self.case,
                account=self.account,
                snapshot_date=date,
                total_balance=balances['total'],
                separate_property_balance=balances['separate'],
                marital_property_balance=balances['marital'],
                is_dip_point=balances['is_dip']
            )
            snapshots.append(snapshot)
        
        BalanceSnapshot.objects.bulk_create(
            snapshots,
            update_conflicts=True,
            update_fields=['total_balance', 'separate_property_balance', 'marital_property_balance', 'is_dip_point'],
            unique_fields=['account', 'snapshot_date']
        )

    def get_balance_at_date(self, target_date):
        snapshot = BalanceSnapshot.objects.filter(account=self.account, snapshot_date=target_date).first()
        if snapshot: return snapshot.total_balance
        return Decimal('0.00')


class LIBRReportGenerator:
    """
    Generates text summaries for the UI based on LIBR results.
    ROBUST: Handles NoneTypes to prevent crashes if calc hasn't run.
    """
    def __init__(self, claim: SeparatePropertyClaim):
        self.claim = claim
        self.account = claim.account
    
    def generate_summary_report(self):
        # Safety Check: Default to 0.00 if values are None
        lowest_bal = self.claim.lowest_balance_amount or Decimal('0.00')
        lowest_date = self.claim.lowest_balance_date
        
        return {
            'claim_name': self.claim.claim_name,
            'account_name': self.account.account_name,
            'initial_deposit': {
                'date': self.claim.initial_deposit_date,
                'amount': self.claim.initial_amount,
                'source': self.claim.get_source_type_display()
            },
            'current_status': {
                'traceable_amount': self.claim.current_traceable_amount,
                'percentage_retained': self._calculate_retention_percentage(),
                'lowest_balance': lowest_bal,
                'lowest_balance_date': lowest_date
            },
            'analysis': self._generate_narrative_analysis()
        }
    
    def _calculate_retention_percentage(self):
        if self.claim.initial_amount == 0: return Decimal('0.00')
        return (self.claim.current_traceable_amount / self.claim.initial_amount * 100).quantize(Decimal('0.01'))
    
    def _generate_narrative_analysis(self):
        # Handle "Pending" state
        if self.claim.calculation_status != 'complete':
            return "Analysis pending. Please wait for the LIBR calculation to complete."

        pct = self._calculate_retention_percentage()
        initial = self.claim.initial_amount
        current = self.claim.current_traceable_amount
        
        # Safe access to lowest balance
        lowest_bal = self.claim.lowest_balance_amount or Decimal('0.00')
        lowest_date_str = str(self.claim.lowest_balance_date) if self.claim.lowest_balance_date else "unknown date"
        
        if pct == 100:
            return f"Success: The entire ${initial:,.2f} remains traceable. The account never dipped below this amount."
        elif pct > 0:
            return f"Partial Trace: ${current:,.2f} ({pct}%) remains. The account dipped to ${lowest_bal:,.2f} on {lowest_date_str}."
        else:
            return f"Trace Failed: The separate property was fully commingled. Account hit ${lowest_bal:,.2f} on {lowest_date_str}."