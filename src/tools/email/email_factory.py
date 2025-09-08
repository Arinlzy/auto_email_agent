"""
Email client factory for creating appropriate email clients.

Provides a factory pattern implementation for creating email clients
based on provider type and configuration.
"""

import os
from typing import Optional, Dict, Any

from .base_email_client import BaseEmailClient
from .imap_smtp_client import IMAPSMTPClient
from .email_config import EmailConfigManager


class EmailFactory:
    """Factory for creating email clients based on provider type."""
    
    # Registry of available client types
    _client_registry = {
        'gmail': IMAPSMTPClient,    # Gmail统一使用IMAP/SMTP
        'outlook': IMAPSMTPClient,
        'yahoo': IMAPSMTPClient,
        'icloud': IMAPSMTPClient,
        'tju': IMAPSMTPClient,      # 天津大学邮箱
        'generic': IMAPSMTPClient,
        'imap': IMAPSMTPClient,  # Alias for generic IMAP/SMTP
    }
    
    @classmethod
    def create_client(
        cls, 
        provider: Optional[str] = None, 
        config_file: Optional[str] = None,
        **kwargs
    ) -> BaseEmailClient:
        """
        Create an email client for the specified provider.
        
        Args:
            provider: Email provider name (gmail, outlook, yahoo, etc.)
                     If None, attempts to detect from environment
            config_file: Optional custom configuration file
            **kwargs: Additional arguments passed to client constructor
            
        Returns:
            Configured email client instance
            
        Raises:
            ValueError: If provider is not supported or cannot be detected
        """
        # Auto-detect provider if not specified
        if provider is None:
            provider = cls._detect_provider_from_config(config_file)
        
        provider = provider.lower()
        
        # Get the appropriate client class
        if provider not in cls._client_registry:
            available = ', '.join(cls._client_registry.keys())
            raise ValueError(
                f"Unsupported email provider: {provider}. "
                f"Available providers: {available}"
            )
        
        client_class = cls._client_registry[provider]
        
        # Create client instance
        try:
            # All providers now use the same IMAP/SMTP client initialization
            return client_class(provider=provider, config_file=config_file, **kwargs)
                
        except Exception as e:
            raise ValueError(f"Failed to create {provider} email client: {e}")
    
    @classmethod
    def _detect_provider_from_config(cls, config_file: Optional[str] = None) -> str:
        """
        Detect email provider from configuration file.
        
        Args:
            config_file: Path to configuration file
            
        Returns:
            Detected provider name
            
        Raises:
            ValueError: If provider cannot be detected
        """
        if config_file:
            try:
                config_manager = EmailConfigManager(config_file)
                current_provider = config_manager.get_current_provider()
                if current_provider and current_provider in cls._client_registry:
                    return current_provider
            except Exception as e:
                print(f"Failed to detect provider from config file: {e}")
        
        # Default to gmail if detection fails
        print("Could not detect email provider from config, defaulting to gmail")
        return 'gmail'
    
    @classmethod
    def register_provider(
        cls, 
        provider_name: str, 
        client_class: type,
        override: bool = False
    ) -> None:
        """
        Register a custom email client provider.
        
        Args:
            provider_name: Name of the provider
            client_class: Email client class (must inherit from BaseEmailClient)
            override: Whether to override existing provider
            
        Raises:
            ValueError: If provider already exists and override is False
            TypeError: If client_class is not a BaseEmailClient subclass
        """
        if not issubclass(client_class, BaseEmailClient):
            raise TypeError("Client class must inherit from BaseEmailClient")
        
        provider_name = provider_name.lower()
        
        if provider_name in cls._client_registry and not override:
            raise ValueError(f"Provider '{provider_name}' already exists. Use override=True to replace.")
        
        cls._client_registry[provider_name] = client_class
        print(f"Registered email provider: {provider_name}")
    
    @classmethod
    def get_available_providers(cls) -> list:
        """
        Get list of available email providers.
        
        Returns:
            List of provider names
        """
        return list(cls._client_registry.keys())
    
    @classmethod
    def create_from_config(cls, config: Dict[str, Any]) -> BaseEmailClient:
        """
        Create email client from configuration dictionary.
        
        Args:
            config: Configuration dictionary with 'provider' key and other settings
            
        Returns:
            Configured email client
        """
        provider = config.get('provider', 'generic')
        config_file = config.get('config_file')
        
        # Remove factory-specific keys before passing to client
        client_config = {k: v for k, v in config.items() 
                        if k not in ('provider', 'config_file')}
        
        return cls.create_client(
            provider=provider,
            config_file=config_file,
            **client_config
        )
    
    @classmethod
    def test_provider_connection(cls, provider: str, config_file: Optional[str] = None) -> bool:
        """
        Test connection to an email provider.
        
        Args:
            provider: Provider name to test
            config_file: Optional configuration file
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            client = cls.create_client(provider, config_file)
            connected = client.connect()
            if connected:
                client.disconnect()
            return connected
        except Exception as e:
            print(f"Connection test failed for {provider}: {e}")
            return False


# Convenience functions for common use cases
def create_gmail_client(config_file: Optional[str] = None) -> IMAPSMTPClient:
    """Create a Gmail IMAP/SMTP client."""
    return EmailFactory.create_client('gmail', config_file)


def create_outlook_client(config_file: Optional[str] = None) -> IMAPSMTPClient:
    """Create an Outlook IMAP/SMTP client."""
    return EmailFactory.create_client('outlook', config_file)


def create_generic_client(provider: str = 'generic', config_file: Optional[str] = None) -> IMAPSMTPClient:
    """Create a generic IMAP/SMTP client."""
    return EmailFactory.create_client(provider, config_file)


def auto_create_client(config_file: Optional[str] = None) -> BaseEmailClient:
    """
    Automatically create the best email client based on environment.
    
    Args:
        config_file: Optional configuration file
        
    Returns:
        Auto-configured email client
    """
    return EmailFactory.create_client(config_file=config_file)