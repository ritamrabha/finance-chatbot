// AI Invoice Assistant - all Azure resources in one file.
//
// Deploy (from the repo root, after `az login`):
//   az group create -n rg-invoice-assistant -l centralindia
//   az deployment group create -g rg-invoice-assistant -f infra/main.bicep -p infra/main.parameters.json
//
// Cost notes (Azure for Students):
//   Document Intelligence F0 ........ free (500 pages/month)
//   Azure SQL Database free offer ... free (100k vCore-seconds + 32 GB / month, auto-pauses at the limit)
//   App Service plan F1 ............. free (60 CPU-minutes/day). B1 ~ US$13/month if you need speed.
//   Storage account (LRS) ........... a few cents/month at demo volume
//   Key Vault (standard) ............ ~US$0.03 per 10,000 operations
//   Application Insights ............ first 5 GB/month of logs free

targetScope = 'resourceGroup'

@description('Azure region. Azure for Students limits which regions are allowed; centralindia usually works.')
param location string = resourceGroup().location

@description('Short lowercase name used to build resource names.')
@maxLength(12)
param prefix string = 'invoiceai'

@description('App Service plan tier: F1 (free) or B1 (paid, ~US$13/month, faster, Always On).')
@allowed(['F1', 'B1'])
param appServiceSku string = 'F1'

@description('SQL Server admin login (used only for setup).')
param sqlAdminLogin string = 'sqladminuser'

@secure()
@description('SQL Server admin password.')
param sqlAdminPassword string

@secure()
@description('Password for the app writer SQL user (created by scripts/setup_azure_sql.py).')
param sqlWriterPassword string

@secure()
@description('Password for the chatbot READ-ONLY SQL user.')
param sqlReaderPassword string

@secure()
@description('LLM API key (Groq or xAI).')
param llmApiKey string

param llmBaseUrl string = 'https://api.groq.com/openai/v1'
param llmModel string = 'llama-3.3-70b-versatile'

param appUsername string = 'admin'

@secure()
@description('Output of scripts/hash_password.py (the hash, not the password).')
param appPasswordHash string

var suffix = uniqueString(resourceGroup().id)
var names = {
  logs: '${prefix}-logs-${suffix}'
  appi: '${prefix}-appi-${suffix}'
  storage: take(toLower('${prefix}st${suffix}'), 24)
  docintel: '${prefix}-di-${suffix}'
  sqlServer: '${prefix}-sql-${suffix}'
  sqlDb: 'invoicedb'
  keyVault: take('${prefix}-kv-${suffix}', 24)
  plan: '${prefix}-plan-${suffix}'
  web: '${prefix}-web-${suffix}'
}

// ---------------- Monitoring ----------------
resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: names.logs
  location: location
  properties: {
    sku: { name: 'PerGB2018' }
    retentionInDays: 30
    workspaceCapping: { dailyQuotaGb: 1 } // hard cap so logs can never run up a bill
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: names.appi
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

// ---------------- Blob Storage ----------------
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: names.storage
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
  properties: {
    minimumTlsVersion: 'TLS1_2'
    allowBlobPublicAccess: false   // invoices are never publicly readable
    supportsHttpsTrafficOnly: true
    accessTier: 'Hot'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource container 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'invoices'
  properties: { publicAccess: 'None' }
}

// ---------------- Document Intelligence (free tier) ----------------
resource docIntel 'Microsoft.CognitiveServices/accounts@2024-10-01' = {
  name: names.docintel
  location: location
  kind: 'FormRecognizer'
  sku: { name: 'F0' }
  properties: {
    customSubDomainName: names.docintel
    publicNetworkAccess: 'Enabled'
  }
}

// ---------------- Azure SQL Database (free offer) ----------------
resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: names.sqlServer
  location: location
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlDb 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: names.sqlDb
  location: location
  sku: { name: 'GP_S_Gen5_2', tier: 'GeneralPurpose' }   // serverless
  properties: {
    useFreeLimit: true                         // the "free offer"
    freeLimitExhaustionBehavior: 'AutoPause'   // pause instead of billing when the free amount runs out
    autoPauseDelay: 60
    minCapacity: json('0.5')
    maxSizeBytes: 34359738368                  // 32 GB
  }
}

