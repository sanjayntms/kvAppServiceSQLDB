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

@app.route("/flow", methods=["GET"])
def flow_page():
    html = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Azure Key Vault → App Service → SQL Flow</title>
  <style>
    * {
      box-sizing: border-box;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    body {
      margin: 0;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      background: radial-gradient(circle at top, #1f6feb, #020817);
      color: #f9fafb;
    }
    .shell {
      width: min(1000px, 95vw);
      background: rgba(15,23,42,0.95);
      border-radius: 24px;
      padding: 24px 24px 28px;
      box-shadow: 0 24px 70px rgba(0,0,0,0.7);
      border: 1px solid rgba(148,163,184,0.4);
      position: relative;
      overflow: hidden;
    }
    .shell::before {
      content: "";
      position: absolute;
      inset: -40%;
      background: radial-gradient(circle at 0 0, rgba(125,211,252,0.16), transparent 55%),
                  radial-gradient(circle at 100% 100%, rgba(94,234,212,0.16), transparent 60%);
      opacity: 0.7;
      pointer-events: none;
    }
    .header {
      position: relative;
      z-index: 2;
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 18px;
    }
    .title-block h1 {
      margin: 0;
      font-size: 1.4rem;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    .title-pill {
      font-size: 0.72rem;
      padding: 2px 8px;
      border-radius: 999px;
      background: rgba(34,197,94,0.14);
      border: 1px solid rgba(34,197,94,0.4);
      color: #bbf7d0;
    }
    .subtitle {
      margin: 4px 0 0;
      font-size: 0.85rem;
      color: #cbd5f5;
      opacity: 0.9;
    }
    .actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .btn {
      border-radius: 999px;
      border: 1px solid rgba(148,163,184,0.7);
      padding: 6px 14px;
      background: rgba(15,23,42,0.8);
      color: #e5e7eb;
      cursor: pointer;
      font-size: 0.8rem;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.18s ease;
    }
    .btn-primary {
      background: linear-gradient(135deg, #22c55e, #16a4dd);
      border-color: transparent;
      color: #0b1120;
      font-weight: 600;
    }
    .btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 8px 25px rgba(15,23,42,0.5);
    }
    .btn span { font-size: 1rem; }
    .layout {
      position: relative;
      z-index: 2;
      display: grid;
      grid-template-columns: 3fr 2fr;
      gap: 18px;
      margin-top: 10px;
    }
    @media (max-width: 800px) { .layout { grid-template-columns: 1fr; } }
    .timeline {
      position: relative;
      padding-left: 28px;
      margin-top: 10px;
    }
    .timeline::before {
      content: "";
      position: absolute;
      left: 10px;
      top: 10px;
      bottom: 10px;
      width: 2px;
      background: linear-gradient(to bottom, #38bdf8, transparent);
      opacity: 0.7;
    }
    .step {
      position: relative;
      margin-bottom: 14px;
      opacity: 0;
      transform: translateY(18px);
      animation: fadeUp 0.6s ease-out forwards;
    }
    .step-dot {
      position: absolute;
      left: -19px;
      top: 7px;
      width: 14px;
      height: 14px;
      border-radius: 999px;
      background: #0f172a;
      border: 2px solid #38bdf8;
      box-shadow: 0 0 0 4px rgba(56,189,248,0.2);
    }
    .step-headline {
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #a5b4fc;
      margin-bottom: 3px;
    }
    .step-title { font-size: 1rem; font-weight: 600; margin-bottom: 4px; }
    .step-desc { font-size: 0.85rem; color: #cbd5f5; }
    .step-badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.75rem;
      padding: 2px 8px;
      border-radius: 999px;
      background: rgba(15,23,42,0.9);
      border: 1px solid rgba(148,163,184,0.7);
      margin-top: 6px;
      color: #e5e7eb;
    }
    .step-badge span { font-size: 0.9rem; }
    .step:nth-child(1) { animation-delay: 0.2s; }
    .step:nth-child(2) { animation-delay: 0.6s; }
    .step:nth-child(3) { animation-delay: 1.0s; }
    .step:nth-child(4) { animation-delay: 1.4s; }
    .step:nth-child(5) { animation-delay: 1.8s; }
    .step:nth-child(6) { animation-delay: 2.2s; }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(18px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    .right-panel {
      border-radius: 18px;
      background: radial-gradient(circle at top left, rgba(56,189,248,0.15), transparent 55%),
                  radial-gradient(circle at bottom right, rgba(45,212,191,0.18), transparent 60%),
                  rgba(15,23,42,0.95);
      border: 1px solid rgba(148,163,184,0.5);
      padding: 14px 16px 16px;
      position: relative;
      overflow: hidden;
    }
    .mini-header {
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      color: #a5b4fc;
      margin-bottom: 4px;
    }
    .right-title {
      font-size: 0.95rem;
      margin: 0 0 6px;
    }
    .code-block {
      background: rgba(15,23,42,0.9);
      border-radius: 12px;
      padding: 10px 12px;
      font-family: "JetBrains Mono", ui-monospace, SFMono-Regular, Menlo,
      Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
      font-size: 0.75rem;
      color: #e5e7eb;
      border: 1px solid rgba(30,64,175,0.9);
      max-height: 220px;
      overflow: auto;
    }
    .legend { margin-top: 8px; font-size: 0.8rem; color: #e5e7eb; }
    .legend strong { color: #f97316; }

    .pulse-orbit {
      position: absolute;
      width: 140px;
      height: 140px;
      border-radius: 999px;
      border: 1px dashed rgba(148,163,184,0.6);
      top: -35px;
      right: -10px;
      opacity: 0.45;
      animation: spin 18s linear infinite;
      pointer-events: none;
    }
    .pulse-dot {
      position: absolute;
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: #22c55e;
      top: 10px;
      left: 50%;
      transform: translateX(-50%);
      box-shadow: 0 0 10px rgba(34,197,94,0.85);
    }

    @keyframes spin {
      from { transform: rotate(0deg); }
      to   { transform: rotate(360deg); }
    }
  </style>
</head>

<body>
  <div class="shell">
    <div class="header">
      <div class="title-block">
        <h1>
          Key Vault → App Service → SQL Flow
          <span class="title-pill">Animated Story</span>
        </h1>
        <p class="subtitle">
          Visualizing how your Flask app uses Managed Identity to pull a SQL connection string from Key Vault
          and insert records into Azure SQL.
        </p>
      </div>

      <div class="actions">
        <button class="btn btn-primary" id="replay">
          <span>⟳</span> Replay Animation
        </button>
      </div>
    </div>

    <div class="layout">
      <div class="timeline" id="timeline">
        <div class="step">
          <div class="step-dot"></div>
          <div class="step-headline">Step 1 · User</div>
          <div class="step-title">Browser hits the Web App</div>
          <div class="step-desc">
            User visits your App Service — HTTPS is terminated and the request is routed to Flask.
          </div>
          <div class="step-badge"><span>🌐</span> Browser → App Service</div>
        </div>

        <div class="step">
          <div class="step-dot"></div>
          <div class="step-headline">Step 2 · Flask</div>
          <div class="step-title">Flask runs index()</div>
          <div class="step-desc">
            The route calls <code>get_connection()</code> which starts the secure DB lookup workflow.
          </div>
          <div class="step-badge"><span>🐍</span> Python Flask</div>
        </div>

        <div class="step">
          <div class="step-dot"></div>
          <div class="step-headline">Step 3 · Managed Identity</div>
          <div class="step-title">Authentication without secrets</div>
          <div class="step-desc">
            App Service’s Managed Identity fetches a token from Entra ID.
          </div>
          <div class="step-badge"><span>🪪</span> Token Request</div>
        </div>

        <div class="step">
          <div class="step-dot"></div>
          <div class="step-headline">Step 4 · Key Vault</div>
          <div class="step-title">SQL connection string returned</div>
          <div class="step-desc">
            Flask retrieves <code>sql-conn-string</code> from Key Vault securely.
          </div>
          <div class="step-badge"><span>🔐</span> Secret Read</div>
        </div>

        <div class="step">
          <div class="step-dot"></div>
          <div class="step-headline">Step 5 · Database</div>
          <div class="step-title">pyodbc connects to Azure SQL</div>
          <div class="step-desc">
            A secure TLS connection is created using the cleaned ODBC string.
          </div>
          <div class="step-badge"><span>🗄️</span> SQL Connected</div>
        </div>

        <div class="step">
          <div class="step-dot"></div>
          <div class="step-headline">Step 6 · Insert + Query</div>
          <div class="step-title">Record added + List refreshed</div>
          <div class="step-desc">
            <code>INSERT</code> is executed on /add and <code>SELECT</code> refreshes the UI.
          </div>
          <div class="step-badge"><span>✅</span> Completed Flow</div>
        </div>
      </div>

      <div class="right-panel">
        <div class="pulse-orbit"><div class="pulse-dot"></div></div>
        <div class="mini-header">Code snippet</div>
        <h3 class="right-title">Simplified connection workflow</h3>

        <pre class="code-block">
DefaultAzureCredential → KeyVault → SQL Connection

Flask calls get_connection() →
  Managed Identity gets token →
    Key Vault returns SQL secret →
      Python builds ODBC string →
        pyodbc connects securely →
          / and /add routes execute SQL queries
        </pre>

        <div class="legend">
          <strong>Highlight:</strong> No passwords in code — Key Vault + Managed Identity handles security.
        </div>
      </div>
    </div>
  </div>

  <script>
      const replayBtn = document.getElementById("replay");
      replayBtn.addEventListener("click", () => {
          const timeline = document.getElementById("timeline");
          const clone = timeline.cloneNode(true);
          timeline.parentNode.replaceChild(clone, timeline);
      });
  </script>
</body>
</html>
    """

    return Response(html, mimetype="text/html")
