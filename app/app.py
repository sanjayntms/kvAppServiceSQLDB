from flask import Flask, request
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import pymssql
import os

app = Flask(__name__)

KEY_VAULT_URI = os.getenv("KEY_VAULT_URI")
SECRET_NAME = "sql-conn-string"

def get_connection():
    # Required for App Service Managed Identity to authenticate
    credential = DefaultAzureCredential(
        managed_identity_client_id=os.getenv("AZURE_CLIENT_ID")
    )

    client = SecretClient(vault_url=KEY_VAULT_URI, credential=credential)

    conn_str = client.get_secret(SECRET_NAME).value

    # Parse ADO.NET Connection String → pymssql format
    parts = {}
    for item in conn_str.split(";"):
        if "=" in item:
            key, value = item.split("=", 1)
            parts[key.strip().lower()] = value.strip()

    # ADO.NET keys → pymssql translation
    server = parts["server"].replace("tcp:", "").replace(",1433", "")
    username = parts.get("uid") or parts.get("user id")
    password = parts.get("pwd") or parts.get("password")
    database = parts["database"]

    try:
        return pymssql.connect(server=server, user=username, password=password, database=database)
    except Exception as e:
        raise Exception(f"pymssql connection failed: {e}\nParsed parts: {parts}")

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

    return html

@app.route("/add", methods=["POST"])
def add_record():
    name = request.form.get("name")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO DemoRecords (Name) VALUES (%s)", (name,))
    conn.commit()
    return "<h3>Record Added!</h3><a href='/'>Back</a>"

if __name__ == '__main__':
   app.run()
