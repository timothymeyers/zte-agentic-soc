"""
Authentication module using Azure Managed Identity.

This module provides Azure authentication using DefaultAzureCredential
which supports multiple authentication methods in the following order:
1. Environment variables (for local development)
2. Managed Identity (for Azure deployments)
3. Azure CLI (for local development)
4. Visual Studio Code
5. Azure PowerShell
"""

import logging
from typing import Optional

from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.core.credentials import TokenCredential


logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Manages Azure authentication using Managed Identity or service principals."""
    
    def __init__(
        self,
        tenant_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """
        Initialize authentication manager.
        
        Args:
            tenant_id: Azure tenant ID (optional, for service principal auth)
            client_id: Application client ID (optional, for service principal auth)
            client_secret: Application client secret (optional, for service principal auth)
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._credential: Optional[TokenCredential] = None
    
    def get_credential(self) -> TokenCredential:
        """
        Get Azure credential for authentication.
        
        Returns:
            TokenCredential: Azure credential object
        
        Note:
            Prefers DefaultAzureCredential (Managed Identity) but falls back
            to ClientSecretCredential if service principal credentials are provided.
        """
        if self._credential is not None:
            return self._credential
        
        # If service principal credentials are provided, use them
        if all([self.tenant_id, self.client_id, self.client_secret]):
            logger.info("Using service principal authentication")
            self._credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )
        else:
            # Otherwise, use DefaultAzureCredential (Managed Identity preferred)
            logger.info("Using DefaultAzureCredential (Managed Identity or fallback)")
            self._credential = DefaultAzureCredential()
        
        return self._credential
    
    def get_token(self, scopes: list[str]) -> str:
        """
        Get access token for specified scopes.
        
        Args:
            scopes: List of OAuth2 scopes to request
        
        Returns:
            str: Access token
        """
        credential = self.get_credential()
        token = credential.get_token(*scopes)
        return token.token


# Global authentication manager instance
_auth_manager: Optional[AuthenticationManager] = None


def initialize_auth(
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> AuthenticationManager:
    """
    Initialize global authentication manager.
    
    Args:
        tenant_id: Azure tenant ID (optional)
        client_id: Application client ID (optional)
        client_secret: Application client secret (optional)
    
    Returns:
        AuthenticationManager: Initialized authentication manager
    """
    global _auth_manager
    _auth_manager = AuthenticationManager(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    logger.info("Authentication manager initialized")
    return _auth_manager


def get_auth_manager() -> AuthenticationManager:
    """
    Get global authentication manager instance.
    
    Returns:
        AuthenticationManager: Global authentication manager
    
    Raises:
        RuntimeError: If authentication manager not initialized
    """
    if _auth_manager is None:
        raise RuntimeError(
            "Authentication manager not initialized. "
            "Call initialize_auth() first."
        )
    return _auth_manager


def get_credential() -> TokenCredential:
    """
    Get Azure credential from global authentication manager.
    
    Returns:
        TokenCredential: Azure credential object
    """
    return get_auth_manager().get_credential()
