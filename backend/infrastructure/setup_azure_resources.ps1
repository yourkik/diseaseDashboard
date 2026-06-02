param (
    [string]$SubscriptionId = "27db5ec6-d206-4028-b5e1-6004dca5eeef",
    [string]$Location = "koreacentral",
    [string]$ResourceGroupName = "3dt-final-team5",
    [string]$Prefix = "disease-ai",
    [string]$HubName = "$Prefix-hub",
    [string]$ProjectName = "$Prefix-project",
    [string]$OpenAIName = "$Prefix-openai",
    [string]$BingSearchName = "$Prefix-bing"
)

Write-Host "========================================="
Write-Host " Azure AI Foundry Resource Provisioning"
Write-Host "========================================="

# Validate inputs
if ([string]::IsNullOrWhiteSpace($SubscriptionId)) {
    $SubscriptionId = Read-Host "Enter your Azure Subscription ID"
}
if ([string]::IsNullOrWhiteSpace($ResourceGroupName)) {
    $ResourceGroupName = Read-Host "Enter your existing Resource Group Name"
}

# Login check
$account = az account show 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Please login to Azure CLI first. Running 'az login'..."
    az login
}

Write-Host "Setting subscription to $SubscriptionId..."
az account set --subscription $SubscriptionId

Write-Host "Ensuring resource group exists: $ResourceGroupName in $Location..."
az group create --name $ResourceGroupName --location $Location -o none

Write-Host "Adding/Updating 'ml' extension for Azure AI CLI..."
az extension add --name ml --upgrade -y -o none

Write-Host "1. Creating Azure AI Hub: $HubName ..."
az ml workspace create --kind hub --name $HubName --resource-group $ResourceGroupName --location $Location -o none

Write-Host "2. Creating Azure AI Project: $ProjectName ..."
$HubId = "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.MachineLearningServices/workspaces/$HubName"
az ml workspace create --kind project --name $ProjectName --hub-id $HubId --resource-group $ResourceGroupName --location $Location -o none

Write-Host "3. Creating Azure OpenAI Resource: $OpenAIName ..."
az cognitiveservices account create --name $OpenAIName --resource-group $ResourceGroupName --location $Location --kind OpenAI --sku S0 --custom-domain $OpenAIName -o none

Write-Host "4. Deploying gpt-4o model to OpenAI ..."
az cognitiveservices account deployment create `
    --name $OpenAIName `
    --resource-group $ResourceGroupName `
    --deployment-name "gpt-4o" `
    --model-name "gpt-4o" `
    --model-version "2024-05-13" `
    --model-format "OpenAI" `
    --sku-capacity 1 `
    --sku-name "Standard" -o none

Write-Host "5. Creating Bing Search v7 Resource: $BingSearchName ..."
az cognitiveservices account create --name $BingSearchName --resource-group $ResourceGroupName --location "global" --kind Bing.Search.v7 --sku S1 -o none

# Retrieve endpoint
Write-Host "Retrieving Project Endpoint..."
$DiscoveryUrl = az ml workspace show --name $ProjectName --resource-group $ResourceGroupName --query discovery_url -o tsv
# AI Foundry API Project endpoint is usually the discovery URL. 
# But let's construct the direct project endpoint.
$ProjectEndpoint = "https://$Location.api.azureml.ms/mlflow/v1.0/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.MachineLearningServices/workspaces/$ProjectName"
# Wait, the v2 AI Project endpoint is usually: https://<location>.api.azureml.ms/ext/project/subscriptions/...
# For simplicity, we can also instruct the user to check the portal or use the standard pattern.
# According to azure-ai-projects, it looks like: https://<domain>.services.ai.azure.com/api/projects/<ProjectName>
$ProjectEndpoint = az ml workspace show --name $ProjectName --resource-group $ResourceGroupName --query "discovery_url" -o tsv

Write-Host "6. Assigning RBAC Roles (Azure AI Developer) to current user ..."
$UserId = (az ad signed-in-user show --query id -o tsv)
az role assignment create --role "Azure AI Developer" --assignee $UserId --scope "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.MachineLearningServices/workspaces/$ProjectName" -o none
az role assignment create --role "Cognitive Services OpenAI User" --assignee $UserId --scope "/subscriptions/$SubscriptionId/resourceGroups/$ResourceGroupName/providers/Microsoft.CognitiveServices/accounts/$OpenAIName" -o none

Write-Host "========================================="
Write-Host " Provisioning Complete!"
Write-Host "========================================="
Write-Host "Next Steps:"
Write-Host "1. In Azure AI Studio (AI Foundry), open your project '$ProjectName'."
Write-Host "2. Go to 'Management' -> 'Connected resources' and ensure your Azure OpenAI and Bing Search are added as connections."
Write-Host "3. Update your .env file with the following:"
Write-Host ""
Write-Host "PROJECT_ENDPOINT=""$ProjectEndpoint"""
Write-Host "AZURE_OPENAI_DEPLOYMENT_NAME=""gpt-4o"""
Write-Host "BING_CONNECTION_NAME=""GroundingBingSearch"""
Write-Host ""
Write-Host "========================================="

# Generate .env file in the backend directory
$envPath = Join-Path $PSScriptRoot "..\.env"
$envContent = @"
# Azure AI Foundry 연동 정보
PROJECT_ENDPOINT="$ProjectEndpoint"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o"
BING_CONNECTION_NAME="GroundingBingSearch"

# 질병관리청 API KEY (KDCA_TOKEN)
KDCA_TOKEN="YOUR_KDCA_API_KEY_HERE"
"@

Set-Content -Path $envPath -Value $envContent -Encoding UTF8
Write-Host "Generated .env file at: $envPath"
