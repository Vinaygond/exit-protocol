import pdfplumber
import re
from decimal import Decimal
from datetime import datetime

class StatementParser:
    def __init__(self, evidence_document):
        self.document = evidence_document
        self.file_path = evidence_document.document.path

    def parse(self):
        """
        Main entry point. 
        Tries multiple strategies to extract transaction data from PDF.
        """
        extracted_data = []
        print(f"[Parser] Scanning file: {self.file_path}")
        
        try:
            with pdfplumber.open(self.file_path) as pdf:
                # --- STRATEGY 1: Standard Table Extraction ---
                print("[Parser] Attempting Strategy 1: Table Extraction")
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            clean_row = [str(cell).strip() if cell else "" for cell in row]
                            txn = self._normalize_row(clean_row)
                            if txn:
                                extracted_data.append(txn)

                # --- STRATEGY 2: Text Line Scanning (Fallback) ---
                if len(extracted_data) == 0:
                    print("[Parser] Strategy 1 yielded 0 rows. Attempting Strategy 2: Text Scanning")
                    full_text = ""
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text += text + "\n"
                    
                    # Split lines and parse
                    for line in full_text.split('\n'):
                        if not line.strip(): continue
                        txn = self._parse_flexible_line(line)
                        if txn:
                            extracted_data.append(txn)
                                    
        except Exception as e:
            print(f"[Parser] Critical Error: {e}")
            
        print(f"[Parser] Extraction complete. Found {len(extracted_data)} transactions.")
        return extracted_data

    def _normalize_row(self, row):
        """Strategy 1 Helper: Convert Table Row to Dict"""
        if not row or len(row) < 2: return None
        
        # 1. Detect Date (Column 0)
        raw_date = row[0]
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)', raw_date)
        if not date_match: return None
        
        # 2. Detect Amount (Last non-empty column usually)
        raw_amount = next((x for x in reversed(row) if x and self._is_money(x)), None)
        if not raw_amount: return None

        # 3. Description is everything else
        description = " ".join([c for c in row if c != raw_date and c != raw_amount])
        if not description.strip(): description = "Transaction"

        return self._build_transaction(date_match.group(1), description, raw_amount)

    def _parse_flexible_line(self, line):
        """
        Strategy 2 Helper: Parses raw text lines (including CSV-style quotes).
        """
        # Clean the line: Remove quotes, backslashes, and extra spaces
        clean_line = line.replace('"', '').replace("'", "").replace('\\', '').strip()
        
        # Regex: Date ... Amount
        pattern = r'(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?).*?(-?\$?[\d,]+\.\d{2})'
        match = re.search(pattern, clean_line)
        
        if match:
            date_str = match.group(1)
            amount_str = match.group(2)
            
            # Extract Description
            start_idx = clean_line.find(date_str) + len(date_str)
            end_idx = clean_line.rfind(amount_str)
            description = clean_line[start_idx:end_idx].strip(', ').strip()
            
            if not description: description = "Transaction"

            return self._build_transaction(date_str, description, amount_str)
        
        return None

    def _is_money(self, text):
        return re.search(r'\d+\.\d{2}', text) is not None

    def _build_transaction(self, date_str, desc, amount_str):
        """Final type conversion"""
        try:
            # Clean Amount
            clean_amount = amount_str.replace('$', '').replace(',', '').replace('"', '').replace(' ', '')
            amount = Decimal(clean_amount)
            
            # Handle Negatives
            if '(' in amount_str or '-' in amount_str:
                amount = -abs(amount)

            # Parse Date
            current_year = datetime.now().year
            date_str = date_str.replace('-', '/')
            parts = date_str.split('/')
            
            if len(parts) == 3:
                year = parts[2]
                if len(year) == 2: year = f"20{year}"
                parsed_date = datetime.strptime(f"{parts[0]}/{parts[1]}/{year}", "%m/%d/%Y").date()
            else:
                parsed_date = datetime.strptime(f"{parts[0]}/{parts[1]}/{current_year}", "%m/%d/%Y").date()

            return {
                'transaction_date': parsed_date,
                'description': desc[:255],
                'amount': amount,
                'category': 'uncategorized',
                'memo': 'Extracted from PDF'
            }
        except Exception as e:
            return None