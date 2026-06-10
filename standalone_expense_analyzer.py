#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         PERSONAL EXPENSE ANALYZER & FORECASTER  — Standalone Edition        ║
║                                                                              ║
║  • 100 % self-contained — bank data is embedded; no external files needed.  ║
║  • Run directly in PyScripter (or any Python 3.8+ environment).             ║
║  • Only external dependency: numpy  (pip install numpy)                     ║
╚══════════════════════════════════════════════════════════════════════════════╝

Data Pipeline:
    Embedded CSV string
        → Generator (line-by-line)
        → parse_line()  [OOP + exception handling]
        → Transaction objects
        → NumPy arrays
        → Statistical analysis
        → Formatted terminal report + annual forecast
"""

from __future__ import annotations

import io
import sys

# ── UTF-8 safety for Windows console ─────────────────────────────────────────
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from datetime import datetime
from typing import Generator

import numpy as np


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 0 – EMBEDDED BANK DATA
# ══════════════════════════════════════════════════════════════════════════════

# Paste your bank_statement.txt content here — or keep this sample.
# Format per line:  YYYY-MM-DD,Category,Amount
# Lines that don't match the format are skipped with a warning.

BANK_DATA = """\
2024-01-03,Groceries,45.20
2024-01-05,Rent,1200.00
2024-01-07,Dining,32.50
2024-01-09,Groceries,67.80
2024-01-11,Transport,15.00
2024-01-14,Entertainment,55.00
2024-01-15,Groceries,90.10
2024-01-18,Utilities,110.00
2024-01-20,Dining,48.00
2024-01-22,Transport,20.00
2024-01-25,Groceries,35.40
2024-01-27,Entertainment,80.00
2024-01-28,Dining,27.50
2024-01-30,Utilities,95.00
INVALID_LINE_TO_TEST_ERROR_HANDLING
2024-01-31,Groceries,60.00
"""

# ── Optional: set to a file path string to load from disk instead of BANK_DATA
#    e.g.  FILEPATH = r"C:\Users\radic\...\bank_statement.txt"
#    Leave as None to use the embedded BANK_DATA string above.
FILEPATH = None


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 – TRANSACTION CLASS  (OOP)
# ══════════════════════════════════════════════════════════════════════════════

class Transaction:
    """Represents a single financial transaction.

    Attributes:
        date     : datetime  — date the transaction occurred.
        category : str       — spending category (e.g. 'Groceries').
        amount   : float     — transaction amount in dollars (positive = expense).
    """

    def __init__(self, date: datetime, category: str, amount: float) -> None:
        self.date: datetime = date
        self.category: str = category
        self.amount: float = amount

    def __repr__(self) -> str:
        return (
            f"Transaction(date={self.date.strftime('%Y-%m-%d')}, "
            f"category='{self.category}', amount={self.amount:.2f})"
        )

    @property
    def month_name(self) -> str:
        """Full month name of the transaction date (e.g. 'January')."""
        return self.date.strftime("%B")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 – GENERATOR  (memory-efficient line reader)
# ══════════════════════════════════════════════════════════════════════════════

def _lines_from_string(data: str) -> Generator[str, None, None]:
    """Yield non-empty stripped lines from an in-memory string.

    Simulates the same interface as a file-based generator so the rest of
    the pipeline remains identical whether we read from disk or from the
    embedded constant.
    """
    for line in data.splitlines():
        stripped = line.strip()
        if stripped:
            yield stripped
    print("[INFO] Embedded data stream fully consumed.")


def _lines_from_file(filepath: str) -> Generator[str, None, None]:
    """Yield non-empty stripped lines from a disk file.

    Raises:
        SystemExit: if the file is not found.
    """
    fh = None
    try:
        fh = open(filepath, "r", encoding="utf-8")
        for line in fh:
            stripped = line.strip()
            if stripped:
                yield stripped
    except FileNotFoundError:
        print(f"\n[ERROR] File not found: '{filepath}'")
        print("        Falling back to embedded BANK_DATA …\n")
        yield from _lines_from_string(BANK_DATA)
        return
    finally:
        if fh is not None:
            fh.close()
        print("[INFO] File stream closed.")


def read_transactions(source: str | None) -> Generator[str, None, None]:
    """Route to the appropriate line generator based on *source*.

    Args:
        source: File path string, or ``None`` to use the embedded data.

    Yields:
        One raw CSV line at a time.
    """
    if source:
        yield from _lines_from_file(source)
    else:
        yield from _lines_from_string(BANK_DATA)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 – PARSING  (line → Transaction, with exception handling)
# ══════════════════════════════════════════════════════════════════════════════

def parse_line(raw_line: str) -> Transaction | None:
    """Parse one CSV line into a Transaction, or return None on any error.

    Format expected:  YYYY-MM-DD,Category,Amount

    Handles:
        * Wrong field count
        * Invalid date format
        * Non-numeric amount
    """
    fields = raw_line.split(",")

    if len(fields) != 3:
        print(f"[WARNING] Skipping malformed line (wrong field count): {raw_line!r}")
        return None

    date_str, category, amount_str = fields

    # ── date ──
    try:
        date = datetime.strptime(date_str.strip(), "%Y-%m-%d")
    except ValueError:
        print(f"[WARNING] Skipping malformed line (bad date): {raw_line!r}")
        return None

    # ── amount ──
    try:
        amount = float(amount_str.strip())
    except ValueError:
        print(f"[WARNING] Skipping malformed line (bad amount): {raw_line!r}")
        return None

    return Transaction(date=date, category=category.strip(), amount=amount)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 – BUILD & FILTER  (list comprehension, filter/lambda, dict comprehension)
# ══════════════════════════════════════════════════════════════════════════════

def build_transactions(source: str | None) -> list[Transaction]:
    """Read + parse all valid transactions from *source*.

    Uses a **list comprehension** with a walrus operator to compactly
    filter out None results from malformed lines.
    """
    return [
        txn
        for raw in read_transactions(source)
        if (txn := parse_line(raw)) is not None
    ]


def filter_by_category(transactions: list[Transaction], category: str) -> list[Transaction]:
    """Return transactions matching *category* (case-insensitive).

    Uses ``filter()`` with a **lambda** as the predicate.
    """
    return list(
        filter(lambda t: t.category.lower() == category.lower(), transactions)
    )


def group_by_category(transactions: list[Transaction]) -> dict[str, list[Transaction]]:
    """Group transactions by category using a **dict comprehension**."""
    categories: set[str] = {t.category for t in transactions}
    return {
        cat: [t for t in transactions if t.category == cat]
        for cat in sorted(categories)
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 – NUMPY ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def analyze_category(amounts: np.ndarray) -> dict[str, float]:
    """Compute summary statistics for one category's amounts.

    Returns:
        Dict with keys: total, mean, std, min, max.
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
    """Run analyze_category() for every group and flag high volatility.

    A category is HIGH VOLATILITY when  std > 50 % of mean.
    """
    stats: dict[str, dict[str, float]] = {}
    for cat, txns in grouped.items():
        amounts = np.array([t.amount for t in txns])
        result = analyze_category(amounts)
        result["volatile"] = 1.0 if result["std"] > 0.5 * result["mean"] else 0.0
        stats[cat] = result
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 – FORECASTING
# ══════════════════════════════════════════════════════════════════════════════

