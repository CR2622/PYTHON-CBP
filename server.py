import http.server
import socketserver
import json
import sys
import os

# Import the existing Python NumPy logic
import expense_analyzer

PORT = 8000

class ExpenseAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve frontend files from the 'static' directory
        super().__init__(*args, directory="static", **kwargs)
        
    def do_GET(self):
        # Route for the REST API
        if self.path == '/api/analyze':
            self.handle_analyze()
        else:
            # Fallback to serving static files (index.html, styles.css, app.js)
            super().do_GET()
            
    def do_POST(self):
        if self.path == '/api/transactions':
            self.handle_add_transaction()
        elif self.path == '/api/chat':
            self.handle_chat()
        else:
            self.send_response(404)
            self.end_headers()
            
    def handle_analyze(self):
        try:
            # Ensure we read the file from the current directory, not 'static'
            filepath = "bank_statement.txt"
            
            # Execute the data pipeline
            transactions = expense_analyzer.build_transactions(filepath)
            grouped = expense_analyzer.group_by_category(transactions)
            stats = expense_analyzer.compute_all_stats(grouped)
            
            # Calculate overall metrics
            overall_total = sum(s["total"] for s in stats.values())
            annual_forecast = expense_analyzer.forecast_annual(overall_total)
            
            # Prepare the JSON payload
            response = {
                "stats": stats,
                "overall_total": overall_total,
                "annual_forecast": annual_forecast,
                "high_volatility": [cat for cat, s in stats.items() if s["volatile"]]
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            # The INVALID_LINE_TO_TEST_ERROR_HANDLING line is handled by expense_analyzer.py.
            # This catch-all ensures any unexpected errors don't crash the server.
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {"error": str(e)}
            self.wfile.write(json.dumps(error_response).encode('utf-8'))

    def handle_add_transaction(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            date = data.get('date')
            category = data.get('category')
            amount = data.get('amount')
            
            if not all([date, category, amount]):
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing fields"}).encode('utf-8'))
                return
                
            # Append to bank_statement.txt
            with open("bank_statement.txt", "a", encoding="utf-8") as f:
                f.write(f"{date},{category},{amount}\n")
                
            self.send_response(201)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def handle_chat(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_message = data.get('message', '')
            if not user_message:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing message"}).encode('utf-8'))
                return

            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "GEMINI_API_KEY environment variable is not set on the server."}).encode('utf-8'))
                return

            # Get financial context
            filepath = "bank_statement.txt"
            try:
                transactions = expense_analyzer.build_transactions(filepath)
                grouped = expense_analyzer.group_by_category(transactions)
                stats = expense_analyzer.compute_all_stats(grouped)
                overall_total = sum(s["total"] for s in stats.values())
                annual_forecast = expense_analyzer.forecast_annual(overall_total)
                
                context = f"Financial Context:\nOverall Monthly Total: ${overall_total:.2f}\nAnnual Forecast: ${annual_forecast:.2f}\n"
                context += "Category Breakdown:\n"
                for cat, s in stats.items():
                    context += f"- {cat}: Total ${s['total']:.2f}, Mean ${s['mean']:.2f}, StdDev ${s['std']:.2f}\n"
            except Exception as e:
                context = "Financial context currently unavailable."

            system_prompt = "You are a helpful and intelligent financial assistant for the 'Expense Forecaster' dashboard. Use the user's financial context below to provide personalized advice and answer their questions concisely. Format your response using markdown if helpful. Financial Context:\n" + context
            
            import urllib.request
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            headers = {'Content-Type': 'application/json'}
            payload = {
                "system_instruction": {
                    "parts": [{"text": system_prompt}]
                },
                "contents": [
                    {"role": "user", "parts": [{"text": user_message}]}
                ]
            }
            
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
            try:
                response = urllib.request.urlopen(req)
                result = json.loads(response.read().decode('utf-8'))
                bot_text = result['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                bot_text = f"Error calling Gemini API. Make sure your API key is valid."
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"reply": bot_text}).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

def run_server():
    with socketserver.TCPServer(("", PORT), ExpenseAPIHandler) as httpd:
        print(f"[INFO] Serving at http://localhost:{PORT}")
        print("[INFO] Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] Server stopped.")

if __name__ == '__main__':
    run_server()
