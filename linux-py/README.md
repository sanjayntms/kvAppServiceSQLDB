# Create a setup manually for the Azure batch task video
# 1) Create App service Linux-based OS - Python 3.1 runtime
   Enable MI
   Add SCM_DO_BUILD_DURING_DEPLOYMENT --> 1 in app settings
   Add KEY_VAULT_URI --->https://ntmsdevsecops-kv.vault.azure.net  # Change kv name as per your setup
   
# 2) Create KV - access policy or RBAC
   Assign RBAC/ access policy to App service name(MI enabled) 
   If RBAC based - Assign Key Vault Secrets User
   If access policy based, use get/list in secret permission
   Create secret sql-conn-string and add this:
   Server=tcp:kvsqlserverdemo.database.windows.net,1433; Database=db; Uid=sqladmin; Pwd=P@ssw0rd123#; Encrypt=yes; TrustServerCertificate=no; Connection Timeout=30;
# 3) Create PaaS Azure SQL DB - DTU - Std
# 4) Create the table in SQL DB
   CREATE TABLE DemoRecords (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100),
    CreatedAt DATETIME DEFAULT GETDATE()
    );
# 5) Open azcli cloud shell
   git clone repo ( app folder for Windows-based app service, linapp for Linux-based app service)
   ntms [ ~/kvAppServiceSQLDB/linapp ]$ zip -r linapp.zip .   # I assumed a Linux-based App service - App service plan - B1 
   linapp.zip created
   az webapp deploy --name ntmspy1 --resource-group python-rg --src-path app.zip   # Change app service name and rg name
   
