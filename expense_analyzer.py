#!/usr/bin/env python3
"""
Personal Expense Analyzer & Forecaster
=======================================
A command-line application that reads a bank statement text file, parses
transactions into objects, performs NumPy-powered statistical analysis,
and prints a formatted financial forecast report.

Data Pipeline:
    Read File -> Parse to Objects -> Convert to NumPy Arrays -> Analyze -> Output Report

Dependencies: numpy (standard library otherwise)
Usage: python expense_analyzer.py
"""

from __future__ import annotations

import io
import sys

# Ensure stdout can handle UTF-8 on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from datetime import datetime
from typing import Generator

import numpy as np


# ──────────────────────────────────────────────────────────────────────────────
# 1. TRANSACTION CLASS (OOP)
# ──────────────────────────────────────────────────────────────────────────────

class Transaction:
    """Represents a single financial transaction parsed from a bank statement.

    Attributes:
        date:     The date the transaction occurred.
        category: Spending category (e.g. 'Groceries', 'Rent').
        amount:   Transaction amount in dollars.
    """

    def __init__(self, date: datetime, category: str, amount: float) -> None:
        self.date: datetime = date
        self.category: str = category
        self.amount: float = amount

    def __repr__(self) -> str:
        """Return a human-readable string representation of the transaction."""
        return (
            f"Transaction(date={self.date.strftime('%Y-%m-%d')}, "
            f"category='{self.category}', amount={self.amount:.2f})"
        )

    @property
    def month_name(self) -> str:
        """Return the full month name of the transaction date."""
        return self.date.strftime("%B")


# ──────────────────────────────────────────────────────────────────────────────
# 2. GENERATOR – MEMORY-EFFICIENT FILE READER
# ──────────────────────────────────────────────────────────────────────────────

def read_transactions(filepath: str) -> Generator[str, None, None]:
    """Yield one stripped, non-empty line at a time from *filepath*.

    This generator simulates memory-efficient reading of arbitrarily large
    bank-statement files by never loading the entire file into memory.

    Args:
        filepath: Path to the bank statement text file.

    Yields:
        Each non-blank line from the file, with leading/trailing whitespace
        removed.

    Raises:
        FileNotFoundError: If *filepath* does not exist.
    """
    file_handle = None
    try:
        file_handle = open(filepath, "r", encoding="utf-8")
        for line in file_handle:
            stripped = line.strip()
            if stripped:
                yield stripped
    except FileNotFoundError:
        print(f"\n[ERROR] File not found: '{filepath}'")
        print("        Please ensure 'bank_statement.txt' exists in the working directory.")
        sys.exit(1)
    finally:
        if file_handle is not None:
            file_handle.close()
        print("[INFO] File stream closed.")


# ──────────────────────────────────────────────────────────────────────────────
# 3. PARSING – LINE → TRANSACTION (with exception handling)
# ──────────────────────────────────────────────────────────────────────────────

def parse_line(raw_line: str) -> Transaction | None:
    """Attempt to parse a raw CSV line into a Transaction object.

    Handles malformed lines gracefully by printing a warning and returning
    ``None`` instead of raising an exception.

    Args:
        raw_line: A single comma-separated line (date,category,amount).

    Returns:
        A ``Transaction`` instance on success, or ``None`` if the line is
        malformed.
    """
    fields = raw_line.split(",")

    # --- wrong number of fields ---
    if len(fields) != 3:
        print(f"[WARNING] Skipping malformed line (wrong field count): {raw_line}")
        return None

    date_str, category, amount_str = fields

    # --- bad date ---
    try:
        date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        print(f"[WARNING] Skipping malformed line (invalid date): {raw_line}")
        return None

    # --- bad amount ---
    try:
        amount = float(amount_str.strip())
    except ValueError:
        print(f"[WARNING] Skipping malformed line (invalid amount): {raw_line}")
        return None

    return Transaction(date=date, category=category.strip(), amount=amount)


# ──────────────────────────────────────────────────────────────────────────────
# 4. BUILD TRANSACTION LIST (list comprehension + filter)
# ──────────────────────────────────────────────────────────────────────────────

def build_transactions(filepath: str) -> list[Transaction]:
    """Read and parse all valid transactions from *filepath*.

    Uses a **list comprehension** over the generator to construct the list,
    filtering out any ``None`` results from malformed lines.

    Args:
        filepath: Path to the bank statement text file.

    Returns:
        A list of successfully parsed ``Transaction`` objects.
    """
    # List comprehension over the generator, skipping None results
    transactions: list[Transaction] = [
        txn
        for raw in read_transactions(filepath)
        if (txn := parse_line(raw)) is not None
    ]
    return transactions


def filter_by_category(transactions: list[Transaction], category: str) -> list[Transaction]:
    """Return only transactions matching *category* (case-insensitive).

    Uses ``filter()`` with a **lambda** as required.

    Args:
        transactions: Full list of transactions.
        category:     The category name to filter on.

    Returns:
        A filtered list of transactions.
    """
    return list(
        filter(lambda t: t.category.lower() == category.lower(), transactions)
    )


def group_by_category(transactions: list[Transaction]) -> dict[str, list[Transaction]]:
    """Group transactions by their category using a **dict comprehension**.

    Args:
        transactions: Full list of transactions.

    Returns:
        A dictionary mapping each category name to its list of transactions.
    """
    categories: set[str] = {t.category for t in transactions}
    return {
        cat: [t for t in transactions if t.category == cat]
        for cat in sorted(categories)
    }


# ──────────────────────────────────────────────────────────────────────────────
# 5. NUMPY ANALYSIS
# ──────────────────────────────────────────────────────────────────────────────

