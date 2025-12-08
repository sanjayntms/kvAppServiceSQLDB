from flask import Flask, request, Response
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import pymssql
import os
import json
import time

app = Flask(__name__)

# Environment variables set in App Service:
# KEY_VAULT_URI
# AZURE_CLIENT_ID (optional if using system identity)
KEY_VAULT_URI = os.getenv("KEY_VAULT_URI")
SECRET_NAME = "sql-conn-string"


# -----------------------------
# Helper: Connect to SQL
# -----------------------------
def get_connection():
    credential = DefaultAzureCredential(managed_identity_client_id=os.getenv("AZURE_CLIENT_ID"))

    client = SecretClient(vault_url=KEY_VAULT_URI, credential=credential)
    conn_str = client.get_secret(SECRET_NAME).value

    # Parse ADO.NET connection string
    parts = {}
    for item in conn_str.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            parts[key.strip().lower()] = value.strip()

    server = parts["server"].replace("tcp:", "").replace(",1433", "")
    username = parts["user id"]
    password = parts["password"]
    database = parts["database"]

    return pymssql.connect(server, username, password, database)


# -----------------------------
# Homepage — Shows DB Records
# -----------------------------
@app.route("/", methods=["GET"])
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Name, CreatedAt FROM DemoRecords ORDER BY Id DESC")
    rows = cursor.fetchall()

    html = "<h1>Key Vault → SQL → App Service Demo</h1>"
    html += "<form method='post' action='/add'>"
    html += "<input name='name' placeholder='Enter Name'>"
    html += "<button>Add</button></form><hr>"

    for r in rows:
        html += f"{r[0]} — {r[1]} — {r[2]}<br>"

    # Add button to open live animation
    html += "<br><br><a href='/live'><button style='padding:12px;font-size:18px;'>Show Live API Flow 🚀</button></a>"

    return html


# -----------------------------
# Add a Record
# -----------------------------
@app.route("/add", methods=["POST"])
def add_record():
    name = request.form.get("name")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO DemoRecords (Name) VALUES (%s)", (name,))
    conn.commit()
    return "<h3>Record Added!</h3><a href='/'>Back</a>"


# -----------------------------
# Real-Time API Testing Endpoint
# -----------------------------
@app.route("/live/status")
def live_status():
    steps = []

    def add(label):
        steps.append({"step": label, "timestamp": time.time()})

    try:
        add("🔵 Calling Key Vault for secret")
        conn = get_connection()
        add("🟢 Key Vault returned SQL connection string")

        cursor = conn.cursor()
        add("🔵 Running SQL SELECT")

        cursor.execute("SELECT TOP 1 Id, Name FROM DemoRecords ORDER BY Id DESC")
        row = cursor.fetchone()

        if row:
            add(f"🟢 SQL Query OK — Latest record: {row[0]} - {row[1]}")
        else:
            add("🟢 SQL Query OK — No records yet")

        return json.dumps({"status": "ok", "steps": steps})

    except Exception as ex:
        add(f"❌ Error: {str(ex)}")
        return json.dumps({"status": "error", "steps": steps})


# -----------------------------
# Serve Animated HTML Page (/live)
# -----------------------------
@app.route("/live")
def live_page():
    return app.send_static_file("liveflow.html")


# -----------------------------
# Animated System Flow Page (/flow)
# -----------------------------
@app.route("/flow")
def flow_page():
    html = """ 
    <!-- Your animated static flow HTML inserted here -->
    <h1>Flow page placeholder — replace with full animated HTML</h1>
    <p>This is /flow route.</p>
    """
    return Response(html, mimetype="text/html")


# -----------------------------
# Run App (App Service ignores port)
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
