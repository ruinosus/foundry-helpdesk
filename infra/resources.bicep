// Foundry Helpdesk — resource-group-scoped resources.
//
// Foundry account (kind AIServices, project management on) + project +
// gpt-4.1-mini deployment + "Azure AI User" data-plane role for the caller.
//
// apiVersions/types verified against microsoft-foundry/foundry-samples 00-basic
// and learn.microsoft.com/azure/foundry/how-to/create-resource-template.

@description('Primary location for all resources.')
param location string

@description('Tags applied to every resource.')
param tags object = {}

@description('Short unique token to make the (globally-unique) account name unique.')
param resourceToken string

@description('Principal granted Azure AI User (data-plane). Empty string skips the assignment.')
param principalId string = ''

@description('Model deployment name (must match the app FOUNDRY_MODEL).')
param modelDeploymentName string = 'gpt-4.1-mini'

@description('Model version for gpt-4.1-mini.')
param modelVersion string = '2025-04-14'

@description('Deployment capacity in thousands of tokens-per-minute. Lower if you hit quota.')
param modelCapacity int = 30

// Account name doubles as customSubDomainName, which must be globally unique.
var accountName = 'aif-helpdesk-${resourceToken}'
var projectName = 'helpdesk-concierge'

// "Azure AI User" (renamed "Foundry User", same GUID) — data-plane inference with Entra ID.
// Owner does NOT grant data-plane access, so without this you'd get 401 at inference time.
var azureAiUserRoleId = '53ca6127-db72-4b80-b1b0-d745d6d5456d'

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  tags: tags
  kind: 'AIServices'
  sku: { name: 'S0' }
  identity: { type: 'SystemAssigned' }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  name: projectName
  parent: account
  location: location
  tags: tags
  identity: { type: 'SystemAssigned' }
  properties: {}
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: account
  name: modelDeploymentName
  sku: { name: 'GlobalStandard', capacity: modelCapacity }
  properties: {
    model: {
      name: modelDeploymentName
      format: 'OpenAI'
      version: modelVersion
    }
  }
}

resource aiUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(principalId)) {
  name: guid(account.id, principalId, azureAiUserRoleId)
  scope: account
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', azureAiUserRoleId)
    principalId: principalId
    principalType: 'User'
  }
}

// Project endpoint in the AIProjectClient form. If FoundryChatClient rejects it
// at runtime, try AZURE_AI_ACCOUNT_ENDPOINT instead (see README troubleshooting).
output FOUNDRY_PROJECT_ENDPOINT string = 'https://${accountName}.services.ai.azure.com/api/projects/${projectName}'
output AZURE_AI_ACCOUNT_ENDPOINT string = account.properties.endpoint
output FOUNDRY_MODEL string = modelDeploymentName
