# 🛡️ Exit Protocol

_Forensic Asset Tracing & Communication Defense for High-Stakes Litigation._

Exit Protocol is a secure **System of Record** designed to protect high-net-worth individuals during complex separation proceedings. It automates the expensive, manual work typically performed by forensic accountants and paralegals.

---

## The Value Proposition

### Problem
In a divorce, “Separate Property” (e.g., inheritance) is often lost because it becomes mixed with marital funds.  
Proving what is yours requires complex math — work lawyers charge **thousands of dollars** to perform.

### The Solution
Exit Protocol automates forensic tracing using the **Lowest Intermediate Balance Rule (LIBR)** — the legal standard for asset tracing.

### The ROI
A user pays **$99** to save **$5,000+** in legal fees and potentially protect **$100,000+** in assets.

---

## 🚀 Core Features (Fully Functional)

### 1. Secure Evidence Locker
- **Chain of Custody:** Every upload is cryptographically hashed (SHA-256).  
- **Audit Trail:** Tracks every view, download, and modification.  
- **Result:** Proof that evidence has not been tampered with.

---

### 2. Financial Intelligence Engine
- **PDF Statement Parser:** Drag-and-drop a PDF bank statement to automatically extract dates, descriptions, and amounts using a dual-strategy OCR/Regex engine.  
- **CSV Support:** Handles large datasets with bulk imports.

---

### 3. ⚖️ LIBR Forensic Calculator
- **The Algorithm:** Automatically replays account history day-by-day.  
- **The Logic:** Detects if the account balance ever dipped below the claimed separate property amount.  
- **The Visualization:** Renders a **Chart.js** timeline showing where and when commingling occurred.

---

### 4. Court-Admissible Reporting
- **One-Click PDF:** Generates a polished “Exhibit A” document.  
- **Executive Summary:** Shows the initial claim vs. the legally traceable remainder.  
- **Transaction Ledger:** Appends the full historical ledger for judges and opposing counsel.

---

### 5. Secure Communications (AI Powered)
- **The Threat:** High-conflict ex-partners send emotional, baiting messages.  
- **The Shield:** An AI engine (BIFF Model) rewrites hostile texts into responses that are **Brief, Informative, Friendly, and Firm**.

---

## 🛠️ Technical Stack

- **Backend:** Python / Django 5.0  
- **Database:** SQLite (Dev) / PostgreSQL (Production)  
- **Frontend:** Bootstrap 5 + Tailwind Utilities + Chart.js  
- **PDF Processing:** pdfplumber (Extraction) + xhtml2pdf (Generation)  
- **Security:** Django middleware (case isolation) + SHA-256 hashing  

---

## 🏁 Quick Start (Local Dev)

### Install Dependencies
```bash
pip install -r requirements.txt
````

### Initialize Database
```bash
python manage.py migrate
```

### Run the Server
```bash
python manage.py runserver
```

Access the App

URL: http://127.0.0.1:8000

Navigate to: Login -> Dashboard -> "Initialize Case"
