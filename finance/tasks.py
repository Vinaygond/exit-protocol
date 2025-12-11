from .models import SeparatePropertyClaim, FinancialAccount, Transaction
from .services.libr_calculator import LIBRCalculator
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SynchronousTask:
    """
    A helper to run tasks immediately in the main thread.
    This replaces Celery for the prototype phase so logic runs instantly.
    """
    def __init__(self, task_func):
        self.task_func = task_func

    def delay(self, *args, **kwargs):
        """
        Mimics Celery's .delay() but runs code instantly.
        """
        try:
            return self.task_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Task Failed: {e}")
            print(f"!!! TASK ERROR: {e}")

# --- ACTUAL TASK LOGIC FUNCTIONS ---

def run_libr_single_claim(claim_id):
    """
    Finds the claim and runs the LIBR Calculator on it.
    """
    print(f"[Task] Starting LIBR Calculation for Claim ID: {claim_id}")
    try:
        claim = SeparatePropertyClaim.objects.get(id=claim_id)
        calculator = LIBRCalculator(claim.account)
        result = calculator.calculate_claim(claim)
        
        if result:
            print(f"[Task] LIBR Success. Traceable Amount: ${result['current_traceable']}")
        else:
            print("[Task] LIBR calculation returned None (Check logs for errors)")
            
    except SeparatePropertyClaim.DoesNotExist:
        print(f"[Task] Error: Claim {claim_id} not found.")
    except Exception as e:
        print(f"[Task] Critical LIBR Error: {e}")

def run_bulk_import(account_id, transactions_data):
    """
    Imports a list of transactions into an account.
    """
    print(f"[Task] Starting Bulk Import for Account: {account_id}")
    try:
        account = FinancialAccount.objects.get(id=account_id)
        count = 0
        
        for data in transactions_data:
            # Parse date if string
            if isinstance(data.get('transaction_date'), str):
                 try:
                     data['transaction_date'] = datetime.strptime(data['transaction_date'], '%Y-%m-%d').date()
                 except:
                     pass

            Transaction.objects.create(
                case=account.case,
                account=account,
                transaction_date=data['transaction_date'],
                description=data['description'],
                amount=data['amount'],
                category=data.get('category', 'uncategorized'),
                transaction_type=data.get('transaction_type', 'withdrawal')
            )
            count += 1
        print(f"[Task] Imported {count} transactions.")
        
        # Trigger LIBR recalculation for this account after import
        run_libr_account_recalc(account_id)
        
    except Exception as e:
        print(f"[Task] Import Error: {e}")

def run_libr_account_recalc(account_id):
    """
    Recalculates ALL claims for an account (e.g. after new transactions added).
    """
    try:
        account = FinancialAccount.objects.get(id=account_id)
        calculator = LIBRCalculator(account)
        calculator.calculate_all_claims()
        print(f"[Task] Recalculated all claims for Account {account.account_name}")
    except Exception as e:
        print(f"[Task] Account Recalc Error: {e}")

def run_ocr_placeholder(document_id):
    print(f"[Task] OCR Processing simulated for Doc: {document_id}")
    # In a real app, this would call AWS Textract or Google Document AI


# --- EXPORTED TASKS (These link the functions to the Views) ---

# This maps the function `run_libr_single_claim` to the variable `recalculate_single_claim`
# So when views call `recalculate_single_claim.delay(id)`, it runs our wrapper.

recalculate_single_claim = SynchronousTask(run_libr_single_claim)
bulk_import_transactions = SynchronousTask(run_bulk_import)
recalculate_libr_for_account = SynchronousTask(run_libr_account_recalc)
process_evidence_ocr = SynchronousTask(run_ocr_placeholder)