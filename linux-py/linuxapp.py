from flask import Flask, request
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import pyodbc
import os
import json
import time
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
    conn_str += ";Driver={ODBC Driver 18 for SQL Server}"
    conn = pyodbc.connect(conn_str, timeout=30)

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

    html = """
    <html>
    <head>
    <style>
        body {
            margin: 0;
            padding: 0;
            background: linear-gradient(145deg, #0d1117, #1b2636);
            font-family: 'Segoe UI', sans-serif;
            color: #e6edf3;
        }

        .container {
            width: 80%;
            margin: 40px auto;
        }

        .title {
            text-align: center;
            font-size: 34px;
            font-weight: 700;
            margin-bottom: 20px;
            color: #ffffff;
            text-shadow: 0px 0px 8px #0af;
        }

        .card {
            background: #161b22;
            border-radius: 14px;
            padding: 28px;
            border: 1px solid #30363d;
            box-shadow: 0 0 18px rgba(0,0,0,0.3);
        }

        input {
            padding: 10px;
            width: 250px;
            border-radius: 6px;
            border: 1px solid #30363d;
            background: #0d1117;
            color: white;
            font-size: 16px;
        }

        button {
            padding: 10px 18px;
            background: #238636;
            border: none;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            font-size: 16px;
            margin-left: 4px;
        }

        button:hover {
            background: #2ea043;
        }

        .btn {
            display: inline-block;
            padding: 14px 22px;
            margin-top: 20px;
            margin-right: 12px;
            font-size: 18px;
            border-radius: 10px;
            text-decoration: none;
            color: white;
            font-weight: 500;
        }

        .green-btn { background: #238636; }
        .green-btn:hover { background: #2ea043; }

        .blue-btn { background: #0366d6; }
        .blue-btn:hover { background: #0572ed; }

        .records {
            margin-top: 30px;
            padding: 20px;
            background: #0d1117;
            border-radius: 10px;
            border: 1px solid #30363d;
        }

        .record-item {
            padding: 8px 0;
            border-bottom: 1px solid #30363d;
        }
    </style>
    </head>

    <body>
    <div class="container">

        <div class="title">
            NTMS Azure Batch — Key Vault → SQL → App Service Demo
        </div>

        <div class="card">
            <form method="post" action="/add">
                <input name="name" placeholder="Enter Name" required>
                <button>Add</button>
            </form>

            <a href="/live" class="btn green-btn">🚀 View Live API Flow Animation</a>
            <a href="/flow" class="btn blue-btn">🎨 View Architecture Flow</a>
        </div>

        <div class="records">
            <h3>📌 Stored Records</h3>
    """

    # Insert SQL rows
    for r in rows:
        html += f"<div class='record-item'>{r[0]} — {r[1]} — {r[2]}</div>"

    html += """
        </div>
    </div>
    </body>
    </html>
    """

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
        steps.append({"step": msg, "time": time.time()})

    try:
        # ----------------------------------------------------
        # 1. Get Managed Identity Token
        # ----------------------------------------------------
        log("🔵 Requesting Managed Identity token from Azure AD")

        credential = DefaultAzureCredential(
            managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
        )
        token = credential.get_token("https://vault.azure.net/.default")

        log(f"🟢 Azure AD returned access token (expires in {token.expires_on - int(time.time())}s)")

        # ----------------------------------------------------
        # 2. Call Key Vault with token
        # ----------------------------------------------------
        log("🔵 Calling Key Vault using access token")

        client = SecretClient(vault_url=KEY_VAULT_URI, credential=credential)
        secret = client.get_secret(SECRET_NAME)

        log("🟢 Key Vault returned SQL connection string")

        conn_str = secret.value

        # ----------------------------------------------------
        # 3. Open SQL connection
        # ----------------------------------------------------
        log("🔵 Opening ODBC connection to Azure SQL")

        # Parse Key Vault ADO.NET style → ODBC format
        parts = {}
        for item in conn_str.split(";"):
            if "=" in item:
                key, value = item.split("=", 1)
                parts[key.strip().lower()] = value.strip()

        server = parts["server"].replace("tcp:", "").split(",")[0]
        database = parts["database"]
        username = parts.get("user id") or parts.get("uid")
        password = parts.get("password") or parts.get("pwd")

        odbc_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={server};"
            "PORT=1433;"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
        )

        conn = pyodbc.connect(odbc_str, timeout=5)

        log("🟢 SQL login successful")

        # ----------------------------------------------------
        # 4. Run SELECT
        # ----------------------------------------------------
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