def analyze_category(amounts: np.ndarray) -> dict[str, float]:
    """Compute summary statistics for a NumPy array of transaction amounts.

    Args:
        amounts: 1-D array of spending amounts for one category.

    Returns:
        Dictionary with keys: total, mean, std, min, max.
    """
    return {
        "total": float(np.sum(amounts)),
        "mean":  float(np.mean(amounts)),
        "std":   float(np.std(amounts)),
        "min":   float(np.min(amounts)),
        "max":   float(np.max(amounts)),
    }


def compute_all_stats(
    grouped: dict[str, list[Transaction]],
) -> dict[str, dict[str, float]]:
    """Run ``analyze_category`` for every category and add volatility flags.

    A category is flagged as **HIGH VOLATILITY** when its standard deviation
    exceeds 50 % of its mean.

    Args:
        grouped: Transactions grouped by category.

    Returns:
        Nested dict: ``{category: {total, mean, std, min, max, volatile}}``.
    """
    stats: dict[str, dict[str, float]] = {}
    for cat, txns in grouped.items():
        amounts = np.array([t.amount for t in txns])
        result = analyze_category(amounts)
        # Volatility flag: std > 50% of mean
        result["volatile"] = 1.0 if result["std"] > 0.5 * result["mean"] else 0.0
        stats[cat] = result
    return stats


# ──────────────────────────────────────────────────────────────────────────────
# 6. FORECASTING
# ──────────────────────────────────────────────────────────────────────────────

def forecast_annual(monthly_total: float) -> float:
    """Project annual spending using simple linear extrapolation.

    Args:
        monthly_total: Total spending for the current month.

    Returns:
        Estimated annual spending (monthly × 12).
    """
    return monthly_total * 12


# ──────────────────────────────────────────────────────────────────────────────
# 7. REPORT PRINTING
# ──────────────────────────────────────────────────────────────────────────────

def print_report(
    stats: dict[str, dict[str, float]],
    transactions: list[Transaction],
) -> None:
    """Print a formatted financial analysis report to the terminal.

    Args:
        stats:        Per-category statistics from ``compute_all_stats``.
        transactions: Full list of parsed transactions (used for metadata).
    """
    if not transactions:
        print("\n[INFO] No valid transactions to report.")
        return

    month = transactions[0].month_name
    year = transactions[0].date.year

    # -- Header --
    width = 100
    print("\n" + "=" * width)
    print("  PERSONAL EXPENSE ANALYZER & FORECASTER".center(width))
    print(f"  Report for: {month} {year}".center(width))
    print("=" * width)

    # -- Per-Category Table --
    header = (
        f"  {'Category':<15}"
        f"{'Total':>10}"
        f"{'Mean':>10}"
        f"{'Std Dev':>10}"
        f"{'Min':>10}"
        f"{'Max':>10}"
        f"  {'Volatility':<16}"
    )
    print("\n" + header)
    print("  " + "-" * (width - 4))

    overall_total = 0.0
    high_vol_categories: list[str] = []

    for cat, s in stats.items():
        flag = "!! HIGH" if s["volatile"] else "   Normal"
        row = (
            f"  {cat:<15}"
            f"${s['total']:>9.2f}"
            f"${s['mean']:>9.2f}"
            f"${s['std']:>9.2f}"
            f"${s['min']:>9.2f}"
            f"${s['max']:>9.2f}"
            f"  {flag:<16}"
        )
        print(row)
        overall_total += s["total"]
        if s["volatile"]:
            high_vol_categories.append(cat)

    print("  " + "-" * (width - 4))

    # -- Monthly Total --
    print(f"\n  {'Monthly Total Spending:':<35} ${overall_total:>10.2f}")

    # -- Annual Forecast --
    annual = forecast_annual(overall_total)
    print(f"  {'Projected Annual Spending:':<35} ${annual:>10.2f}")

    # -- High-Volatility Warnings --
    print("\n  " + "-" * (width - 4))
    if high_vol_categories:
        print("\n  !!  HIGH-VOLATILITY CATEGORIES:")
        for cat in high_vol_categories:
            s = stats[cat]
            pct = (s["std"] / s["mean"]) * 100 if s["mean"] != 0 else 0
            print(
                f"     * {cat:<15} -- Std Dev is {pct:.0f}% of Mean "
                f"(${s['std']:.2f} vs ${s['mean']:.2f}). "
                f"Spending in this category is unpredictable."
            )
    else:
        print("\n  [OK] No high-volatility categories detected. Spending is stable.")

    print("\n" + "=" * width)

    # -- Demo: filter by category using lambda --
    groceries = filter_by_category(transactions, "Groceries")
    print(f"\n  [DEMO] Filtered 'Groceries' transactions ({len(groceries)} found):")
    for g in groceries:
        print(f"     {g}")

    print("\n" + "=" * width + "\n")


# ──────────────────────────────────────────────────────────────────────────────
# 8. ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Run the full expense analysis pipeline.

    Pipeline stages:
        1. Read raw lines via generator
        2. Parse into Transaction objects (list comprehension)
        3. Group by category (dict comprehension)
        4. Convert to NumPy arrays & compute statistics
        5. Print formatted report with forecast
    """
    filepath = "bank_statement.txt"

    # Step 1-2: Read & Parse
    transactions = build_transactions(filepath)
    print(f"[INFO] Successfully parsed {len(transactions)} transactions.\n")

    # Step 3: Group by category (dict comprehension)
    grouped = group_by_category(transactions)

    # Step 4: NumPy analysis
    stats = compute_all_stats(grouped)

    # Step 5: Report
    print_report(stats, transactions)


if __name__ == "__main__":
    main()
