#!/bin/bash

RG=sqlkv-rg
LOC=centralindia
APP=ntms-sqlkv-webapp-demo
PLAN=sqlkv-plan
KV=ntms-sqlkv-demo-v1
SQL=ntmssqlkvserver
DB=demoDB
PASSWORD="P@ssw0rd123#"

echo "Creating Resource Group..."
az group create -n $RG -l $LOC

echo "Creating SQL Server..."
az sql server create -n $SQL -g $RG -l $LOC -u sqladmin -p $PASSWORD

echo "Creating SQL DB..."
az sql db create -n $DB -s $SQL -g $RG --service-objective Basic

echo "Creating Key Vault..."
az keyvault create -n $KV -g $RG -l $LOC

CONN="Server=tcp:$SQL.database.windows.net,1433;Database=$DB;User ID=sqladmin;Password=$PASSWORD;Encrypt=true;"
az keyvault secret set --vault-name $KV --name SqlConnString --value "$CONN"

echo "Creating App Service Plan..."
az appservice plan create -g $RG -n $PLAN --sku B1 --is-linux

echo "Creating Web App..."
az webapp create -g $RG -p $PLAN -n $APP --runtime "PYTHON:3.10"

echo "Assigning Managed Identity..."
APP_ID=$(az webapp identity assign -g $RG -n $APP --query principalId -o tsv)

echo "Adding Key Vault access policy..."
az keyvault set-policy -n $KV --object-id $APP_ID --secret-permissions get list

echo "Adding Key Vault reference to App Settings..."
SECRET_URI=$(az keyvault secret show --vault-name $KV --name SqlConnString --query id -o tsv)

az webapp config appsettings set -g $RG -n $APP \
  --settings SQL_CONN="@Microsoft.KeyVault(SecretUri=$SECRET_URI)"

echo "Done!"
