"""
Email tools class providing Gmail API compatibility.

This class serves as a drop-in replacement for GmailToolsClass,
maintaining the exact same interface while using IMAP/SMTP underneath.
"""

from typing import List, Dict, Optional

from .email_factory import EmailFactory, auto_create_client
from .base_email_client import BaseEmailClient
from ...state import Email


class EmailToolsClass:
    """
    Email tools class compatible with GmailToolsClass interface.
    
    This class provides the exact same methods as GmailToolsClass but uses
    IMAP/SMTP protocols underneath, allowing for easy migration from Gmail API.
    """
    
    def __init__(self, provider: Optional[str] = None, config_file: Optional[str] = None):
        """
        Initialize email tools.
        
        Args:
            provider: Email provider name (auto-detected if None)
            config_file: Optional custom configuration file
        """
        try:
            if provider:
                self.client = EmailFactory.create_client(provider, config_file)
            else:
                self.client = auto_create_client(config_file)
            
            self._connected = False
            print(f"EmailToolsClass initialized with {type(self.client).__name__}")
            
        except Exception as e:
            print(f"Failed to initialize email client: {e}")
            print("Please check your email configuration and credentials.")
            raise
    
    @property
    def email_address(self) -> str:
        """Get the email address from the underlying client."""
        return getattr(self.client, 'email_address', 'Unknown')
    
    def fetch_unanswered_emails(self, max_results: int = 50) -> List[Dict[str, str]]:
        """
        Fetch unanswered emails from the email server.
        
        This method maintains compatibility with the Gmail API version,
        returning emails in the same format.
        
        Args:
            max_results: Maximum number of emails to fetch
            
        Returns:
            List of email dictionaries with Gmail API compatible format:
            - id: Email ID
            - threadId: Thread ID
            - messageId: Message ID
            - references: Email references
            - sender: Sender email address
            - subject: Email subject
            - body: Email body text
        """
        try:
            # Ensure connection
            if not self._connected:
                self._connected = self.client.connect()
                if not self._connected:
                    print("Failed to connect to email server")
                    return []
            
            # Fetch emails
            emails = self.client.fetch_unanswered_emails(max_results)
            
            print(f"Fetched {len(emails)} unanswered emails")
            return emails
            
        except Exception as e:
            print(f"Error fetching unanswered emails: {e}")
            return []
    
    def create_draft_reply(self, initial_email: Email, reply_text: str) -> Optional[Dict]:
        """
        Create a draft reply to an email.
        
        Args:
            initial_email: Email object to reply to
            reply_text: Content of the reply
            
        Returns:
            Draft information dictionary if successful, None if failed
        """
        try:
            # Ensure connection
            if not self._connected:
                self._connected = self.client.connect()
                if not self._connected:
                    print("Failed to connect to email server")
                    return None
            
            # Create draft
            success = self.client.create_draft_reply(initial_email, reply_text)
            
            if success:
                return {
                    'id': f"draft_{initial_email.id}",
                    'message': {
                        'id': f"msg_{initial_email.id}",
                        'threadId': initial_email.threadId
                    }
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error creating draft reply: {e}")
            return None
    
    def send_reply(self, initial_email: Email, reply_text: str) -> Optional[Dict]:
        """
        Send a reply to an email.
        
        Args:
            initial_email: Email object to reply to
            reply_text: Content of the reply
            
        Returns:
            Sent message information if successful, None if failed
        """
        try:
            # Ensure connection
            if not self._connected:
                self._connected = self.client.connect()
                if not self._connected:
                    print("Failed to connect to email server")
                    return None
            
            # Send reply
            success = self.client.send_reply(initial_email, reply_text)
            
            if success:
                return {
                    'id': f"sent_{initial_email.id}",
                    'threadId': initial_email.threadId,
                    'labelIds': ['SENT']
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error sending reply: {e}")
            return None
    
    def fetch_recent_emails(self, max_results: int = 50) -> List[Dict[str, str]]:
        """
        Fetch recent emails (for compatibility with existing code).
        
        This is an alias for fetch_unanswered_emails to maintain compatibility.
        
        Args:
            max_results: Maximum number of emails to fetch
            
        Returns:
            List of email dictionaries
        """
        return self.fetch_unanswered_emails(max_results)
    
    def fetch_draft_replies(self) -> List[Dict[str, str]]:
        """
        Fetch all draft email replies.
        
        Note: This is a simplified implementation for compatibility.
        The actual draft fetching is handled internally by the client.
        
        Returns:
            List of draft dictionaries (simplified)
        """
        try:
            # This is a placeholder implementation
            # The actual draft management is handled by the IMAP client
            print("Draft fetching is handled internally by IMAP client")
            return []
            
        except Exception as e:
            print(f"Error fetching drafts: {e}")
            return []
    
    def get_connection_status(self) -> Dict[str, bool]:
        """
        Get email connection status.
        
        Returns:
            Dictionary with connection status information
        """
        if hasattr(self.client, 'get_connection_status'):
            return self.client.get_connection_status()
        else:
            return {
                'connected': self._connected,
                'imap_available': self._connected,
                'smtp_available': self._connected
            }
    
    def reconnect(self) -> bool:
        """
        Reconnect to email servers.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        try:
            if self.client:
                self.client.disconnect()
            
            self._connected = self.client.connect()
            return self._connected
            
        except Exception as e:
            print(f"Error reconnecting: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from email servers."""
        try:
            if self.client:
                self.client.disconnect()
            self._connected = False
            print("Disconnected from email servers")
            
        except Exception as e:
            print(f"Error during disconnect: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        if not self._connected:
            self._connected = self.client.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
    
    def __del__(self):
        """Cleanup on object destruction."""
        try:
            self.disconnect()
        except:
            pass


# Convenience function for creating email tools with auto-detection
def create_email_tools(provider: Optional[str] = None, config_file: Optional[str] = None) -> EmailToolsClass:
    """
    Create EmailToolsClass instance with provider auto-detection.
    
    Args:
        provider: Email provider name (auto-detected if None)
        config_file: Optional configuration file
        
    Returns:
        EmailToolsClass instance
    """
    # If no provider specified, try to read from config file
    if provider is None and config_file:
        from .email_config import EmailConfigManager
        config_manager = EmailConfigManager(config_file)
        provider = config_manager.get_current_provider()
    
    return EmailToolsClass(provider, config_file)


# Legacy compatibility - direct replacement for GmailToolsClass
def GmailToolsClass(*args, **kwargs) -> EmailToolsClass:
    """
    Legacy compatibility function.
    
    Creates an EmailToolsClass instance configured for Gmail,
    maintaining backward compatibility with existing code.
    """
    return EmailToolsClass(provider='gmail', *args, **kwargs)