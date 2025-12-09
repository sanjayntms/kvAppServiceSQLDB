from flask import Flask, request
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import pyodbc
import os

app = Flask(__name__)

KEY_VAULT_URI = os.getenv("KEY_VAULT_URI")
SECRET_NAME = "sql-conn-string"

def get_connection():
    # Use Managed Identity inside App Service
    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )

    # Get connection string from Key Vault
    client = SecretClient(vault_url=KEY_VAULT_URI, credential=credential)
    conn_str = client.get_secret(SECRET_NAME).value

    # Normalize and ALWAYS append the driver
    conn_str = conn_str.strip().rstrip(";")
    conn_str += ";Driver={ODBC Driver 17 for SQL Server}"

    try:
        conn = pyodbc.connect(conn_str, timeout=5)
        return conn
    except Exception as e:
        raise Exception(
            f"\n❌ ODBC connection failed: {e}\n"
            f"➡️ Connection string used: {conn_str}\n"
        )


@app.route("/", methods=["GET"])
def index():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT Id, Name, CreatedAt FROM DemoRecords ORDER BY Id DESC")
    rows = cursor.fetchall()

    html = "<h1>NTMS Azure Batch - Security -Key Vault → SQL → App Service Demo</h1>"
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
