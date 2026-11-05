"""
Data Validator Module
Implements comprehensive deterministic validation checks according to Finance definitions.
"""

from typing import Dict, List, Set, Tuple, Any
import numpy as np
import pandas as pd


class DataValidator:
    """Validates raw orders, customers, and products against finance rules."""

    SUPPORTED_CURRENCIES = {"INR", "USD"}
    VALID_STATUSES = {"completed", "cancelled", "refunded"}
    USD_TO_INR_RATE = 85.0

    def __init__(
        self,
        orders_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
    ):
        self.raw_orders = orders_df.copy()
        self.raw_customers = customers_df.copy()
        self.raw_products = products_df.copy()

        self.valid_cust_ids = set(self.raw_customers["customer_id"].dropna().str.strip())
        self.valid_prod_ids = set(self.raw_products["product_id"].dropna().str.strip())

    def identify_duplicates_and_conflicts(self) -> Tuple[List[int], Set[str]]:
        """
        Differentiates between exact duplicate rows and conflicting order_ids.
        Returns:
            - exact_duplicate_indices: row indices of redundant identical duplicates to drop.
            - conflicting_order_ids: set of order_ids that have conflicting values.
        """
        exact_duplicate_indices = []
        conflicting_order_ids = set()

        groups = self.raw_orders.groupby("order_id")
        for order_id, group in groups:
            if len(group) > 1:
                first_row = group.iloc[0]
                is_all_identical = True
                for i in range(1, len(group)):
                    # Check if all column values match exactly
                    if not group.iloc[i].equals(first_row):
                        is_all_identical = False
                        break

                if is_all_identical:
                    # Keep the first, mark subsequent duplicates for quarantine/drop
                    exact_duplicate_indices.extend(group.index[1:].tolist())
                else:
                    conflicting_order_ids.add(order_id)

        return exact_duplicate_indices, conflicting_order_ids

    def validate_date(self, date_val: Any) -> Tuple[bool, str, Any]:
        """
        Validates date string parseability and sanity.
        Returns (is_valid, reason, parsed_timestamp).
        """
        if pd.isna(date_val) or str(date_val).strip() == "":
            return False, "Missing order_date", None

        date_str = str(date_val).strip()
        try:
            # pd.to_datetime handles ISO8601 and YYYY/MM/DD, but rejects invalid calendar dates like 2026-09-31
            dt = pd.to_datetime(date_str, errors="raise")
            return True, "", dt
        except Exception as e:
            return False, f"Invalid/unparseable order_date: '{date_str}'", None

    def validate_row(
        self,
        idx: int,
        row: pd.Series,
        exact_duplicate_indices: List[int],
        conflicting_order_ids: Set[str],
    ) -> Dict[str, Any]:
        """Validates an individual order row across all validation rules."""
        rejection_reasons = []
        order_id = str(row.get("order_id", "")).strip()

        # 1. Conflicting Order ID
        if order_id in conflicting_order_ids:
            rejection_reasons.append("Conflicting order_id with inconsistent records")

        # 2. Exact Duplicate Row
        if idx in exact_duplicate_indices:
            rejection_reasons.append("Exact duplicate row")

        # 3. Customer Foreign Key Validation
        cust_id = row.get("customer_id")
        if pd.isna(cust_id) or str(cust_id).strip() == "":
            rejection_reasons.append("Missing customer_id")
        else:
            cust_id_clean = str(cust_id).strip()
            if cust_id_clean not in self.valid_cust_ids:
                rejection_reasons.append(f"Invalid customer_id foreign key: '{cust_id_clean}'")

        # 4. Product Foreign Key Validation
        prod_id = row.get("product_id")
        if pd.isna(prod_id) or str(prod_id).strip() == "":
            rejection_reasons.append("Missing product_id")
        else:
            prod_id_clean = str(prod_id).strip()
            if prod_id_clean not in self.valid_prod_ids:
                rejection_reasons.append(f"Invalid product_id foreign key: '{prod_id_clean}'")

        # 5. Date Validation
        is_date_valid, date_reason, parsed_dt = self.validate_date(row.get("order_date"))
        if not is_date_valid:
            rejection_reasons.append(date_reason)

        # 6. Quantity Validation (> 0)
        qty_val = None
        try:
            raw_qty = row.get("quantity")
            qty_val = int(raw_qty)
            if qty_val <= 0:
                rejection_reasons.append(f"Non-positive quantity: {qty_val}")
        except Exception:
            rejection_reasons.append(f"Invalid quantity: '{row.get('quantity')}'")

        # 7. Unit Price Validation (> 0)
        price_val = None
        try:
            raw_price = row.get("unit_price")
            price_val = float(raw_price)
            if price_val <= 0:
                rejection_reasons.append(f"Non-positive unit_price: {price_val}")
        except Exception:
            rejection_reasons.append(f"Invalid unit_price: '{row.get('unit_price')}'")

        # 8. Currency Validation
        currency_raw = str(row.get("currency", "")).strip().upper()
        if currency_raw not in self.SUPPORTED_CURRENCIES:
            rejection_reasons.append(f"Unsupported currency: '{row.get('currency')}'")

        # 9. Status Normalization & Validation
        status_raw = str(row.get("status", ""))
        status_norm = status_raw.strip().lower()

        # Rule: valid completed status is completed. Do not automatically equate COMPLETE with completed.
        if status_norm not in self.VALID_STATUSES:
            rejection_reasons.append(
                f"Unrecognized status: '{status_raw}' (normalized: '{status_norm}')"
            )

        # Calculate revenue & potential revenue
        is_valid = len(rejection_reasons) == 0
        rate = self.USD_TO_INR_RATE if currency_raw == "USD" else 1.0

        trusted_revenue_inr = None
        if is_valid and status_norm == "completed" and qty_val is not None and price_val is not None:
            trusted_revenue_inr = round(qty_val * price_val * rate, 2)

        potential_revenue_inr = 0.0
        if not is_valid:
            try:
                q = float(row.get("quantity", 0))
                p = float(row.get("unit_price", 0))
                # Currency conversion for potential revenue if known
                r = self.USD_TO_INR_RATE if currency_raw == "USD" else (1.0 if currency_raw == "INR" else 0.0)
                if q > 0 and p > 0 and r > 0:
                    potential_revenue_inr = round(q * p * r, 2)
            except Exception:
                potential_revenue_inr = 0.0

        return {
            "row_index": idx,
            "order_id": order_id,
            "order_date": row.get("order_date"),
            "parsed_date": parsed_dt.strftime("%Y-%m-%d") if parsed_dt is not None else None,
            "month": parsed_dt.strftime("%Y-%m") if parsed_dt is not None else None,
            "customer_id": str(cust_id).strip() if pd.notna(cust_id) else None,
            "product_id": str(prod_id).strip() if pd.notna(prod_id) else None,
            "quantity": qty_val,
            "unit_price": price_val,
            "currency": currency_raw,
            "raw_status": status_raw,
            "cleaned_status": status_norm,
            "is_valid": is_valid,
            "rejection_reasons": "; ".join(rejection_reasons) if rejection_reasons else None,
            "rejection_reasons_list": rejection_reasons,
            "trusted_revenue_inr": trusted_revenue_inr,
            "potential_revenue_inr": potential_revenue_inr,
        }

    def validate_all(self) -> List[Dict[str, Any]]:
        """Runs validation on every row in the raw orders dataset."""
        exact_dups, conflicts = self.identify_duplicates_and_conflicts()
        results = []
        for idx, row in self.raw_orders.iterrows():
            res = self.validate_row(idx, row, exact_dups, conflicts)
            results.append(res)
        return results


if __name__ == "__main__":
    from src.data_loader import DataLoader
    loader = DataLoader()
    orders_df, customers_df, products_df = loader.load_data()
    validator = DataValidator(orders_df, customers_df, products_df)
    results = validator.validate_all()
    invalid_rows = [r for r in results if not r["is_valid"]]
    print(f"Total validated rows: {len(results)}")
    print(f"Total invalid / rejected rows: {len(invalid_rows)}")
    for r in invalid_rows[:5]:
        print(f"Order {r['order_id']} (Row {r['row_index']}): {r['rejection_reasons']}")

