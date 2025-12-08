from flask import Flask, request, Response
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import pyodbc
import os
import json
import time

app = Flask(__name__)

# Environment variables set by App Service:
#   KEY_VAULT_URI
#   AZURE_CLIENT_ID  (optional if system identity is default)
KEY_VAULT_URI = os.getenv("KEY_VAULT_URI")
SECRET_NAME = "sql-conn-string"


# ----------------------------------------------------
# DATABASE CONNECTION USING PYODBC + ODBC DRIVER 18
# ----------------------------------------------------
def get_connection():
    credential = DefaultAzureCredential(managed_identity_client_id=os.getenv("AZURE_CLIENT_ID"))
    client = SecretClient(vault_url=KEY_VAULT_URI, credential=credential)

    conn_str = client.get_secret(SECRET_NAME).value

    # Parse Key Vault ADO.NET string
    parts = {}
    for item in conn_str.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            parts[key.strip().lower()] = value.strip()

    server = parts["server"]  # full tcp:servername.database.windows.net,1433
    database = parts["database"]
    username = parts["user id"]
    password = parts["password"]
    encrypt = parts.get("encrypt", "yes")

    # pyodbc ODBC driver connection string
    odbc_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate=no;"
    )

    return pyodbc.connect(odbc_str)


# ----------------------------------------------------
# HOME PAGE (Show Records)
# ----------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Name, CreatedAt FROM DemoRecords ORDER BY Id DESC")
    rows = cursor.fetchall()

    html = "<h1>Key Vault → SQL → App Service Demo</h1>"
    html += "<form method='post' action='/add'>"
    html += "<input name='name' placeholder='Enter Name'>"
    html += "<button>Add</button>"
    html += "</form><hr>"

    for r in rows:
        html += f"{r[0]} — {r[1]} — {r[2]}<br>"

    html += "<br><br>"
    html += "<a href='/live'><button style='padding:12px;font-size:18px;'>Show Live API Flow 🚀</button></a>"
    html += "<br><br>"
    html += "<a href='/flow'><button style='padding:12px;font-size:18px;'>Show Architecture Flow 🎨</button></a>"

    return html


# ----------------------------------------------------
# ADD A RECORD
# ----------------------------------------------------
@app.route("/add", methods=["POST"])
def add_record():
    name = request.form.get("name")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO DemoRecords (Name) VALUES (?)", (name,))
    conn.commit()

    return "<h3>Record Added!</h3><a href='/'>Back</a>"


# ----------------------------------------------------
# LIVE API STATUS — Shows actual backend operations
# ----------------------------------------------------
@app.route("/live/status")
def live_status():
    steps = []

    def log(msg):
        steps.append({"step": msg, "timestamp": time.time()})

    try:
        log("🔵 Calling Key Vault for SQL secret")
        conn = get_connection()
        log("🟢 Key Vault returned SQL connection string")

        cursor = conn.cursor()
        log("🔵 Running SQL SELECT")

        cursor.execute("SELECT TOP 1 Id, Name FROM DemoRecords ORDER BY Id DESC")
        row = cursor.fetchone()

        if row:
            log(f"🟢 SQL OK — Latest record: {row[0]} - {row[1]}")
        else:
            log("🟢 SQL OK — No records found")

        return json.dumps({"status": "ok", "steps": steps})

    except Exception as ex:
        log(f"❌ ERROR: {str(ex)}")
        return json.dumps({"status": "error", "steps": steps})


# ----------------------------------------------------
# SERVE LIVE ANIMATION PAGE
# ----------------------------------------------------
@app.route("/live")
def live_page():
    return app.send_static_file("liveflow.html")


# ----------------------------------------------------
# ARCHITECTURE FLOW PAGE (/flow)
# ----------------------------------------------------
@app.route("/flow")
def flow_page():
    return app.send_static_file("flow.html")  # You can replace with animated page


# ----------------------------------------------------
# RUN FLASK (App Service ignores the port you set)
# ----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
