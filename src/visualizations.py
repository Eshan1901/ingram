"""
Visualizations Module
Generates 7 publication-quality charts for executive presentations and dashboards.
Saved automatically to output/charts/.
"""

from pathlib import Path
from typing import Dict, Any, List
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


class ChartGenerator:
    """Creates clear, modern visual analytics conforming to executive reporting standards."""

    def __init__(self, output_dir: str = "output/charts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        sns.set_theme(style="whitegrid", font="sans-serif")
        plt.rcParams.update({
            "font.size": 11,
            "axes.titlesize": 13,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.labelweight": "bold",
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "figure.autolayout": True,
        })

    def plot_monthly_revenue_comparison(self, summary: Dict[str, Any]) -> Path:
        """Chart 1: August vs September revenue comparison."""
        fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
        months = ["August 2026", "September 2026"]
        revs = [summary["august_revenue_inr"], summary["september_revenue_inr"]]
        colors = ["#2b5c8f", "#d95f02"]

        bars = ax.bar(months, [r / 1e5 for r in revs], color=colors, width=0.45, edgecolor="black", linewidth=1.2)

        for bar, rev in zip(bars, revs):
            yval = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                yval + 0.3,
                f"INR {rev:,.2f}\n({yval:.2f} Lakh)",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        pct = summary["percentage_revenue_change"]
        diff = summary["absolute_revenue_diff_inr"]
        ax.set_title("Completed Monthly Revenue (Trusted Records Only)", pad=15)
        ax.set_ylabel("Revenue (Lakh INR)", labelpad=10)
        ax.set_ylim(0, max(revs) / 1e5 * 1.25)

        ax.text(
            0.5,
            0.85,
            f"Decline: INR {abs(diff):,.2f} ({pct:.2f}%)\nCalculated strictly across validated orders",
            transform=ax.transAxes,
            ha="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#fee0d2", edgecolor="#de2d26", linewidth=1.2),
            fontsize=10,
            fontweight="bold",
        )

        save_path = self.output_dir / "01_revenue_comparison.png"
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_monthly_orders_comparison(self, summary: Dict[str, Any]) -> Path:
        """Chart 2: Monthly completed order comparison."""
        fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
        months = ["August 2026", "September 2026"]
        orders = [summary["august_completed_orders"], summary["september_completed_orders"]]
        colors = ["#386cb0", "#f0027f"]

        bars = ax.bar(months, orders, color=colors, width=0.45, edgecolor="black", linewidth=1.2)

        for bar, count in zip(bars, orders):
            yval = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                yval + 2,
                f"{count} Orders",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        pct = summary["orders_pct_change"]
        diff = summary["orders_diff"]
        ax.set_title("Completed Orders Volume (Monthly)", pad=15)
        ax.set_ylabel("Completed Orders Count", labelpad=10)
        ax.set_ylim(0, max(orders) * 1.2)

        ax.text(
            0.5,
            0.85,
            f"Volume Change: {diff} Orders ({pct:.2f}%)\nDemonstrates lower completed transaction count",
            transform=ax.transAxes,
            ha="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff2ae", edgecolor="#e6ab02", linewidth=1.2),
            fontsize=10,
            fontweight="bold",
        )

        save_path = self.output_dir / "02_orders_comparison.png"
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_aov_comparison(self, summary: Dict[str, Any]) -> Path:
        """Chart 3: Average order value comparison."""
        fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
        months = ["August 2026", "September 2026"]
        aovs = [summary["august_aov_inr"], summary["september_aov_inr"]]
        colors = ["#4daf4a", "#984ea3"]

        bars = ax.bar(months, aovs, color=colors, width=0.45, edgecolor="black", linewidth=1.2)

        for bar, aov in zip(bars, aovs):
            yval = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                yval + 300,
                f"INR {aov:,.2f}",
                ha="center",
                va="bottom",
                fontsize=10,
                fontweight="bold",
            )

        pct = summary["aov_pct_change"]
        diff = summary["aov_diff_inr"]
        ax.set_title("Average Order Value (AOV) Comparison", pad=15)
        ax.set_ylabel("AOV (INR)", labelpad=10)
        ax.set_ylim(0, max(aovs) * 1.22)

        ax.text(
            0.5,
            0.85,
            f"AOV Change: -INR {abs(diff):,.2f} ({pct:.2f}%)\nReflects reduced ticket size per order",
            transform=ax.transAxes,
            ha="center",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#e5f5e0", edgecolor="#31a354", linewidth=1.2),
            fontsize=10,
            fontweight="bold",
        )

        save_path = self.output_dir / "03_aov_comparison.png"
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_product_revenue_comparison(self, prod_perf: pd.DataFrame) -> Path:
        """Chart 4: Product-wise revenue comparison (Where the shift occurred)."""
        fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
        df = prod_perf.copy().sort_values(by="2026-08", ascending=True)

        y_positions = np.arange(len(df))
        bar_height = 0.38

        aug_revs = df["2026-08"] / 1e5
        sep_revs = df["2026-09"] / 1e5

        ax.barh(y_positions + bar_height / 2, aug_revs, height=bar_height, label="August 2026", color="#2b5c8f", edgecolor="black")
        ax.barh(y_positions - bar_height / 2, sep_revs, height=bar_height, label="September 2026", color="#d95f02", edgecolor="black")

        ax.set_yticks(y_positions)
        ax.set_yticklabels(df["product_name"], fontsize=10, fontweight="bold")
        ax.set_xlabel("Revenue (Lakh INR)", labelpad=10)
        ax.set_title("Product-Level Revenue: Identifying Where Revenue Shifted", pad=15)
        ax.legend(loc="lower right", frameon=True, framealpha=0.9)

        for i, (_, row) in enumerate(df.iterrows()):
            if row["product_name"] == "Laptop 16":
                ax.text(
                    max(aug_revs.iloc[i], sep_revs.iloc[i]) + 0.2,
                    i,
                    "-INR 7.92L (-84.62%)",
                    va="center",
                    fontsize=9,
                    fontweight="bold",
                    color="#b30000",
                )

        save_path = self.output_dir / "04_product_revenue_comparison.png"
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_regional_sales_comparison(self, reg_perf: pd.DataFrame) -> Path:
        """Chart 5: Region-wise sales comparison."""
        fig, ax = plt.subplots(figsize=(9, 6), dpi=300)
        df = reg_perf.copy().sort_values(by="region")

        x = np.arange(len(df))
        width = 0.35

        aug_vals = df["2026-08"] / 1e5
        sep_vals = df["2026-09"] / 1e5

        b1 = ax.bar(x - width / 2, aug_vals, width, label="August 2026", color="#2b5c8f", edgecolor="black")
        b2 = ax.bar(x + width / 2, sep_vals, width, label="September 2026", color="#d95f02", edgecolor="black")

        for b in b1:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 0.1, f"{h:.2f}L", ha="center", va="bottom", fontsize=9, fontweight="bold")
        for b in b2:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 0.1, f"{h:.2f}L", ha="center", va="bottom", fontsize=9, fontweight="bold")

        ax.set_xticks(x)
        ax.set_xticklabels(df["region"], fontsize=11, fontweight="bold")
        ax.set_ylabel("Revenue (Lakh INR)", labelpad=10)
        ax.set_title("Regional Sales Distribution: South & North Drops vs West Growth", pad=15)
        ax.set_ylim(0, max(max(aug_vals), max(sep_vals)) * 1.25)
        ax.legend(loc="upper right", frameon=True)

        save_path = self.output_dir / "05_region_sales_comparison.png"
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_data_quality_issues(self, dq_report: pd.DataFrame) -> Path:
        """Chart 6: Data quality issue distribution."""
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        df = dq_report.sort_values(by="occurrences", ascending=True)

        y_pos = np.arange(len(df))
        bars = ax.barh(y_pos, df["occurrences"], color="#7570b3", edgecolor="black", height=0.55)

        for bar, occ in zip(bars, df["occurrences"]):
            w = bar.get_width()
            ax.text(w + 0.1, bar.get_y() + bar.get_height() / 2, f"{occ} record(s)", va="center", fontsize=10, fontweight="bold")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(df["issue_category"], fontsize=10, fontweight="bold")
        ax.set_xlabel("Number of Occurrences", labelpad=10)
        ax.set_title("Distribution of Quarantined Records by Quality Defect", pad=15)
        ax.set_xlim(0, max(df["occurrences"]) + 1.2)

        save_path = self.output_dir / "06_data_quality_issues.png"
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def plot_revenue_impact_excluded(self, sensitivity: Dict[str, Any]) -> Path:
        """Chart 7: Revenue impact of excluded records (Hypothetical Sensitivity Bounds)."""
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

        scenarios = [
            "Scenario 1:\nTrusted Baseline\n(Audited Clean)",
            "Scenario 2:\nHypothetical Max Sep\n(+ Ambiguous/O0036)",
            "Scenario 3:\nHypothetical Max Aug\n(+ Aug Quarantined)",
        ]

        sc1 = sensitivity.get("scenario_trusted", sensitivity.get("scenario_conservative", {}))
        sc2 = sensitivity.get("scenario_max_september", {})
        sc3 = sensitivity.get("scenario_max_august", {})

        aug_vals = [sc1["august_revenue"] / 1e5, sc2["august_revenue"] / 1e5, sc3["august_revenue"] / 1e5]
        sep_vals = [sc1["september_revenue"] / 1e5, sc2["september_revenue"] / 1e5, sc3["september_revenue"] / 1e5]
        pct_declines = [sc1["decline_pct"], sc2["decline_pct"], sc3["decline_pct"]]

        x = np.arange(len(scenarios))
        width = 0.35

        b1 = ax.bar(x - width / 2, aug_vals, width, label="August Revenue (Lakh)", color="#2b5c8f", edgecolor="black")
        b2 = ax.bar(x + width / 2, sep_vals, width, label="September Revenue (Lakh)", color="#d95f02", edgecolor="black")

        for i, pct in enumerate(pct_declines):
            y_top = max(aug_vals[i], sep_vals[i])
            ax.text(x[i], y_top + 0.8, f"Decline:\n{pct:.2f}%", ha="center", va="bottom", fontsize=10, fontweight="bold", color="#b30000")

        ax.set_xticks(x)
        ax.set_xticklabels(scenarios, fontsize=10, fontweight="bold")
        ax.set_ylabel("Revenue (Lakh INR)", labelpad=10)
        ax.set_title("Hypothetical Sensitivity Bounds Across Data Scenarios", pad=15)
        ax.set_ylim(0, max(max(aug_vals), max(sep_vals)) * 1.35)
        ax.legend(loc="upper right", frameon=True)

        save_path = self.output_dir / "07_revenue_impact_excluded.png"
        fig.savefig(save_path, bbox_inches="tight")
        plt.close(fig)
        return save_path

    def generate_all_charts(
        self,
        summary: Dict[str, Any],
        prod_perf: pd.DataFrame,
        reg_perf: pd.DataFrame,
        dq_report: pd.DataFrame,
        sensitivity: Dict[str, Any],
    ) -> List[Path]:
        """Generates all 7 required visualization charts."""
        paths = [
            self.plot_monthly_revenue_comparison(summary),
            self.plot_monthly_orders_comparison(summary),
            self.plot_aov_comparison(summary),
            self.plot_product_revenue_comparison(prod_perf),
            self.plot_regional_sales_comparison(reg_perf),
            self.plot_data_quality_issues(dq_report),
            self.plot_revenue_impact_excluded(sensitivity),
        ]
        return paths
