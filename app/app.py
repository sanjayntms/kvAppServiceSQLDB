import os
import pyodbc
from flask import Flask

app = Flask(__name__)

conn_str = os.environ.get("SQL_CONN")

@app.route("/")
def index():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT GETDATE()")
        row = cursor.fetchone()
        return f"Connected to SQL! Time: {row[0]}"
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Azure App Service provides PORT env var
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