// Lets other Azure services (our App Service) reach the server. Access still requires a SQL login.
resource sqlAllowAzure 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: { startIpAddress: '0.0.0.0', endIpAddress: '0.0.0.0' }
}

// ---------------- Key Vault + secrets ----------------
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: names.keyVault
  location: location
  properties: {
    tenantId: subscription().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}

var secrets = {
  'LLM-API-KEY': llmApiKey
  'APP-PASSWORD-HASH': appPasswordHash
  'DOCINTEL-KEY': docIntel.listKeys().key1
  'STORAGE-CONNECTION-STRING': 'DefaultEndpointsProtocol=https;AccountName=${storage.name};AccountKey=${storage.listKeys().keys[0].value};EndpointSuffix=${environment().suffixes.storage}'
  'SQL-WRITER-PASSWORD': sqlWriterPassword
  'SQL-READER-PASSWORD': sqlReaderPassword
}

resource kvSecrets 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = [for s in items(secrets): {
  parent: kv
  name: s.key
  properties: { value: s.value }
}]

func kvRef(vaultName string, secretName string) string =>
  '@Microsoft.KeyVault(VaultName=${vaultName};SecretName=${secretName})'

// ---------------- App Service ----------------
resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: names.plan
  location: location
  sku: { name: appServiceSku }
  kind: 'linux'
  properties: { reserved: true }
}

resource web 'Microsoft.Web/sites@2023-12-01' = {
  name: names.web
  location: location
  identity: { type: 'SystemAssigned' }   // managed identity: lets the app read Key Vault without a password
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    keyVaultReferenceIdentity: 'SystemAssigned'
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.11'
      appCommandLine: 'python -m streamlit run streamlit_app.py --server.port 8000 --server.address 0.0.0.0'
      webSocketsEnabled: true          // Streamlit needs WebSockets
      alwaysOn: appServiceSku != 'F1'  // not available on the free tier
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: [
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT', value: 'true' }
        { name: 'WEBSITES_PORT', value: '8000' }
        { name: 'LLM_BASE_URL', value: llmBaseUrl }
        { name: 'LLM_MODEL', value: llmModel }
        { name: 'LLM_API_KEY', value: kvRef(kv.name, 'LLM-API-KEY') }
        { name: 'APP_USERNAME', value: appUsername }
        { name: 'APP_PASSWORD_HASH', value: kvRef(kv.name, 'APP-PASSWORD-HASH') }
        { name: 'AZURE_DOCINTEL_ENDPOINT', value: docIntel.properties.endpoint }
        { name: 'AZURE_DOCINTEL_KEY', value: kvRef(kv.name, 'DOCINTEL-KEY') }
        { name: 'AZURE_STORAGE_CONNECTION_STRING', value: kvRef(kv.name, 'STORAGE-CONNECTION-STRING') }
        { name: 'AZURE_STORAGE_CONTAINER', value: 'invoices' }
        { name: 'AZURE_SQL_SERVER', value: sqlServer.properties.fullyQualifiedDomainName }
        { name: 'AZURE_SQL_DATABASE', value: sqlDb.name }
        { name: 'AZURE_SQL_WRITER_USER', value: 'invoice_app_writer' }
        { name: 'AZURE_SQL_WRITER_PASSWORD', value: kvRef(kv.name, 'SQL-WRITER-PASSWORD') }
        { name: 'AZURE_SQL_READER_USER', value: 'invoice_chat_reader' }
        { name: 'AZURE_SQL_READER_PASSWORD', value: kvRef(kv.name, 'SQL-READER-PASSWORD') }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsights.properties.ConnectionString }
      ]
    }
  }
}

// Give the web app permission to READ secrets (and nothing else) in Key Vault
var kvSecretsUserRole = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
resource kvAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: kv
  name: guid(kv.id, web.id, kvSecretsUserRole)
  properties: {
    roleDefinitionId: kvSecretsUserRole
    principalId: web.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

output webAppName string = web.name
output webAppUrl string = 'https://${web.properties.defaultHostName}'
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output sqlServerName string = sqlServer.name
output keyVaultName string = kv.name
output docIntelEndpoint string = docIntel.properties.endpoint
output storageAccountName string = storage.name
