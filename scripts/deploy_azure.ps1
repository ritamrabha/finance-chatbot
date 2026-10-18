<#
  Deploy AI Invoice Assistant to Azure (PowerShell, Windows).

  Prerequisites: Azure CLI installed and `az login` done.
  Run from the repo root:   .\scripts\deploy_azure.ps1

  The script asks before every step that creates resources.
  Secrets are typed into hidden prompts and passed straight to Azure; they are
  never written to disk or to git.
#>
param(
    [string]$ResourceGroup = "rg-invoice-assistant",
    [string]$Location = "centralindia",
    [ValidateSet("F1", "B1")] [string]$Sku = "F1",
    [string]$LlmBaseUrl = "https://api.groq.com/openai/v1",
    [string]$LlmModel = "llama-3.3-70b-versatile"
)
$ErrorActionPreference = "Stop"
if (Test-Path "C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin") {
    $env:Path += ";C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin"
}

function Confirm-Step($msg) {
    $a = Read-Host "$msg  Continue? (y/n)"
    if ($a -ne "y") { Write-Host "Stopped."; exit 1 }
}
function Read-Secret($prompt) {
    $s = Read-Host $prompt -AsSecureString
    return [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($s))
}

Write-Host "Subscription:" (az account show --query name -o tsv)

Confirm-Step "STEP 1: create resource group '$ResourceGroup' in $Location (free)."
az group create -n $ResourceGroup -l $Location -o none

Write-Host ""
Write-Host "STEP 2 creates: Document Intelligence F0 (free), Azure SQL free-offer DB (free, auto-pauses),"
Write-Host "  Storage account (cents/month), Key Vault (cents/month), App Insights + Log Analytics (free tier, 1 GB/day cap),"
Write-Host "  App Service plan $Sku $(if ($Sku -eq 'B1') {'(PAID ~US$13/month from student credit)'} else {'(free)'})."
Confirm-Step "Create these resources?"

$sqlAdminPw = Read-Secret "Choose SQL admin password (12+ chars, upper/lower/digit/symbol)"
$sqlWriterPw = Read-Secret "Choose SQL app-writer password"
$sqlReaderPw = Read-Secret "Choose SQL chatbot-reader password"
$llmKey = Read-Secret "Paste your LLM API key"
Write-Host "Create the app login hash now (python scripts/hash_password.py) and paste ONLY the hash part."
$appHash = Read-Host "APP_PASSWORD_HASH"

$params = @{
    location = @{ value = $Location }; appServiceSku = @{ value = $Sku }
    sqlAdminPassword = @{ value = $sqlAdminPw }; sqlWriterPassword = @{ value = $sqlWriterPw }
    sqlReaderPassword = @{ value = $sqlReaderPw }; llmApiKey = @{ value = $llmKey }
    llmBaseUrl = @{ value = $LlmBaseUrl }; llmModel = @{ value = $LlmModel }
    appPasswordHash = @{ value = $appHash }
}
# Parameters go through a temp file that is deleted right after (avoids secrets in the command line / history)
$tmp = New-TemporaryFile
@{ '$schema' = "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#"; contentVersion = "1.0.0.0"; parameters = $params } |
    ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $tmp
try {
    $out = az deployment group create -g $ResourceGroup -f infra/main.bicep -p "@$tmp" --query properties.outputs -o json | ConvertFrom-Json
} finally { Remove-Item $tmp -Force }

$web = $out.webAppName.value
$sqlFqdn = $out.sqlServerFqdn.value
$sqlName = $out.sqlServerName.value
Write-Host "Deployed. Web app: $web  SQL: $sqlFqdn"

Confirm-Step "STEP 3: allow YOUR current IP through the SQL firewall and create tables + least-privilege users (free)."
$myIp = (Invoke-RestMethod -Uri "https://api.ipify.org")
az sql server firewall-rule create -g $ResourceGroup -s $sqlName -n "setup-client" --start-ip-address $myIp --end-ip-address $myIp -o none
$env:AZURE_SQL_SERVER = $sqlFqdn; $env:AZURE_SQL_DATABASE = "invoicedb"
$env:AZURE_SQL_ADMIN_USER = "sqladminuser"; $env:AZURE_SQL_ADMIN_PASSWORD = $sqlAdminPw
$env:AZURE_SQL_WRITER_PASSWORD = $sqlWriterPw; $env:AZURE_SQL_READER_PASSWORD = $sqlReaderPw
.\.venv\Scripts\python.exe scripts\setup_azure_sql.py
Remove-Item Env:AZURE_SQL_ADMIN_PASSWORD, Env:AZURE_SQL_WRITER_PASSWORD, Env:AZURE_SQL_READER_PASSWORD

Confirm-Step "STEP 4: build Vue.js frontend and upload code to App Service (free)."
Write-Host "Building Vue.js production bundle..."
npm run build
Write-Host "Creating deployment archive with Vue.js frontend and server..."
Compress-Archive -Path dist, server.py, app, requirements.txt, samples -DestinationPath deploy.zip -Force
az webapp deploy -g $ResourceGroup -n $web --src-path deploy.zip --type zip -o none
Remove-Item deploy.zip -Force

Write-Host ""
Write-Host "Done. Open: $($out.webAppUrl.value)"
Write-Host "First start can take 2-4 minutes (installing packages). Then sign in and use 'Demo controls > Reset to sample data'."
