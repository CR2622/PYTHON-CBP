# Personal Expense Forecaster

A lightweight web application for tracking and forecasting personal expenses. It features a vanilla JavaScript frontend, a custom Python HTTP server, and uses NumPy for data analysis. It also includes an integrated AI financial assistant powered by the Gemini API.

## Features
- **REST API & Vanilla UI:** A clean frontend design paired with a robust Python backend API.
- **Expense Analysis & Forecasting:** Uses statistical methods to understand your spending patterns and forecast annual expenses.
- **AI Financial Assistant:** Integrated chat with Gemini to get personalized financial advice based on your current expense context.
- **Dynamic Updates:** Add new transactions on the fly and have them automatically appended to your local records.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CR2622/PYTHON-CBP.git
   cd PYTHON-CBP
   ```

2. **Environment Variables:**
   Set the `GEMINI_API_KEY` environment variable to use the AI chat assistant functionality.
   
   *Windows (PowerShell):*
   ```powershell
   $env:GEMINI_API_KEY="your-api-key"
   ```
   
   *macOS/Linux:*
   ```bash
   export GEMINI_API_KEY="your-api-key"
   ```

3. **Run the Server:**
   This application utilizes standard Python libraries and does not require heavy web frameworks like Flask or Django.
   ```bash
   python server.py
   ```
   The application will be served locally at [http://localhost:8000](http://localhost:8000).

## Architecture
- `server.py`: Custom HTTP server handling REST API endpoints and static file serving.
- `expense_analyzer.py`: Contains the core data processing logic utilizing NumPy to extract statistical insights from `bank_statement.txt`.
- `static/`: Contains the `index.html`, `styles.css`, and vanilla `app.js` for the frontend dashboard.
