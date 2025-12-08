from flask import Flask, request
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import pyodbc
import os

app = Flask(__name__)

# Values injected by GitHub Actions + App Service
KEY_VAULT_URI = os.getenv("KEY_VAULT_URI")
SECRET_NAME = "sql-conn-string"

def get_connection():
    # Required on Azure App Service for Managed Identity authentication
    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )

    # Retrieve SQL connection string from Key Vault
    client = SecretClient(vault_url=KEY_VAULT_URI, credential=credential)
    conn_str = client.get_secret(SECRET_NAME).value

    # App Service requires explicit SQL ODBC driver
    if "Driver=" not in conn_str:
        conn_str += ";Driver={ODBC Driver 17 for SQL Server}"

    try:
        # pyodbc supports redirect mode used by Azure SQL
        conn = pyodbc.connect(conn_str, timeout=5)
        return conn
    except Exception as e:
        raise Exception(
            f"ODBC connection failed: {e}\n"
            f"Connection string used: {conn_str}"
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
    # App Service supplies its own PORT dynamically
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
