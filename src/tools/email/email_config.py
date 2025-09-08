"""
Email configuration management for different providers.

Handles loading and managing email provider configurations including
server settings, authentication methods, and provider-specific options.
"""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class EmailProviderConfig:
    """Configuration for a specific email provider."""
    
    name: str
    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    auth_method: str
    drafts_folder: str = "Drafts"
    use_ssl: bool = True
    use_starttls: bool = True
    
    @classmethod
    def from_dict(cls, name: str, config_dict: Dict[str, Any]) -> 'EmailProviderConfig':
        """Create a provider config from a dictionary."""
        return cls(
            name=name,
            imap_server=config_dict.get('imap_server'),
            imap_port=config_dict.get('imap_port', 993),
            smtp_server=config_dict.get('smtp_server'),
            smtp_port=config_dict.get('smtp_port', 587),
            auth_method=config_dict.get('auth_method', 'app_password'),
            drafts_folder=config_dict.get('drafts_folder', 'Drafts'),
            use_ssl=config_dict.get('use_ssl', True),
            use_starttls=config_dict.get('use_starttls', True)
        )


class EmailConfigManager:
    """Manages email provider configurations."""
    
    # Default configuration for common providers
    DEFAULT_PROVIDERS = {
        'gmail': {
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'auth_method': 'app_password',
            'drafts_folder': 'Drafts'
        },
        'outlook': {
            'imap_server': 'imap-mail.outlook.com',
            'imap_port': 993,
            'smtp_server': 'smtp-mail.outlook.com',
            'smtp_port': 587,
            'auth_method': 'app_password',
            'drafts_folder': 'Drafts'
        },
        'yahoo': {
            'imap_server': 'imap.mail.yahoo.com',
            'imap_port': 993,
            'smtp_server': 'smtp.mail.yahoo.com',
            'smtp_port': 587,
            'auth_method': 'app_password',
            'drafts_folder': 'Drafts'
        },
        'icloud': {
            'imap_server': 'imap.mail.me.com',
            'imap_port': 993,
            'smtp_server': 'smtp.mail.me.com',
            'smtp_port': 587,
            'auth_method': 'app_password',
            'drafts_folder': 'Drafts'
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the config manager.
        
        Args:
            config_file: Path to custom configuration file (optional)
        """
        self.config_file = config_file
        self._providers = {}
        self._current_provider = None
        self._load_configurations()
    
    def _load_configurations(self) -> None:
        """Load provider configurations from file or defaults."""
        # Start with default providers
        self._providers = self.DEFAULT_PROVIDERS.copy()
        
        # Override with custom config file if provided
        if self.config_file and os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    custom_config = yaml.safe_load(f)
                    if 'providers' in custom_config:
                        self._providers.update(custom_config['providers'])
                    # Load current provider setting
                    self._current_provider = custom_config.get('provider', 'gmail')
            except Exception as e:
                print(f"Warning: Failed to load custom config file {self.config_file}: {e}")
                print("Using default configurations only.")
        
        # Default to gmail if no provider specified
        if not self._current_provider:
            self._current_provider = 'gmail'
    
    def get_provider_config(self, provider_name: str) -> EmailProviderConfig:
        """
        Get configuration for a specific provider.
        
        Args:
            provider_name: Name of the email provider
            
        Returns:
            EmailProviderConfig: Configuration for the provider
            
        Raises:
            ValueError: If provider is not configured
        """
        if provider_name not in self._providers:
            available_providers = ', '.join(self._providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not configured. "
                f"Available providers: {available_providers}"
            )
        
        return EmailProviderConfig.from_dict(
            provider_name, 
            self._providers[provider_name]
        )
    
    def get_available_providers(self) -> list:
        """Get list of available provider names."""
        return list(self._providers.keys())
    
    def get_current_provider(self) -> str:
        """Get the currently configured provider."""
        return self._current_provider
    
    def add_custom_provider(self, name: str, config: Dict[str, Any]) -> None:
        """
        Add a custom provider configuration.
        
        Args:
            name: Provider name
            config: Provider configuration dictionary
        """
        self._providers[name] = config
    
    def get_credentials(self, provider: str = None) -> Dict[str, str]:
        """
        Get email credentials from configuration file.
        
        Args:
            provider: Provider name
            
        Returns:
            Dictionary containing credentials
            
        Raises:
            ValueError: If credentials not found in configuration
        """
        credentials = {}
        
        # Get credentials from configuration file
        if provider and provider in self._providers:
            provider_config = self._providers[provider]
            config_email = provider_config.get('email')
            # Support both 'app_password' and 'password' fields
            config_password = (
                provider_config.get('app_password') or 
                provider_config.get('password')
            )
            
            if config_email and config_password:
                credentials['email'] = config_email
                credentials['password'] = config_password
                credentials['username'] = provider_config.get('username', config_email)
                return credentials
        
        # If no valid configuration found, raise error
        raise ValueError(
            f"Email credentials not found for provider '{provider}' in configuration file. "
            f"Please ensure email and app_password are configured in {self.config_file}."
        )
    


# Global config manager instance
config_manager = EmailConfigManager()


def create_email_config_file(file_path: str) -> None:
    """
    Create a sample email configuration file.
    
    Args:
        file_path: Path where to create the configuration file
    """
    sample_config = {
        'providers': {
            'gmail': {
                'imap_server': 'imap.gmail.com',
                'imap_port': 993,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'auth_method': 'app_password',
                'drafts_folder': 'Drafts',
                'use_ssl': True,
                'use_starttls': True
            },
            'outlook': {
                'imap_server': 'imap-mail.outlook.com',
                'imap_port': 993,
                'smtp_server': 'smtp-mail.outlook.com',
                'smtp_port': 587,
                'auth_method': 'app_password',
                'drafts_folder': 'Drafts',
                'use_ssl': True,
                'use_starttls': True
            },
            'custom_exchange': {
                'imap_server': 'mail.company.com',
                'imap_port': 993,
                'smtp_server': 'mail.company.com',
                'smtp_port': 587,
                'auth_method': 'ntlm',
                'drafts_folder': 'Drafts',
                'use_ssl': True,
                'use_starttls': True
            }
        }
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    
    print(f"Sample email configuration created at: {file_path}")