# Sales Decline Investigation: Data Quality vs Genuine Business Loss

A production-grade, reproducible data analytics, engineering, and root cause investigation pipeline built for the B2B E-commerce Sales Challenge.

---

## 1. Executive Business Problem

The Growth and Finance teams reported that revenue declined in **September 2026** compared to **August 2026**. 

Our mandate: Determine through rigorous data engineering, auditing, and SQL analytics whether this decline is:
1. **A genuine business downturn**,
2. **An artifact of data quality defects** (omissions, unparseable dates, bad currencies, duplicates), or
3. **A combination of both.**

---

## 2. Definitive Business Verdict

> ### **FINAL EVALUATION: `GENUINE_BUSINESS_DECLINE`**  
> **Confidence Rating:** `MODERATE` (Acknowledging 2-month dataset limitations and lack of external pipeline logs)  
> Across trusted, clean records, completed monthly revenue declined by **-37.13% (-₹6,71,600.00)**, dropping from **₹18,09,000.00** in August to **₹11,37,400.00** in September.

### Core Supporting Evidence & Findings:
1. **Demand Contraction Across Volume & Value:**
   - Completed orders fell by **-25.66%** (from 113 to 84 orders).
   - Average Order Value (AOV) dropped by **-15.42%** (from ₹16,008.85 to ₹13,540.48).
   - Total units sold decreased by **-18.52%** (135 to 110 units).
   - Active buying customers contracted by **-25.00%** (64 to 48 customers).
2. **Where the Decline Occurred (Product Concentration):**
   - **Laptop 16** (P010 @ ₹72,000) collapsed by **-84.62%** (-₹7,92,000.00; 13 units in August vs. 2 units in September).
   - This single product loss accounts for **117.93%** of the company's net revenue decline.
   - Growth in **Laptop 14** (+₹2,50,000.00 / +125%) and **Printers** (+₹45,000.00 / +50%) was insufficient to offset this loss.
   - *Important Distinction:* This data pinpoints *where* the drop occurred in the product catalog; it does not prove the commercial *why* (e.g. supply shortages, enterprise deal postponement, or competitive pressure), which requires qualitative commercial follow-up.
3. **Where the Decline Occurred (Regional Divergence):**
   - **South** revenue dropped by **-59.50%** (-₹5,78,800.00).
   - **North** revenue dropped by **-74.08%** (-₹4,02,800.00).
   - **West** revenue expanded by **+105.98%** (+₹3,10,000.00), demonstrating localized resilience.
4. **Acquisition Funnel Freeze:**
   - First-time buyer revenue in the window plunged by **-73.72%** (₹6,14,900.00 in August vs. ₹1,61,600.00 in September), indicating a severe freeze in new customer acquisition.
5. **Data Quality Audit & Sensitivity Bounds:**
   - **18 records were quarantined** across both months.
   - **September raw data is not defect-free:** Order `O0036` contains an invalid calendar date (`2026-09-31`, potential value ₹9,000.00).
   - However, hypothetical sensitivity modeling demonstrates that even if `O0036` were added to September, September revenue still declines by **-36.54%**. The decline is robust across all data exclusion permutations.

---

## 3. Project Structure

```text
Data_AI_Challenge_Candidate_Pack 1/
│
├── data/                                 # Raw input data files
│   ├── orders.csv                        # Raw orders (244 rows)
│   ├── customers.csv                     # Customer master (80 rows)
│   └── products.csv                      # Product catalog (12 rows)
│
├── output/                               # Pipeline outputs
│   ├── clean_orders.csv                  # 226 validated, trusted orders
│   ├── rejected_orders.csv               # 18 quarantined orders with documented reasons
│   ├── data_quality_report.csv           # Audit log categorized by defect type
│   ├── executive_summary.md              # Concise 150-250 word executive brief
│   ├── ai_verification.md                # Claim-by-claim verification matrix
│   └── charts/                           # 7 publication-quality charts (300 DPI)
│       ├── 01_revenue_comparison.png
│       ├── 02_orders_comparison.png
│       ├── 03_aov_comparison.png
│       ├── 04_product_revenue_comparison.png
│       ├── 05_region_sales_comparison.png
│       ├── 06_data_quality_issues.png
│       └── 07_revenue_impact_excluded.png
│
├── src/                                  # Modular Python source code
│   ├── data_loader.py                    # Dataset loading & schema inspection
│   ├── data_validator.py                 # Deterministic validation rules & conflict detection
│   ├── data_cleaner.py                   # Data segregation, conversions & reporting
│   ├── sales_analysis.py                 # SQLite SQL queries & KPI calculations
│   ├── root_cause.py                     # Explainable diagnosis engine & sensitivity modeling
│   └── visualizations.py                 # Matplotlib / Seaborn visualization generator
│
├── sql/
│   └── analysis_queries.sql              # Analytical SQLite SQL script
│
├── tests/
│   └── test_pipeline.py                  # Automated unit test suite (8 tests)
│
├── analysis.py                           # Reproducible analysis entry point (Candidate Pack deliverable)
├── queries.sql                           # SQLite script matching hackathon deliverable
├── app.py                                # Dynamic Streamlit executive dashboard
├── main.py                               # One-click end-to-end pipeline runner
├── requirements.txt                      # Project dependencies
└── README.md                             # Comprehensive technical documentation
```

---

