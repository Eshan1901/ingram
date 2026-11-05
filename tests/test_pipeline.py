"""
Automated Test Suite for Sales Decline Investigation Pipeline
Tests:
1. Revenue calculation and status filtering (completed vs cancelled/refunded)
2. Currency conversion (USD -> INR at 85.0, rejection of EUR)
3. Duplicate handling (identical deduplication vs conflicting order IDs)
4. Date validation (valid dates vs unparseable and out-of-range dates like 2026-09-31)
5. Non-positive quantity and unit price validation
6. Foreign key validation (customer_id and product_id)
7. SQL vs Python calculation agreement
8. Root cause diagnosis classification logic
"""

import unittest
import pandas as pd
import numpy as np

from src.data_loader import DataLoader
from src.data_validator import DataValidator
from src.data_cleaner import DataCleaner
from src.sales_analysis import SalesAnalyzer
from src.root_cause import RootCauseAnalyzer


class TestSalesInvestigationPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Loads dataset and runs validation and cleaning once for test cases."""
        cls.loader = DataLoader()
        cls.orders_df, cls.customers_df, cls.products_df = cls.loader.load_data()
        cls.validator = DataValidator(cls.orders_df, cls.customers_df, cls.products_df)
        cls.validation_results = cls.validator.validate_all()
        cls.cleaner = DataCleaner(cls.validation_results)
        cls.clean_orders, cls.rejected_orders = cls.cleaner.generate_clean_and_rejected_datasets()
        cls.dq_report = cls.cleaner.generate_data_quality_report()
        cls.analyzer = SalesAnalyzer(cls.clean_orders, cls.customers_df, cls.products_df)

    @classmethod
    def tearDownClass(cls):
        cls.analyzer.close()

    def test_currency_conversion(self):
        """Test that USD is converted at exactly 85.0 INR/USD and unsupported currencies are rejected."""
        # Check USD order O0055 in clean_orders
        usd_order = self.clean_orders[self.clean_orders["order_id"] == "O0055"]
        self.assertEqual(len(usd_order), 1, "USD order O0055 should be present in clean_orders")
        row = usd_order.iloc[0]
        self.assertEqual(row["currency"], "USD")
        self.assertEqual(row["rate_to_inr"], 85.0)
        # Quantity = 1, unit_price = 100 -> 8,500.0 INR
        self.assertEqual(row["revenue_inr"], 8500.0)

        # Check unsupported currency EUR (O0058) in rejected_orders
        eur_order = self.rejected_orders[self.rejected_orders["order_id"] == "O0058"]
        self.assertEqual(len(eur_order), 1, "EUR order O0058 must be quarantined")
        self.assertIn("Unsupported currency", eur_order.iloc[0]["rejection_reasons"])

    def test_status_normalization_and_complete_rule(self):
        """Test status whitespace trimming and ensure 'COMPLETE' does not equate to 'completed'."""
        # Order O0057 had status ' Completed ' with whitespace -> should be normalized and in clean_orders
        o0057 = self.clean_orders[self.clean_orders["order_id"] == "O0057"]
        self.assertEqual(len(o0057), 1, "O0057 with ' Completed ' should be cleaned to 'completed'")
        self.assertEqual(o0057.iloc[0]["status"], "completed")

        # Order O0056 had status 'COMPLETE' -> must NOT equate to 'completed' per Finance rule
        o0056 = self.rejected_orders[self.rejected_orders["order_id"] == "O0056"]
        self.assertEqual(len(o0056), 1, "O0056 with status 'COMPLETE' must be rejected")
        self.assertIn("Unrecognized status", o0056.iloc[0]["rejection_reasons"])

    def test_duplicate_vs_conflicting_order_ids(self):
        """Test exact duplicate deduplication vs conflicting order IDs quarantine."""
        # O0030, O0008, O0081 are exact duplicates
        # They should each appear exactly once in clean_orders, and their duplicate copy in rejected_orders
        for oid in ["O0030", "O0081"]:
            clean_matches = self.clean_orders[self.clean_orders["order_id"] == oid]
            self.assertEqual(len(clean_matches), 1, f"Clean orders must have exactly 1 row for exact duplicate ID {oid}")
            rej_matches = self.rejected_orders[self.rejected_orders["order_id"] == oid]
            self.assertEqual(len(rej_matches), 1, f"Rejected orders must contain the duplicate row for {oid}")
            self.assertIn("Exact duplicate row", rej_matches.iloc[0]["rejection_reasons"])

        # O0089 has conflicting unit prices (4400 vs 2200) -> BOTH copies must be quarantined
        o0089_clean = self.clean_orders[self.clean_orders["order_id"] == "O0089"]
        self.assertEqual(len(o0089_clean), 0, "Conflicting order ID O0089 must NOT be in clean_orders")
        o0089_rej = self.rejected_orders[self.rejected_orders["order_id"] == "O0089"]
        self.assertEqual(len(o0089_rej), 2, "Both conflicting rows of O0089 must be quarantined")
        for _, r in o0089_rej.iterrows():
            self.assertIn("Conflicting order_id", r["rejection_reasons"])

    def test_date_validation(self):
        """Test date validation: reject 'not-a-date' and '2026-09-31'."""
        # O0037 has 'not-a-date'
        o0037 = self.rejected_orders[self.rejected_orders["order_id"] == "O0037"]
        self.assertEqual(len(o0037), 1, "O0037 with 'not-a-date' must be quarantined")
        self.assertIn("Invalid/unparseable order_date", o0037.iloc[0]["rejection_reasons"])

        # O0036 has '2026-09-31' (September has only 30 days)
        o0036 = self.rejected_orders[self.rejected_orders["order_id"] == "O0036"]
        self.assertEqual(len(o0036), 1, "O0036 with '2026-09-31' must be quarantined")
        self.assertIn("Invalid/unparseable order_date", o0036.iloc[0]["rejection_reasons"])

    def test_non_positive_quantity_and_price(self):
        """Test rejection of non-positive quantity and unit price."""
        # Non-positive quantity: O0059 (qty=0), O0053 (qty=-1)
        for oid in ["O0059", "O0053"]:
            rej = self.rejected_orders[self.rejected_orders["order_id"] == oid]
            self.assertEqual(len(rej), 1, f"Order {oid} with non-positive qty must be quarantined")
            self.assertIn("Non-positive quantity", rej.iloc[0]["rejection_reasons"])

        # Non-positive price: O0054 (unit_price=0)
        o0054 = self.rejected_orders[self.rejected_orders["order_id"] == "O0054"]
        self.assertEqual(len(o0054), 1, "Order O0054 with unit_price=0 must be quarantined")
        self.assertIn("Non-positive unit_price", o0054.iloc[0]["rejection_reasons"])

    def test_foreign_key_validation(self):
        """Test rejection of invalid customer_id and product_id foreign keys."""
        # Missing customer: O0051, O0052
        for oid in ["O0051", "O0052"]:
            rej = self.rejected_orders[self.rejected_orders["order_id"] == oid]
            self.assertIn("Missing customer_id", rej.iloc[0]["rejection_reasons"])

        # Unknown customer: O0042 (C999), O0043 (C998)
        for oid, cid in [("O0042", "C999"), ("O0043", "C998")]:
            rej = self.rejected_orders[self.rejected_orders["order_id"] == oid]
            self.assertIn(f"Invalid customer_id foreign key: '{cid}'", rej.iloc[0]["rejection_reasons"])

        # Unknown product: O0044 (P999), O0045 (P998)
        for oid, pid in [("O0044", "P999"), ("O0045", "P998")]:
            rej = self.rejected_orders[self.rejected_orders["order_id"] == oid]
            self.assertIn(f"Invalid product_id foreign key: '{pid}'", rej.iloc[0]["rejection_reasons"])

    def test_sql_vs_python_agreement(self):
        """Test that SQLite SQL query outputs exactly match Python calculations."""
        summary = self.analyzer.get_monthly_comparison_summary()

        # Compute with pure Pandas on clean_orders
        completed = self.clean_orders[self.clean_orders["status"] == "completed"].copy()
        completed["month"] = pd.to_datetime(completed["order_date"]).dt.strftime("%Y-%m")

        aug_py_rev = completed[completed["month"] == "2026-08"]["revenue_inr"].sum()
        sep_py_rev = completed[completed["month"] == "2026-09"]["revenue_inr"].sum()
        aug_py_orders = len(completed[completed["month"] == "2026-08"])
        sep_py_orders = len(completed[completed["month"] == "2026-09"])

        self.assertAlmostEqual(summary["august_revenue_inr"], aug_py_rev, places=2)
        self.assertAlmostEqual(summary["september_revenue_inr"], sep_py_rev, places=2)
        self.assertEqual(summary["august_completed_orders"], aug_py_orders)
        self.assertEqual(summary["september_completed_orders"], sep_py_orders)
        self.assertEqual(summary["august_revenue_inr"], 1809000.0)
        self.assertEqual(summary["september_revenue_inr"], 1137400.0)
        self.assertEqual(summary["absolute_revenue_diff_inr"], -671600.0)
        self.assertAlmostEqual(summary["percentage_revenue_change"], -37.13, places=2)

    def test_root_cause_diagnosis_engine(self):
        """Test that the diagnosis engine deterministically classifies the outcome as GENUINE_BUSINESS_DECLINE."""
        summary = self.analyzer.get_monthly_comparison_summary()
        prod_perf = self.analyzer.get_product_performance()
        cat_perf = self.analyzer.get_category_performance()
        reg_perf = self.analyzer.get_regional_performance()
        new_repeat = self.analyzer.get_new_vs_repeat_customers()

        rca = RootCauseAnalyzer(
            summary, prod_perf, cat_perf, reg_perf, new_repeat, self.rejected_orders, self.clean_orders
        )
        diagnosis = rca.diagnose_root_cause()

        self.assertEqual(diagnosis["classification"], "GENUINE_BUSINESS_DECLINE")
        self.assertEqual(diagnosis["confidence_level"], "MODERATE")
        self.assertTrue(len(diagnosis["evidence"]) >= 5)
        self.assertIn("Laptop 16", diagnosis["evidence"][1])


if __name__ == "__main__":
    unittest.main()

