"""
IMAP/SMTP email client implementation.

Provides a complete email client using IMAP for reading and SMTP for sending,
maintaining compatibility with the existing Gmail API interface.
"""

import os
import imaplib
import smtplib
import email
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from .base_email_client import BaseEmailClient
from .email_config import EmailProviderConfig, EmailConfigManager
from .email_parser import EmailParser
from .connection_manager import (
    EmailConnectionManager, 
    IMAPConnectionPool, 
    handle_email_errors
)
from ...state import Email


class IMAPSMTPClient(BaseEmailClient):
    """
    IMAP/SMTP email client implementation.
    
    Uses IMAP for reading emails and SMTP for sending emails,
    providing the same interface as the Gmail API client.
    """
    
    def __init__(self, provider: str = "gmail", config_file: Optional[str] = None):
        """
        Initialize IMAP/SMTP client.
        
        Args:
            provider: Email provider name (gmail, outlook, yahoo, etc.)
            config_file: Optional custom configuration file
        """
        # Get provider configuration
        config_manager = EmailConfigManager(config_file)
        self.config = config_manager.get_provider_config(provider)
        
        # Get credentials from configuration file or environment
        self.credentials = config_manager.get_credentials(provider)
        
        # Initialize base class
        super().__init__(self.credentials['email'], self.credentials)
        
        # Connection management
        self.connection_manager = EmailConnectionManager()
        self.imap_pool = None
        self.smtp_connection = None
        
        print(f"Initialized {provider} email client for {self.email_address}")
    
    @handle_email_errors
    def connect(self) -> bool:
        """
        Establish connections to email servers.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Create IMAP connection pool
            self.imap_pool = IMAPConnectionPool(self.config, self.credentials)
            
            # Test IMAP connection
            imap_conn = self.imap_pool.get_connection()
            imap_conn.select('INBOX')
            
            self._connected = True
            print(f"Successfully connected to {self.config.name} email servers")
            return True
            
        except Exception as e:
            print(f"Failed to connect to email servers: {e}")
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        """Close connections to email servers."""
        if self.imap_pool:
            self.imap_pool.close()
            self.imap_pool = None
        
        if self.smtp_connection:
            try:
                self.smtp_connection.quit()
            except:
                pass
            self.smtp_connection = None
        
        self._connected = False
        print("Disconnected from email servers")
    
    @handle_email_errors
    def fetch_unanswered_emails(self, max_results: int = 50) -> List[Dict[str, str]]:
        """
        Fetch unanswered emails from the server.
        
        Args:
            max_results: Maximum number of emails to fetch
            
        Returns:
            List of email dictionaries compatible with Gmail API format
        """
        if not self._connected:
            if not self.connect():
                return []
        
        try:
            imap_conn = self.imap_pool.get_connection()
            imap_conn.select('INBOX')
            
            # Search for recent emails (last 8 hours) that are UNSEEN (unread)
            since_date = (datetime.now() - timedelta(hours=8)).strftime("%d-%b-%Y")
            search_criteria = f'UNSEEN SINCE "{since_date}"'
            
            print(f"Searching for emails with criteria: {search_criteria}")
            status, messages = imap_conn.search(None, search_criteria)
            if status != 'OK':
                print(f"IMAP search failed: {status}")
                return []
            
            if not messages[0]:
                print("No recent unread emails found")
                return []
            
            email_ids = messages[0].split()
            unanswered_emails = []
            
            # Process emails (most recent first)
            for email_id in reversed(email_ids[-max_results:]):
                try:
                    email_info = self._get_email_info(imap_conn, email_id)
                    if email_info and not self._should_skip_email(email_info):
                        unanswered_emails.append(email_info)
                except Exception as e:
                    print(f"Error processing email {email_id}: {e}")
                    continue
            
            print(f"Found {len(unanswered_emails)} unanswered emails")
            return unanswered_emails
            
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
    
    def _get_email_info(self, imap_conn: imaplib.IMAP4_SSL, email_id: bytes) -> Optional[Dict[str, str]]:
        """
        Get email information from IMAP.
        
        Args:
            imap_conn: IMAP connection
            email_id: Email ID from IMAP
            
        Returns:
            Email information dictionary or None if error
        """
        try:
            # Fetch email data
            status, msg_data = imap_conn.fetch(email_id, '(RFC822)')
            if status != 'OK' or not msg_data or not msg_data[0]:
                return None
            
            # Parse email message
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Extract email information using EmailParser
            return EmailParser.extract_email_info(
                email_message, 
                email_id.decode('utf-8')
            )
            
        except Exception as e:
            print(f"Error extracting email info: {e}")
            return None
    
    def _should_skip_email(self, email_info: Dict[str, str]) -> bool:
        """
        Enhanced email filtering logic.
        
        Skip emails if:
        1. Sent by ourselves
        2. Thread already has a draft reply (check drafts folder)
        
        Args:
            email_info: Email information dictionary
            
        Returns:
            bool: True if email should be skipped, False otherwise
        """
        # Skip emails sent by ourselves
        if self.email_address in email_info.get('sender', ''):
            print(f"Skipping email from self: {email_info.get('sender', '')}")
            return True
        
        # Check if thread already has a draft reply
        thread_id = email_info.get('threadId', '')
        if thread_id and self._thread_has_draft_reply(thread_id):
            print(f"Skipping email - thread {thread_id} already has draft reply")
            return True
        
        return False
    
    def _thread_has_draft_reply(self, thread_id: str) -> bool:
        """
        Check if a thread already has a draft reply.
        
        Args:
            thread_id: Email thread ID
            
        Returns:
            bool: True if thread has draft reply, False otherwise
        """
        try:
            # For now, disable draft checking to avoid IMAP state issues
            # This is a simplified implementation that will be enhanced later
            return False
            
        except Exception as e:
            print(f"Error checking thread drafts: {e}")
            return False
    
    @handle_email_errors
    def create_draft_reply(self, initial_email: Email, reply_text: str) -> bool:
        """
        Create a draft reply to an email.
        
        Args:
            initial_email: Email object to reply to
            reply_text: Content of the reply
            
        Returns:
            True if draft created successfully, False otherwise
        """
        if not self._connected:
            if not self.connect():
                return False
        
        try:
            # Create reply message
            reply_message = EmailParser.create_reply_message(
                initial_email, 
                reply_text, 
                self.email_address,
                send_mode=False  # Draft mode
            )
            
            # Save to drafts folder
            imap_conn = self.imap_pool.get_connection()
            
            # Try to select drafts folder
            drafts_folder = self.config.drafts_folder
            try:
                imap_conn.select(drafts_folder)
            except imaplib.IMAP4.error:
                # Try alternative drafts folder names
                for alt_folder in ['INBOX.Drafts', '[Gmail]/Drafts', 'Draft']:
                    try:
                        imap_conn.select(alt_folder)
                        drafts_folder = alt_folder
                        break
                    except imaplib.IMAP4.error:
                        continue
                else:
                    # Use INBOX as fallback
                    imap_conn.select('INBOX')
                    drafts_folder = 'INBOX'
                    print(f"Warning: Could not find drafts folder, saving to INBOX")
            
            # Save draft
            message_bytes = EmailParser.message_to_bytes(reply_message)
            result = imap_conn.append(
                drafts_folder,
                '\\Draft',  # IMAP flag for drafts
                imaplib.Time2Internaldate(datetime.now()),
                message_bytes
            )
            
            if result[0] == 'OK':
                print(f"Draft reply created successfully in {drafts_folder}")
                return True
            else:
                print(f"Failed to create draft: {result}")
                return False
                
        except Exception as e:
            print(f"Error creating draft reply: {e}")
            return False
    
    @handle_email_errors
    def send_reply(self, initial_email: Email, reply_text: str) -> bool:
        """
        Send a reply to an email.
        
        Args:
            initial_email: Email object to reply to
            reply_text: Content of the reply
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self._connected:
            if not self.connect():
                return False
        
        try:
            # Create reply message
            reply_message = EmailParser.create_reply_message(
                initial_email, 
                reply_text, 
                self.email_address,
                send_mode=True  # Send mode
            )
            
            # Create SMTP connection
            smtp_conn = self.connection_manager.create_smtp_connection(
                self.config, 
                self.credentials
            )
            
            try:
                # Send the message
                smtp_conn.send_message(reply_message)
                print(f"Reply sent successfully to {initial_email.sender}")
                return True
                
            finally:
                smtp_conn.quit()
                
        except Exception as e:
            print(f"Error sending reply: {e}")
            return False
    
    def _get_folder_list(self) -> List[str]:
        """
        Get list of available IMAP folders.
        
        Returns:
            List of folder names
        """
        try:
            if not self._connected:
                return []
            
            imap_conn = self.imap_pool.get_connection()
            status, folders = imap_conn.list()
            
            if status == 'OK':
                folder_names = []
                for folder in folders:
                    # Parse folder name from IMAP response
                    folder_str = folder.decode('utf-8')
                    # Extract folder name (after the last space/quote)
                    folder_name = folder_str.split('"')[-2] if '"' in folder_str else folder_str.split()[-1]
                    folder_names.append(folder_name)
                return folder_names
            
        except Exception as e:
            print(f"Error getting folder list: {e}")
        
        return []
    
    def get_connection_status(self) -> Dict[str, bool]:
        """
        Get status of email connections.
        
        Returns:
            Dictionary with connection status information
        """
        status = {
            'connected': self._connected,
            'imap_available': False,
            'smtp_available': False
        }
        
        if self.imap_pool:
            try:
                conn = self.imap_pool.get_connection()
                conn.noop()
                status['imap_available'] = True
            except:
                status['imap_available'] = False
        
        try:
            smtp_conn = self.connection_manager.create_smtp_connection(
                self.config, 
                self.credentials
            )
            smtp_conn.quit()
            status['smtp_available'] = True
        except:
            status['smtp_available'] = False
        
        return status