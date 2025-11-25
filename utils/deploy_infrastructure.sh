#!/bin/bash
# Deployment script for Agentic SOC infrastructure
# Usage: ./deploy_infrastructure.sh <environment>
# Example: ./deploy_infrastructure.sh dev

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: Environment parameter is required${NC}"
    echo "Usage: ./deploy_infrastructure.sh <environment>"
    echo "Example: ./deploy_infrastructure.sh dev"
    exit 1
fi

ENVIRONMENT=$1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(dirname "$SCRIPT_DIR")/infra"
PARAMETER_FILE="$INFRA_DIR/parameters/$ENVIRONMENT.parameters.json"
MAIN_TEMPLATE="$INFRA_DIR/main.bicep"

# Validate environment
if [ "$ENVIRONMENT" != "dev" ] && [ "$ENVIRONMENT" != "prod" ]; then
    echo -e "${RED}Error: Environment must be 'dev' or 'prod'${NC}"
    exit 1
fi

# Check if parameter file exists
if [ ! -f "$PARAMETER_FILE" ]; then
    echo -e "${RED}Error: Parameter file not found: $PARAMETER_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Agentic SOC Infrastructure Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Environment: $ENVIRONMENT"
echo "Parameter File: $PARAMETER_FILE"
echo "Main Template: $MAIN_TEMPLATE"
echo ""

# Check if logged in to Azure
echo -e "${YELLOW}Checking Azure login...${NC}"
if ! az account show &> /dev/null; then
    echo -e "${RED}Error: Not logged in to Azure. Please run 'az login'${NC}"
    exit 1
fi

SUBSCRIPTION_NAME=$(az account show --query name -o tsv)
echo -e "${GREEN}✓ Logged in to Azure${NC}"
echo "  Subscription: $SUBSCRIPTION_NAME"
echo ""

# Get resource group name from parameters
RESOURCE_GROUP=$(jq -r '.parameters.baseName.value' "$PARAMETER_FILE")-rg-$ENVIRONMENT

# Create resource group if it doesn't exist
echo -e "${YELLOW}Checking resource group: $RESOURCE_GROUP${NC}"
if ! az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    echo -e "${YELLOW}Creating resource group...${NC}"
    LOCATION=$(jq -r '.parameters.location.value' "$PARAMETER_FILE")
    az group create --name "$RESOURCE_GROUP" --location "$LOCATION"
    echo -e "${GREEN}✓ Resource group created${NC}"
else
    echo -e "${GREEN}✓ Resource group exists${NC}"
fi
echo ""

# Validate Bicep template
echo -e "${YELLOW}Validating Bicep template...${NC}"
if az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$MAIN_TEMPLATE" \
    --parameters "@$PARAMETER_FILE" \
    --output none; then
    echo -e "${GREEN}✓ Template validation passed${NC}"
else
    echo -e "${RED}✗ Template validation failed${NC}"
    exit 1
fi
echo ""

# Deploy infrastructure
echo -e "${YELLOW}Deploying infrastructure...${NC}"
echo "This may take 10-15 minutes..."
echo ""

DEPLOYMENT_NAME="agentic-soc-$ENVIRONMENT-$(date +%Y%m%d-%H%M%S)"

if az deployment group create \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --template-file "$MAIN_TEMPLATE" \
    --parameters "@$PARAMETER_FILE" \
    --output table; then
    echo ""
    echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Deployment failed${NC}"
    exit 1
fi
echo ""

# Display deployment outputs
echo -e "${YELLOW}Deployment Outputs:${NC}"
az deployment group show \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.outputs \
    --output table
echo ""

# Save outputs to file
OUTPUTS_FILE="$INFRA_DIR/outputs/$ENVIRONMENT-outputs.json"
mkdir -p "$INFRA_DIR/outputs"
az deployment group show \
    --name "$DEPLOYMENT_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --query properties.outputs \
    --output json > "$OUTPUTS_FILE"
echo -e "${GREEN}✓ Outputs saved to: $OUTPUTS_FILE${NC}"
echo ""

# Display next steps
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Configure environment variables from outputs"
echo "2. Run utils/setup_ai_search.py to create indexes"
echo "3. Run utils/setup_cosmos_db.py to verify collections"
echo "4. Deploy container images to Container Apps"
echo ""
echo -e "${YELLOW}To view resources in Azure Portal:${NC}"
echo "https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/$RESOURCE_GROUP"
echo ""
