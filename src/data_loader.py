"""
Data Loader Module
Loads raw CSV data files (orders, customers, products) and provides initial data health checks.
"""

import os
from pathlib import Path
from typing import Dict, Tuple
import pandas as pd


class DataLoader:
    """Handles discovery and loading of raw dataset files."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = self._resolve_data_dir(data_dir)

    def _resolve_data_dir(self, target_dir: str) -> Path:
        """Finds the data directory from multiple standard locations."""
        candidates = [
            Path(target_dir),
            Path("data"),
            Path("candidate_pack/data"),
            Path("../data"),
            Path("../candidate_pack/data"),
        ]
        for p in candidates:
            if p.exists() and (p / "orders.csv").exists():
                return p.resolve()
        raise FileNotFoundError(
            f"Could not locate data directory containing orders.csv. Tried: {[str(c) for c in candidates]}"
        )

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Loads orders.csv, customers.csv, and products.csv.
        Returns raw untouched DataFrames: (orders_df, customers_df, products_df).
        """
        orders_path = self.data_dir / "orders.csv"
        customers_path = self.data_dir / "customers.csv"
        products_path = self.data_dir / "products.csv"

        if not orders_path.exists():
            raise FileNotFoundError(f"Missing file: {orders_path}")
        if not customers_path.exists():
            raise FileNotFoundError(f"Missing file: {customers_path}")
        if not products_path.exists():
            raise FileNotFoundError(f"Missing file: {products_path}")

        orders_df = pd.read_csv(orders_path, dtype=str)
        customers_df = pd.read_csv(customers_path, dtype=str)
        products_df = pd.read_csv(products_path, dtype=str)

        return orders_df, customers_df, products_df

    def get_raw_health_snapshot(
        self, orders_df: pd.DataFrame, customers_df: pd.DataFrame, products_df: pd.DataFrame
    ) -> Dict[str, Dict]:
        """Generates an initial data health snapshot for reporting."""
        snapshot = {
            "orders": {
                "total_rows": len(orders_df),
                "total_columns": len(orders_df.columns),
                "columns": list(orders_df.columns),
                "null_counts": orders_df.isnull().sum().to_dict(),
                "unique_order_ids": orders_df["order_id"].nunique(),
            },
            "customers": {
                "total_rows": len(customers_df),
                "total_columns": len(customers_df.columns),
                "columns": list(customers_df.columns),
                "null_counts": customers_df.isnull().sum().to_dict(),
                "unique_customer_ids": customers_df["customer_id"].nunique(),
            },
            "products": {
                "total_rows": len(products_df),
                "total_columns": len(products_df.columns),
                "columns": list(products_df.columns),
                "null_counts": products_df.isnull().sum().to_dict(),
                "unique_product_ids": products_df["product_id"].nunique(),
            },
        }
        return snapshot


if __name__ == "__main__":
    loader = DataLoader()
    o, c, p = loader.load_data()
    snap = loader.get_raw_health_snapshot(o, c, p)
    print("DataLoader Health Snapshot:")
    print(snap)

