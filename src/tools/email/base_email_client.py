"""
Abstract base class for email clients.

Defines the standard interface that all email client implementations must follow,
ensuring compatibility with the existing Gmail API workflow.
"""

from abc import ABC, abstractmethod
from typing import List, Dict
from ...state import Email


class BaseEmailClient(ABC):
    """
    Abstract base class for email clients.
    
    This class defines the interface that all email client implementations
    must follow to ensure compatibility with the existing workflow.
    """
    
    def __init__(self, email_address: str, credentials: Dict[str, str]):
        """
        Initialize the email client.
        
        Args:
            email_address: The email address for this account
            credentials: Dictionary containing authentication credentials
        """
        self.email_address = email_address
        self.credentials = credentials
        self._connected = False
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the email server.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """
        Close the connection to the email server.
        """
        pass
    
    @abstractmethod
    def fetch_unanswered_emails(self, max_results: int = 50) -> List[Dict[str, str]]:
        """
        Fetch unanswered emails from the server.
        
        This method should return emails in the same format as the Gmail API
        to maintain compatibility with existing code.
        
        Args:
            max_results: Maximum number of emails to fetch
            
        Returns:
            List of email dictionaries with keys: id, threadId, messageId, 
            references, sender, subject, body
        """
        pass
    
    @abstractmethod
    def create_draft_reply(self, initial_email: Email, reply_text: str) -> bool:
        """
        Create a draft reply to an email.
        
        Args:
            initial_email: The Email object to reply to
            reply_text: The content of the reply
            
        Returns:
            bool: True if draft created successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def send_reply(self, initial_email: Email, reply_text: str) -> bool:
        """
        Send a reply to an email.
        
        Args:
            initial_email: The Email object to reply to
            reply_text: The content of the reply
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        pass
    
    @property
    def is_connected(self) -> bool:
        """
        Check if the client is currently connected.
        
        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected
    
    def _should_skip_email(self, email_info: Dict[str, str]) -> bool:
        """
        Check if an email should be skipped (e.g., sent by ourselves).
        
        Args:
            email_info: Email information dictionary
            
        Returns:
            bool: True if email should be skipped, False otherwise
        """
        return self.email_address in email_info.get('sender', '')