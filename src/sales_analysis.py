"""
Sales Analysis Module
Executes analytical SQL queries in SQLite and computes key sales metrics,
including monthly comparisons, product performance, regional trends, and customer cohorts.
"""

from pathlib import Path
import sqlite3
from typing import Dict, Any, Tuple
import pandas as pd


class SalesAnalyzer:
    """Computes finance-compliant revenue and sales analytics using SQLite and Pandas."""

    def __init__(
        self,
        clean_orders_df: pd.DataFrame,
        customers_df: pd.DataFrame,
        products_df: pd.DataFrame,
        db_path: str = ":memory:",
    ):
        self.clean_orders = clean_orders_df.copy()
        self.customers = customers_df.copy()
        self.products = products_df.copy()
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._setup_database()

    def _setup_database(self) -> None:
        """Loads clean tables into SQLite database."""
        self.clean_orders.to_sql("clean_orders", self.conn, if_exists="replace", index=False)
        self.customers.to_sql("customers", self.conn, if_exists="replace", index=False)
        self.products.to_sql("products", self.conn, if_exists="replace", index=False)

    def execute_query(self, query: str) -> pd.DataFrame:
        """Executes an arbitrary SQL query against the SQLite database."""
        return pd.read_sql_query(query, self.conn)

    def get_monthly_kpis(self) -> pd.DataFrame:
        """Computes core monthly KPIs for August and September 2026."""
        query = """
        SELECT 
            strftime('%Y-%m', order_date) AS month,
            COUNT(order_id) AS completed_orders,
            SUM(quantity) AS total_quantity,
            COUNT(DISTINCT customer_id) AS customer_count,
            ROUND(SUM(quantity * unit_price * CASE WHEN currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS total_revenue_inr,
            ROUND(AVG(quantity * unit_price * CASE WHEN currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS aov_inr
        FROM clean_orders
        WHERE status = 'completed'
        GROUP BY strftime('%Y-%m', order_date)
        ORDER BY month ASC;
        """
        df = self.execute_query(query)
        return df

    def get_monthly_comparison_summary(self) -> Dict[str, Any]:
        """Calculates absolute and percentage changes between August and September 2026."""
        df = self.get_monthly_kpis().set_index("month")

        aug = df.loc["2026-08"]
        sep = df.loc["2026-09"]

        rev_aug = float(aug["total_revenue_inr"])
        rev_sep = float(sep["total_revenue_inr"])
        rev_diff = rev_sep - rev_aug
        rev_pct_change = (rev_diff / rev_aug) * 100.0

        orders_aug = int(aug["completed_orders"])
        orders_sep = int(sep["completed_orders"])
        orders_diff = orders_sep - orders_aug
        orders_pct_change = (orders_diff / orders_aug) * 100.0

        aov_aug = float(aug["aov_inr"])
        aov_sep = float(sep["aov_inr"])
        aov_diff = aov_sep - aov_aug
        aov_pct_change = (aov_diff / aov_aug) * 100.0

        qty_aug = int(aug["total_quantity"])
        qty_sep = int(sep["total_quantity"])
        qty_diff = qty_sep - qty_aug
        qty_pct_change = (qty_diff / qty_aug) * 100.0

        cust_aug = int(aug["customer_count"])
        cust_sep = int(sep["customer_count"])
        cust_diff = cust_sep - cust_aug
        cust_pct_change = (cust_diff / cust_aug) * 100.0

        return {
            "august_revenue_inr": rev_aug,
            "september_revenue_inr": rev_sep,
            "absolute_revenue_diff_inr": rev_diff,
            "percentage_revenue_change": round(rev_pct_change, 2),
            "august_completed_orders": orders_aug,
            "september_completed_orders": orders_sep,
            "orders_diff": orders_diff,
            "orders_pct_change": round(orders_pct_change, 2),
            "august_aov_inr": aov_aug,
            "september_aov_inr": aov_sep,
            "aov_diff_inr": aov_diff,
            "aov_pct_change": round(aov_pct_change, 2),
            "august_total_quantity": qty_aug,
            "september_total_quantity": qty_sep,
            "quantity_diff": qty_diff,
            "quantity_pct_change": round(qty_pct_change, 2),
            "august_customer_count": cust_aug,
            "september_customer_count": cust_sep,
            "customer_diff": cust_diff,
            "customer_pct_change": round(cust_pct_change, 2),
        }

    def get_product_performance(self) -> pd.DataFrame:
        """Product-wise monthly revenue and growth/decline analysis."""
        query = """
        SELECT 
            p.product_id,
            p.product_name,
            p.category,
            strftime('%Y-%m', o.order_date) AS month,
            SUM(o.quantity) AS units_sold,
            COUNT(o.order_id) AS order_count,
            ROUND(SUM(o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS revenue_inr
        FROM clean_orders o
        JOIN products p ON o.product_id = p.product_id
        WHERE o.status = 'completed'
        GROUP BY p.product_id, p.product_name, p.category, strftime('%Y-%m', o.order_date);
        """
        raw_prod = self.execute_query(query)
        piv = raw_prod.pivot_table(
            index=["product_id", "product_name", "category"],
            columns="month",
            values="revenue_inr",
            fill_value=0.0,
        ).reset_index()

        if "2026-08" not in piv.columns:
            piv["2026-08"] = 0.0
        if "2026-09" not in piv.columns:
            piv["2026-09"] = 0.0

        piv["absolute_change_inr"] = piv["2026-09"] - piv["2026-08"]
        piv["percentage_change"] = (
            piv["absolute_change_inr"] / piv["2026-08"].replace(0, float("nan"))
        ) * 100.0
        piv["percentage_change"] = piv["percentage_change"].round(2)
        piv = piv.sort_values(by="absolute_change_inr", ascending=True)
        return piv

    def get_category_performance(self) -> pd.DataFrame:
        """Category-wise monthly revenue comparison."""
        query = """
        SELECT 
            p.category,
            strftime('%Y-%m', o.order_date) AS month,
            ROUND(SUM(o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS revenue_inr
        FROM clean_orders o
        JOIN products p ON o.product_id = p.product_id
        WHERE o.status = 'completed'
        GROUP BY p.category, strftime('%Y-%m', o.order_date);
        """
        raw_cat = self.execute_query(query)
        piv = raw_cat.pivot_table(
            index="category",
            columns="month",
            values="revenue_inr",
            fill_value=0.0,
        ).reset_index()

        if "2026-08" not in piv.columns:
            piv["2026-08"] = 0.0
        if "2026-09" not in piv.columns:
            piv["2026-09"] = 0.0

        piv["absolute_change_inr"] = piv["2026-09"] - piv["2026-08"]
        piv["percentage_change"] = (
            piv["absolute_change_inr"] / piv["2026-08"].replace(0, float("nan"))
        ) * 100.0
        piv["percentage_change"] = piv["percentage_change"].round(2)
        piv = piv.sort_values(by="absolute_change_inr", ascending=True)
        return piv

    def get_regional_performance(self) -> pd.DataFrame:
        """Region-wise monthly revenue and growth/decline analysis."""
        query = """
        SELECT 
            c.region,
            strftime('%Y-%m', o.order_date) AS month,
            COUNT(o.order_id) AS completed_orders,
            COUNT(DISTINCT o.customer_id) AS active_customers,
            ROUND(SUM(o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END), 2) AS revenue_inr
        FROM clean_orders o
        JOIN customers c ON o.customer_id = c.customer_id
        WHERE o.status = 'completed'
        GROUP BY c.region, strftime('%Y-%m', o.order_date);
        """
        raw_reg = self.execute_query(query)
        piv = raw_reg.pivot_table(
            index="region",
            columns="month",
            values="revenue_inr",
            fill_value=0.0,
        ).reset_index()

        if "2026-08" not in piv.columns:
            piv["2026-08"] = 0.0
        if "2026-09" not in piv.columns:
            piv["2026-09"] = 0.0

        piv["absolute_change_inr"] = piv["2026-09"] - piv["2026-08"]
        piv["percentage_change"] = (
            piv["absolute_change_inr"] / piv["2026-08"].replace(0, float("nan"))
        ) * 100.0
        piv["percentage_change"] = piv["percentage_change"].round(2)
        piv = piv.sort_values(by="absolute_change_inr", ascending=True)
        return piv

    def get_new_vs_repeat_customers(self) -> pd.DataFrame:
        """
        Computes new vs repeat customer contribution within the dataset window.
        Rule: A customer's first completed order in the Aug-Sep dataset is 'New';
        orders on later dates are 'Repeat'.
        """
        query = """
        WITH first_orders AS (
            SELECT 
                customer_id,
                MIN(order_date) AS first_completed_date
            FROM clean_orders
            WHERE status = 'completed'
            GROUP BY customer_id
        ),
        classified_orders AS (
            SELECT 
                o.order_id,
                o.order_date,
                strftime('%Y-%m', o.order_date) AS month,
                o.customer_id,
                o.quantity * o.unit_price * CASE WHEN o.currency = 'USD' THEN 85.0 ELSE 1.0 END AS revenue_inr,
                CASE 
                    WHEN o.order_date = f.first_completed_date THEN 'New'
                    ELSE 'Repeat'
                END AS customer_type
            FROM clean_orders o
            JOIN first_orders f ON o.customer_id = f.customer_id
            WHERE o.status = 'completed'
        )
        SELECT 
            month,
            customer_type,
            COUNT(order_id) AS order_count,
            COUNT(DISTINCT customer_id) AS customer_count,
            ROUND(SUM(revenue_inr), 2) AS total_revenue_inr,
            ROUND(AVG(revenue_inr), 2) AS aov_inr
        FROM classified_orders
        GROUP BY month, customer_type
        ORDER BY month ASC, customer_type DESC;
        """
        df = self.execute_query(query)
        return df

    def close(self) -> None:
        """Closes SQLite connection."""
        self.conn.close()


if __name__ == "__main__":
    clean_orders = pd.read_csv("output/clean_orders.csv")
    customers = pd.read_csv("data/customers.csv")
    products = pd.read_csv("data/products.csv")

    analyzer = SalesAnalyzer(clean_orders, customers, products)
    print("--- Monthly KPIs ---")
    print(analyzer.get_monthly_kpis())
    print("\n--- Comparison Summary ---")
    print(analyzer.get_monthly_comparison_summary())
    print("\n--- Product Performance ---")
    print(analyzer.get_product_performance())
    print("\n--- Category Performance ---")
    print(analyzer.get_category_performance())
    print("\n--- Regional Performance ---")
    print(analyzer.get_regional_performance())
    print("\n--- New vs Repeat Customers ---")
    print(analyzer.get_new_vs_repeat_customers())
    analyzer.close()