## 4. Finance Definitions & Cleaning Rules Applied

All rules strictly adhere to Finance specifications without improvisation:

1. **Revenue Calculation:** `Revenue = quantity * unit_price` for completed orders only. `cancelled` and `refunded` orders are preserved in `clean_orders.csv` but excluded from revenue sums. Refunds are not subtracted.
2. **Currency Conversion:** USD converted to INR at exactly **₹85.0 per USD** (Order `O0055`: 1 unit @ $100 = ₹8,500.00). Unsupported currencies (e.g. `EUR` on Order `O0058`) are quarantined.
3. **Status Standardization:** Surrounding whitespace is trimmed and case-normalized. Raw status `'COMPLETE'` (Order `O0056`) normalizes to `'complete'`, which does **not** equate to `'completed'` and is quarantined. Status `' Completed '` (Order `O0057`) normalizes to `'completed'` and is accepted.
4. **Duplicate vs Conflicting Rows:**
   - **Identical Repeated Rows:** Deduplicated safely by keeping the primary record and logging the duplicate (Orders `O0008`, `O0030`, `O0081`).
   - **Conflicting Rows:** Order ID `O0089` contained conflicting unit prices (₹4,400 vs ₹2,200). Both rows were quarantined to prevent arbitrary selection.
5. **Foreign Key Integrity:** Customer IDs (`C999`, `C998`) and product IDs (`P998`, `P999`) not present in master tables were quarantined.
6. **Value Constraints:** Non-positive quantities (`O0059`: qty=0, `O0053`: qty=-1) and prices (`O0054`: price=0) were rejected.
7. **Date Validation:** Unparseable dates (`O0037`: `'not-a-date'`) and invalid calendar dates (`O0036`: `'2026-09-31'`) were rejected.
8. **New vs. Repeat Definition:** Defined by a customer's first completed order in the available August–September dataset window. Same-day first orders count as new; later dates are repeat.

---

## 5. Execution Instructions

### A. Environment Setup
Install required dependencies:
```bash
pip install -r requirements.txt
```

### B. Run Automated Unit Tests
Execute the automated test suite covering revenue math, currency conversions, duplicate handling, date parsing, FK checks, and diagnosis logic:
```bash
python -m unittest discover -s tests -v
```

### C. Run Full Analysis Pipeline
To execute the complete end-to-end audit, execute SQL queries, generate all charts, and produce the markdown reports:
```bash
python main.py
# or:
python analysis.py
```

### D. Launch Interactive Streamlit Dashboard
To launch the interactive executive dashboard:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 6. Analytical Summary Table

| Metric | August 2026 | September 2026 | Absolute Change | Percentage Change |
|---|---|---|---|---|
| **Completed Revenue (INR)** | **₹18,09,000.00** | **₹11,37,400.00** | **-₹6,71,600.00** | **-37.13%** |
| **Completed Orders** | 113 | 84 | -29 orders | -25.66% |
| **Average Order Value (AOV)** | ₹16,008.85 | ₹13,540.48 | -₹2,468.37 | -15.42% |
| **Total Units Sold** | 135 | 110 | -25 units | -18.52% |
| **Active Customers** | 64 | 48 | -16 customers | -25.00% |
| **New Customer Revenue** | ₹6,14,900.00 | ₹1,61,600.00 | -₹4,53,300.00 | -73.72% |
| **Repeat Customer Revenue** | ₹11,94,100.00 | ₹9,75,800.00 | -₹2,18,300.00 | -18.28% |

---

## 7. Sensitivity Analysis (Hypothetical Exploratory Bounds)

*Note: Quarantined records with fatal defects (e.g. zero prices, invalid keys) cannot be treated as actual revenue. Scenarios below represent exploratory sensitivity bounds.*

| Scenario | August Revenue | September Revenue | Decline (INR) | Decline (%) | Verdict Stability |
|---|---|---|---|---|---|
| **Scenario 1: Trusted Records Only (Baseline)** | ₹18,09,000.00 | ₹11,37,400.00 | -₹6,71,600.00 | **-37.13%** | Robust |
| **Scenario 2: Hypothetical Max September (+ O0036/Ambiguous)** | ₹18,09,000.00 | ₹11,48,000.00 | -₹6,61,000.00 | **-36.54%** | Robust |
| **Scenario 3: Hypothetical Max August (+ Aug Quarantined)** | ₹18,72,800.00 | ₹11,37,400.00 | -₹7,35,400.00 | **-39.27%** | Robust |

**Conclusion:** The sales decline remains severe (>36.5%) across all hypothetical interpretations of excluded data.

---

## 8. Limitations & Recommended Business Actions

- **Distinction Between Trusted Data and Complete Data:** While trusted records prove a sales decline, this does not prove that the original export was exhaustive or that unrecorded orders did not occur outside the system.
- **Tenure Limitation:** Customer tenure is measured only within the Aug–Sept 2026 window; true historical CRM tenure before August 1, 2026 is unobserved.
- **Where vs. Why:** Product/region trends show where sales dropped, but commercial causes (e.g. competitor pricing or supply shortages) require qualitative business investigation.
- **Immediate Recommended Business Action:**
  1. Convene a cross-functional review with the North and South regional sales teams to investigate the **Laptop 16** enterprise pipeline.
  2. Audit marketing channels and top-of-funnel conversion in September to address the 73.72% decline in new customer revenue.
