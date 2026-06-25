// Foundry Helpdesk — infrastructure (SKELETON).
//
// ⚠️ This is a placeholder, NOT a verified deployable template. The Foundry
// resource provider surface (account/project/model deployment, Foundry IQ,
// memory store) moves fast. DO NOT run `azd up` against this without first
// verifying every resource type, apiVersion, and property against:
//   https://learn.microsoft.com/azure/templates/microsoft.cognitiveservices
//   https://github.com/microsoft-foundry/foundry-samples (infra/ examples)
//
// TODO: verify resource types + apiVersions below before provisioning.

targetScope = 'resourceGroup'

@description('Base name for resources')
param name string = 'helpdesk'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Model deployment name surfaced to the app as FOUNDRY_MODEL')
param modelDeploymentName string = 'gpt-4.1-mini'

// TODO: verify Microsoft.CognitiveServices Foundry account/project resource
// shape. The following is illustrative scaffolding, not a confirmed schema.
//
// resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
//   name: '${name}-foundry'
//   location: location
//   kind: 'AIServices'
//   sku: { name: 'S0' }
//   properties: { allowProjectManagement: true }
// }
//
// resource project '.../projects@...' = { ... }       // Foundry project
// resource model '.../deployments@...' = { ... }       // gpt-4.1-mini deployment
// resource appInsights 'Microsoft.Insights/components@2020-02-02' = { ... }

// Outputs consumed by azd -> app env (FOUNDRY_PROJECT_ENDPOINT / FOUNDRY_MODEL).
// TODO: wire these to the real project endpoint once resources above are defined.
output FOUNDRY_PROJECT_ENDPOINT string = '' // = project.properties.endpoint
output FOUNDRY_MODEL string = modelDeploymentName
