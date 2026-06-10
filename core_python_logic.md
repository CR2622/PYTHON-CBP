# Core Python Backend Logic - Expense Tracker

This file outlines the main Python components and functions that power the Expense Tracker backend, focusing on data processing, OOP structures, statistical analysis, and the REST API.

## 1. Object-Oriented Data Model (`expense_analyzer.py`)
- **`class Transaction`**: Represents a single financial transaction parsed from the bank statement. It encapsulates the properties `date` (datetime object), `category` (string), and `amount` (float). It provides a clean human-readable representation and a `month_name` helper property.

## 2. Memory-Efficient File Reading (`expense_analyzer.py`)
- **`read_transactions(filepath)`**: A Python **generator function**. Instead of loading the entire bank statement into memory at once, it yields one line at a time. This allows the application to handle massive data files efficiently.

## 3. Data Parsing & Exception Handling (`expense_analyzer.py`)
- **`parse_line(raw_line)`**: Takes a raw CSV string line and attempts to parse it into a `Transaction` object. It includes comprehensive exception handling (`try/except ValueError`) to gracefully skip malformed lines (e.g., bad dates or non-numeric amounts) without crashing the program.

## 4. Advanced Data Transformation (`expense_analyzer.py`)
- **`build_transactions(filepath)`**: Uses a **list comprehension** combined with the walrus operator (`:=`) to quickly build a list of valid `Transaction` objects from the file generator.
- **`filter_by_category(transactions, category)`**: Uses Python's built-in `filter()` function alongside a **lambda** function to isolate transactions belonging to a specific category.
- **`group_by_category(transactions)`**: Uses a **dict comprehension** to elegantly group all transactions into a dictionary mapping category names to lists of transactions.

## 5. NumPy Statistical Analysis (`expense_analyzer.py`)
- **`analyze_category(amounts)`**: Takes a NumPy array of transaction amounts and calculates the total, mean, standard deviation, minimum, and maximum spending.
- **`compute_all_stats(grouped)`**: Iterates over every category, leveraging NumPy arrays to compute statistics. Importantly, it flags categories as "HIGH VOLATILITY" if their standard deviation exceeds 50% of the mean (unpredictable spending).
- **`forecast_annual(monthly_total)`**: Performs linear extrapolation to project the user's annual spending based on the current month's total.

## 6. The REST API Web Server (`server.py`)
- **`class ExpenseAPIHandler`**: A custom HTTP request handler that extends `http.server.SimpleHTTPRequestHandler`.
- **`do_GET()`**: Routes GET requests. Specifically intercepts `/api/analyze` to run the backend analysis pipeline and return the calculated financial stats to the frontend.
- **`do_POST()`**: Routes POST requests. Handles `/api/transactions` (to safely append new transactions to the `bank_statement.txt` file) and `/api/chat` (to contextually interact with the Gemini AI for smart financial advice).
