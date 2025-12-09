# kvAppServiceSQLDB
* App Service MI Issue with KV RBAC Permission - assign KV secret user RBAC
* Add table in SQL db 
   CREATE TABLE DemoRecords (
    Id INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100),
    CreatedAt DATETIME DEFAULT GETDATE()
);
* Need to allow access from Azure services to sql database 