def forecast_annual(monthly_total: float) -> float:
    """Project annual spend via simple linear extrapolation (monthly × 12)."""
    return monthly_total * 12


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 – REPORT PRINTING
# ══════════════════════════════════════════════════════════════════════════════

def print_report(
    stats: dict[str, dict[str, float]],
    transactions: list[Transaction],
) -> None:
    """Print a formatted financial analysis report to the terminal."""
    if not transactions:
        print("\n[INFO] No valid transactions to report.")
        return

    month = transactions[0].month_name
    year  = transactions[0].date.year
    W     = 100   # report width

    # ── Header ───────────────────────────────────────────────────────────────
    print("\n" + "=" * W)
    print("  PERSONAL EXPENSE ANALYZER & FORECASTER".center(W))
    print(f"  Report for: {month} {year}".center(W))
    print("=" * W)

    # ── Category Table ────────────────────────────────────────────────────────
    header = (
        f"  {'Category':<15}"
        f"{'Txns':>6}"
        f"{'Total':>11}"
        f"{'Mean':>10}"
        f"{'Std Dev':>10}"
        f"{'Min':>10}"
        f"{'Max':>10}"
        f"  {'Volatility':<14}"
    )
    print("\n" + header)
    print("  " + "-" * (W - 4))

    overall_total        = 0.0
    high_vol_categories: list[str] = []

    for cat, s in stats.items():
        txn_count = len([t for t in transactions if t.category == cat])
        flag      = "!! HIGH" if s["volatile"] else "   Normal"
        row = (
            f"  {cat:<15}"
            f"{txn_count:>6}"
            f"  ${s['total']:>9.2f}"
            f"  ${s['mean']:>8.2f}"
            f"  ${s['std']:>8.2f}"
            f"  ${s['min']:>8.2f}"
            f"  ${s['max']:>8.2f}"
            f"  {flag:<14}"
        )
        print(row)
        overall_total += s["total"]
        if s["volatile"]:
            high_vol_categories.append(cat)

    print("  " + "-" * (W - 4))

    # ── Totals & Forecast ─────────────────────────────────────────────────────
    print(f"\n  {'Total Transactions Parsed:':<35} {len(transactions):>6}")
    print(f"  {'Monthly Total Spending:':<35} ${overall_total:>10.2f}")
    print(f"  {'Projected Annual Spending:':<35} ${forecast_annual(overall_total):>10.2f}")

    # ── High-Volatility Warnings ──────────────────────────────────────────────
    print("\n  " + "-" * (W - 4))
    if high_vol_categories:
        print("\n  !!  HIGH-VOLATILITY CATEGORIES  (Std Dev > 50% of Mean):")
        for cat in high_vol_categories:
            s   = stats[cat]
            pct = (s["std"] / s["mean"]) * 100 if s["mean"] != 0 else 0.0
            print(
                f"     * {cat:<15} — Std Dev is {pct:.0f}% of Mean "
                f"(${s['std']:.2f} vs ${s['mean']:.2f}). "
                f"Spending is unpredictable!"
            )
    else:
        print("\n  [OK] No high-volatility categories detected. Spending is stable.")

    print("\n" + "=" * W)

    # ── Demo: filter by category using lambda ─────────────────────────────────
    demo_cat  = "Groceries"
    groceries = filter_by_category(transactions, demo_cat)
    print(f"\n  [DEMO] filter_by_category('{demo_cat}') → {len(groceries)} transaction(s) found:")
    for g in groceries:
        print(f"     {g}")

    print("\n" + "=" * W + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 – ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    """Run the full expense analysis pipeline.

    Pipeline:
        1. Read raw lines (generator)           ← SECTION 2
        2. Parse to Transaction objects          ← SECTION 3
        3. Group by category (dict comprehension)← SECTION 4
        4. NumPy statistical analysis            ← SECTION 5
        5. Annual forecast                       ← SECTION 6
        6. Print formatted report                ← SECTION 7
    """
    print("=" * 60)
    print("  PERSONAL EXPENSE ANALYZER — Standalone PyScripter Edition")
    print("=" * 60)

    source = FILEPATH   # None → embedded BANK_DATA string

    # Steps 1-2: Read & Parse
    transactions = build_transactions(source)
    print(f"\n[INFO] Successfully parsed {len(transactions)} valid transaction(s).\n")

    if not transactions:
        print("[INFO] Nothing to analyse. Exiting.")
        return

    # Step 3: Group
    grouped = group_by_category(transactions)

    # Step 4: NumPy analysis
    stats = compute_all_stats(grouped)

    # Steps 5-6: Report + Forecast
    print_report(stats, transactions)


if __name__ == "__main__":
    main()
