"""
Email tools package for IMAP/SMTP email handling.

This package provides a unified interface for working with different email providers
through IMAP/SMTP protocols, serving as a replacement for Gmail API dependencies.
"""

from .email_tools import EmailToolsClass, create_email_tools
from .base_email_client import BaseEmailClient
from .imap_smtp_client import IMAPSMTPClient
from .email_factory import EmailFactory, auto_create_client
from .email_config import EmailConfigManager

__all__ = [
    'EmailToolsClass',
    'create_email_tools',
    'BaseEmailClient', 
    'IMAPSMTPClient',
    'EmailFactory',
    'auto_create_client',
    'EmailConfigManager'
]