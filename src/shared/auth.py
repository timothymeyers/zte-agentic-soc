"""
Authentication module for Agentic SOC.

Implements Managed Identity authentication with fallback to service principal.
Follows FR-053: Managed Identity (recommended) OR service principals with least-privilege.
"""

import os
from typing import Optional

from azure.core.credentials import TokenCredential
from azure.identity import (
    AzureCliCredential,
    ChainedTokenCredential,
    DefaultAzureCredential,
    EnvironmentCredential,
    ManagedIdentityCredential,
)


def get_azure_credential(
    use_cli_fallback: bool = True, managed_identity_client_id: Optional[str] = None
) -> TokenCredential:
    """
    Get Azure credential using Managed Identity with fallbacks.

    Authentication chain (in order of preference):
    1. Managed Identity (recommended for production)
    2. Environment variables (service principal)
    3. Azure CLI (development only, if use_cli_fallback=True)

    Args:
        use_cli_fallback: If True, include Azure CLI in the chain (development).
                         Should be False in production.
        managed_identity_client_id: Optional client ID for user-assigned managed identity.
                                   If None, uses system-assigned managed identity.

    Returns:
        TokenCredential that can be used with Azure SDKs

    Environment Variables (for service principal fallback):
        AZURE_TENANT_ID: Azure tenant ID
        AZURE_CLIENT_ID: Service principal client ID
        AZURE_CLIENT_SECRET: Service principal secret

    Examples:
        >>> # Production: Use Managed Identity
        >>> credential = get_azure_credential(use_cli_fallback=False)
        
        >>> # Development: Allow CLI fallback
        >>> credential = get_azure_credential(use_cli_fallback=True)
        
        >>> # User-assigned managed identity
        >>> credential = get_azure_credential(
        ...     managed_identity_client_id="12345678-1234-1234-1234-123456789012"
        ... )
    """
    credentials = []

    # 1. Managed Identity (recommended for production)
    try:
        if managed_identity_client_id:
            # User-assigned managed identity
            managed_identity = ManagedIdentityCredential(client_id=managed_identity_client_id)
        else:
            # System-assigned managed identity
            managed_identity = ManagedIdentityCredential()
        credentials.append(managed_identity)
    except Exception:  # pylint: disable=broad-except
        # Managed Identity not available (expected in local development)
        pass

    # 2. Environment variables (service principal)
    try:
        env_credential = EnvironmentCredential()
        credentials.append(env_credential)
    except Exception:  # pylint: disable=broad-except
        pass

    # 3. Azure CLI (development only)
    if use_cli_fallback:
        try:
            cli_credential = AzureCliCredential()
            credentials.append(cli_credential)
        except Exception:  # pylint: disable=broad-except
            pass

    # If no credentials were added, fall back to DefaultAzureCredential
    if not credentials:
        return DefaultAzureCredential()

    # Return chained credential that tries each in order
    return ChainedTokenCredential(*credentials)


def get_project_credential() -> TokenCredential:
    """
    Get credential for Microsoft Foundry project operations.

    Uses environment variable to determine if CLI fallback should be enabled:
    - ENVIRONMENT=development: Enable CLI fallback
    - ENVIRONMENT=production: Managed Identity only

    Returns:
        TokenCredential configured based on environment
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    use_cli_fallback = environment == "development"

    # Get user-assigned managed identity client ID if specified
    client_id = os.getenv("AZURE_CLIENT_ID")

    return get_azure_credential(use_cli_fallback=use_cli_fallback, managed_identity_client_id=client_id)


def validate_authentication() -> bool:
    """
    Validate that authentication is working.

    Returns:
        True if authentication succeeds, False otherwise

    Example:
        >>> if validate_authentication():
        ...     print("Authentication successful")
        ... else:
        ...     print("Authentication failed")
    """
    try:
        credential = get_project_credential()
        # Try to get a token for Azure Management API
        token = credential.get_token("https://management.azure.com/.default")
        return token is not None
    except Exception:  # pylint: disable=broad-except
        return False


# =============================================================================
# Convenience Functions
# =============================================================================


def get_subscription_id() -> str:
    """
    Get Azure subscription ID from environment.

    Returns:
        Subscription ID

    Raises:
        ValueError: If AZURE_SUBSCRIPTION_ID is not set
    """
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        raise ValueError(
            "AZURE_SUBSCRIPTION_ID environment variable is required. "
            "Please set it in your .env file or environment."
        )
    return subscription_id


def get_resource_group() -> str:
    """
    Get Azure resource group name from environment.

    Returns:
        Resource group name

    Raises:
        ValueError: If AZURE_RESOURCE_GROUP is not set
    """
    resource_group = os.getenv("AZURE_RESOURCE_GROUP")
    if not resource_group:
        raise ValueError(
            "AZURE_RESOURCE_GROUP environment variable is required. "
            "Please set it in your .env file or environment."
        )
    return resource_group


def get_project_endpoint() -> str:
    """
    Get Microsoft Foundry project endpoint from environment.

    Returns:
        Project endpoint URL

    Raises:
        ValueError: If AZURE_AI_FOUNDRY_PROJECT_ENDPOINT is not set
    """
    endpoint = os.getenv("AZURE_AI_FOUNDRY_PROJECT_ENDPOINT")
    if not endpoint:
        raise ValueError(
            "AZURE_AI_FOUNDRY_PROJECT_ENDPOINT environment variable is required. "
            "Please set it in your .env file or environment."
        )
    return endpoint


def get_openai_deployment() -> str:
    """
    Get Azure OpenAI deployment name from environment.

    Returns:
        Deployment name (e.g., 'gpt-4.1-mini')

    Raises:
        ValueError: If AZURE_OPENAI_DEPLOYMENT_NAME is not set
    """
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    if not deployment:
        raise ValueError(
            "AZURE_OPENAI_DEPLOYMENT_NAME environment variable is required. "
            "Please set it in your .env file or environment."
        )
    return deployment
