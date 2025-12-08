import os
import pyodbc
from flask import Flask, request

app = Flask(__name__)

# App Service automatically retrieves the Key Vault secret via:
#   SQL_CONN = @Microsoft.KeyVault(SecretUri=...)
SQL_CONN = os.getenv("SQL_CONN")

def get_connection():
    """Return a live SQL connection using the ODBC connection string."""
    if not SQL_CONN:
        raise Exception("SQL_CONN environment variable not set.")

    return pyodbc.connect(
        SQL_CONN,
        timeout=5
    )

@app.route("/", methods=["GET"])
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Name, CreatedAt FROM DemoRecords ORDER BY Id DESC")
    rows = cursor.fetchall()

    html = "<h1>Key Vault → SQL → App Service Demo</h1>"
    html += "<form method='post' action='/add'>"
    html += "<input name='name' placeholder='Enter Name' required>"
    html += "<button>Add</button></form><hr>"

    for r in rows:
        html += f"{r[0]} — {r[1]} — {r[2]}<br>"

    return html


@app.route("/add", methods=["POST"])
def add_record():
    name = request.form.get("name")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO DemoRecords (Name) VALUES (?)", (name,))
    conn.commit()
    return "<h3>Record Added!</h3><a href='/'>Back</a>"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
