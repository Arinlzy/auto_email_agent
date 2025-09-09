"""
Email parsing utilities for extracting and processing email content.

Handles email body extraction, threading information, and message formatting
to maintain compatibility with the existing Gmail API format.
"""

import re
import email
import uuid
import base64
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr
from datetime import datetime
from ...state import Email


class EmailParser:
    """Utility class for parsing and processing email messages."""
    
    @staticmethod
    def extract_email_info(message: email.message.Message, msg_id: str) -> Dict[str, str]:
        """
        Extract email information from an email.message.Message object.
        
        Args:
            message: Email message object
            msg_id: Message ID from IMAP
            
        Returns:
            Dictionary containing email information in Gmail API format
        """
        headers = {
            header_name.lower(): header_value 
            for header_name, header_value in message.items()
        }
        
        return {
            'id': msg_id,
            'threadId': EmailParser._generate_thread_id(message),
            'messageId': headers.get('message-id', ''),
            'references': headers.get('references', ''),
            'sender': headers.get('from', 'Unknown'),
            'subject': headers.get('subject', 'No Subject'),
            'body': EmailParser.extract_body(message),
            'date': headers.get('date', '')
        }
    
    @staticmethod
    def extract_body(message: email.message.Message) -> str:
        """
        Extract email body text from an email message.
        
        Prioritizes text/plain over text/html and handles multipart messages.
        
        Args:
            message: Email message object
            
        Returns:
            Cleaned email body text
        """
        body = ""
        
        if message.is_multipart():
            # For multipart messages, walk through all parts
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        break  # Prefer plain text
                    except (UnicodeDecodeError, LookupError):
                        continue
                        
                elif content_type == "text/html" and not body:
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        html_body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        body = EmailParser._extract_text_from_html(html_body)
                    except (UnicodeDecodeError, LookupError):
                        continue
        else:
            # Single part message
            charset = message.get_content_charset() or 'utf-8'
            try:
                body = message.get_payload(decode=True).decode(charset, errors='ignore')
                
                if message.get_content_type() == "text/html":
                    body = EmailParser._extract_text_from_html(body)
            except (UnicodeDecodeError, LookupError, AttributeError):
                # Fallback for non-binary payloads
                body = str(message.get_payload())
        
        return EmailParser._clean_body_text(body)
    
    @staticmethod
    def _extract_text_from_html(html_content: str) -> str:
        """
        Extract plain text from HTML content.
        
        Args:
            html_content: HTML string
            
        Returns:
            Plain text extracted from HTML
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # Remove script, style, and other non-content tags
            for tag in soup(['script', 'style', 'head', 'meta', 'title', 'link']):
                tag.decompose()
            return soup.get_text(separator='\n', strip=True)
        except Exception:
            # Fallback if BeautifulSoup fails
            return re.sub(r'<[^>]+>', '', html_content)
    
    @staticmethod
    def _clean_body_text(text: str) -> str:
        """
        Clean up email body text by removing extra whitespace.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Replace multiple whitespace with single space
        # But preserve some structure by keeping line breaks where appropriate
        text = re.sub(r'\r\n', '\n', text)  # Normalize line endings
        text = re.sub(r'\r', '\n', text)    # Handle Mac line endings
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Reduce multiple blank lines
        text = re.sub(r'[ \t]+', ' ', text)  # Replace multiple spaces/tabs with single space
        
        return text.strip()
    
    @staticmethod
    def _generate_thread_id(message: email.message.Message) -> str:
        """
        Generate thread ID from email headers.
        
        Uses In-Reply-To or References headers to determine threading,
        falling back to Message-ID if no threading info available.
        
        Args:
            message: Email message object
            
        Returns:
            Thread ID string
        """
        in_reply_to = message.get('In-Reply-To', '').strip()
        references = message.get('References', '').strip()
        message_id = message.get('Message-ID', '').strip()
        
        if in_reply_to:
            # Use the message we're replying to as thread ID
            return in_reply_to.strip('<>')
        elif references:
            # Use the first reference as thread ID
            refs = references.split()
            if refs:
                return refs[0].strip('<>')
        
        # If no threading info, use message ID as thread ID
        if message_id:
            return message_id.strip('<>')
        
        # Last resort: generate a UUID
        return str(uuid.uuid4())
    
    @staticmethod
    def create_reply_message(
        original_email: Email, 
        reply_text: str, 
        sender_email: str,
        send_mode: bool = False
    ) -> MIMEMultipart:
        """
        Create a properly formatted reply message.
        
        Args:
            original_email: The Email object being replied to
            reply_text: Text content of the reply
            sender_email: Sender's email address
            send_mode: If True, generates Message-ID for sending
            
        Returns:
            MIMEMultipart message ready for sending
        """
        import time
        start_time = time.time()
        print("开始创建邮件消息...")
        
        message = MIMEMultipart("alternative")
        
        # Extract recipient email address
        recipient = EmailParser._extract_email_address(original_email.sender)
        
        # Set basic headers
        message['To'] = recipient
        message['From'] = sender_email
        
        # Handle subject line
        subject = original_email.subject
        if not subject.lower().startswith('re:'):
            subject = f"Re: {subject}"
        message['Subject'] = subject
        
        # Set threading headers for proper conversation flow
        if original_email.messageId:
            message['In-Reply-To'] = original_email.messageId
            # Combine existing references with the original message ID
            references = f"{original_email.references} {original_email.messageId}".strip()
            message['References'] = references
        
        # Generate Message-ID for sending (not for drafts)
        if send_mode:
            message['Message-ID'] = f"<{uuid.uuid4()}@{sender_email.split('@')[1]}>"
        
        # Add message body in both plain text and HTML formats
        text_part = MIMEText(reply_text, 'plain', 'utf-8')
        message.attach(text_part)
        
        # Create simple HTML version
        html_text = reply_text.replace('\n', '<br>\n')
        html_part = MIMEText(html_text, 'html', 'utf-8')
        message.attach(html_part)
        
        # 性能监控
        end_time = time.time()
        print(f"邮件消息创建完成，耗时: {end_time - start_time:.2f}秒")
        
        return message
    
    @staticmethod
    def _extract_email_address(sender_string: str) -> str:
        """
        Extract email address from sender string.
        
        Handles formats like "Name <email@example.com>" or "email@example.com"
        
        Args:
            sender_string: Sender field from email
            
        Returns:
            Email address only
        """
        name, email_addr = parseaddr(sender_string)
        return email_addr if email_addr else sender_string
    
    @staticmethod
    def message_to_bytes(message: MIMEMultipart) -> bytes:
        """
        Convert MIMEMultipart message to bytes for IMAP operations.
        
        Args:
            message: MIMEMultipart message
            
        Returns:
            Message as bytes
        """
        return message.as_bytes()
    
    @staticmethod
    def message_to_base64(message: MIMEMultipart) -> str:
        """
        Convert MIMEMultipart message to base64 for Gmail API compatibility.
        
        Args:
            message: MIMEMultipart message
            
        Returns:
            Base64 encoded message string
        """
        return base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
    
    @staticmethod
    def decode_imap_data(data: Union[str, bytes]) -> str:
        """
        Decode IMAP data safely.
        
        Args:
            data: Data from IMAP (could be string or bytes)
            
        Returns:
            Decoded string
        """
        if isinstance(data, bytes):
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return data.decode('utf-8', errors='ignore')
        return str(data) if data else ""