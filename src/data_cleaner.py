"""
Data Cleaner Module
Processes validated data, splits trusted records from quarantined records,
and exports clean_orders.csv, rejected_orders.csv, and data_quality_report.csv.
"""

from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd

from src.data_validator import DataValidator


class DataCleaner:
    """Separates clean and rejected orders, applies currency conversion, and exports audit logs."""

    def __init__(self, validator_results: List[Dict]):
        self.results = validator_results
        self.results_df = pd.DataFrame(validator_results)

    def generate_clean_and_rejected_datasets(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Splits validation results into clean_orders and rejected_orders DataFrames.
        Applies necessary field standardizations and conversions.
        """
        clean_rows = []
        rejected_rows = []

        for r in self.results:
            if r["is_valid"]:
                clean_rows.append({
                    "order_id": r["order_id"],
                    "order_date": r["parsed_date"],
                    "customer_id": r["customer_id"],
                    "product_id": r["product_id"],
                    "quantity": r["quantity"],
                    "unit_price": r["unit_price"],
                    "currency": r["currency"],
                    "status": r["cleaned_status"],
                    "rate_to_inr": 85.0 if r["currency"] == "USD" else 1.0,
                    "revenue_inr": r["trusted_revenue_inr"] if r["cleaned_status"] == "completed" else 0.0,
                })
            else:
                rejected_rows.append({
                    "original_row_index": r["row_index"],
                    "order_id": r["order_id"],
                    "order_date": r["order_date"],
                    "customer_id": r["customer_id"],
                    "product_id": r["product_id"],
                    "quantity": r["quantity"],
                    "unit_price": r["unit_price"],
                    "currency": r["currency"],
                    "raw_status": r["raw_status"],
                    "rejection_reasons": r["rejection_reasons"],
                    "potential_revenue_inr": r["potential_revenue_inr"],
                })

        clean_orders_df = pd.DataFrame(clean_rows)
        rejected_orders_df = pd.DataFrame(rejected_rows)

        return clean_orders_df, rejected_orders_df

    def generate_data_quality_report(self) -> pd.DataFrame:
        """
        Compiles an aggregated audit summary of all data quality issues found across the dataset.
        """
        issue_occurrences = []
        for r in self.results:
            if not r["is_valid"]:
                for reason in r["rejection_reasons_list"]:
                    # Categorize reason
                    cat = "Other"
                    if "duplicate" in reason.lower():
                        cat = "Duplicate Record"
                    elif "conflicting" in reason.lower():
                        cat = "Conflicting Order ID"
                    elif "customer_id" in reason.lower():
                        cat = "Foreign Key Violation (Customer)"
                    elif "product_id" in reason.lower():
                        cat = "Foreign Key Violation (Product)"
                    elif "date" in reason.lower():
                        cat = "Invalid Date"
                    elif "quantity" in reason.lower():
                        cat = "Non-positive Quantity"
                    elif "price" in reason.lower():
                        cat = "Non-positive Price"
                    elif "currency" in reason.lower():
                        cat = "Unsupported Currency"
                    elif "status" in reason.lower():
                        cat = "Unrecognized Status"

                    issue_occurrences.append({
                        "issue_category": cat,
                        "specific_reason": reason,
                        "order_id": r["order_id"],
                        "potential_revenue_inr": r["potential_revenue_inr"],
                    })

        issue_df = pd.DataFrame(issue_occurrences)
        if issue_df.empty:
            return pd.DataFrame(columns=[
                "issue_category", "occurrences", "affected_order_ids", "potential_financial_impact_inr", "recommended_action"
            ])

        remediation_map = {
            "Duplicate Record": "Deduplicate identical rows safely using order_id and record hash.",
            "Conflicting Order ID": "Quarantine for engineering audit; verify transaction logs to clarify discrepancy.",
            "Foreign Key Violation (Customer)": "Quarantine; verify customer master sync or backfill missing customer IDs.",
            "Foreign Key Violation (Product)": "Quarantine; verify product catalog lookup or catalog sync latency.",
            "Invalid Date": "Reject invalid dates; inspect ingestion source format and timestamp serialization.",
            "Non-positive Quantity": "Reject zero or negative units; investigate return/reversal logging protocol.",
            "Non-positive Price": "Reject zero price; investigate promotional discount override or testing artifact.",
            "Unsupported Currency": "Quarantine unapproved currency; configure exchange rate table if currency is approved.",
            "Unrecognized Status": "Enforce strict enum validation on order ingestion; audit case and spelling conventions.",
        }

        report_rows = []
        for cat, group in issue_df.groupby("issue_category"):
            report_rows.append({
                "issue_category": cat,
                "occurrences": len(group),
                "affected_order_ids": ", ".join(sorted(group["order_id"].unique())),
                "potential_financial_impact_inr": round(group["potential_revenue_inr"].sum(), 2),
                "recommended_action": remediation_map.get(cat, "Inspect source data pipeline and audit transaction logs."),
            })

        dq_report_df = pd.DataFrame(report_rows).sort_values(by="occurrences", ascending=False)
        return dq_report_df

    def save_outputs(
        self,
        clean_df: pd.DataFrame,
        rejected_df: pd.DataFrame,
        dq_report_df: pd.DataFrame,
        output_dir: str = "output",
    ) -> Dict[str, Path]:
        """Saves generated CSVs to the designated output folder."""
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        clean_path = out_path / "clean_orders.csv"
        rejected_path = out_path / "rejected_orders.csv"
        dq_path = out_path / "data_quality_report.csv"

        clean_df.to_csv(clean_path, index=False)
        rejected_df.to_csv(rejected_path, index=False)
        dq_report_df.to_csv(dq_path, index=False)

        return {
            "clean_orders": clean_path,
            "rejected_orders": rejected_path,
            "data_quality_report": dq_path,
        }


if __name__ == "__main__":
    from src.data_loader import DataLoader

    loader = DataLoader()
    orders_df, customers_df, products_df = loader.load_data()
    validator = DataValidator(orders_df, customers_df, products_df)
    results = validator.validate_all()

    cleaner = DataCleaner(results)
    clean_df, rejected_df = cleaner.generate_clean_and_rejected_datasets()
    dq_df = cleaner.generate_data_quality_report()
    saved = cleaner.save_outputs(clean_df, rejected_df, dq_df)

    print(f"Clean orders saved: {len(clean_df)} rows to {saved['clean_orders']}")
    print(f"Rejected orders saved: {len(rejected_df)} rows to {saved['rejected_orders']}")
    print(f"Data quality report saved: {len(dq_df)} categories to {saved['data_quality_report']}")
    print(dq_df.to_string())

