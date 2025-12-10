# app folder for windows based app service and linux-py ---for linux based app service- python 3.10 runtime
# kvAppServiceSQLDB - app -windows based app service, check/update following settings/issues if it is deployed using github actions. 
* App Service MI Issue with KV RBAC Permission - assign KV secret user RBAC
* Add table in SQL db 
   CREATE TABLE DemoRecords (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100),
    CreatedAt DATETIME DEFAULT GETDATE()
);
* Need to allow access from Azure services to sql database 
