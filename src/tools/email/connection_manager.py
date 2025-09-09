"""
Connection management and error handling for email operations.

Provides robust connection handling with automatic reconnection,
retry logic, and error handling for IMAP and SMTP operations.
"""

import time
import imaplib
import smtplib
from typing import Callable, Any, Dict
from functools import wraps
from .email_config import EmailProviderConfig


class ConnectionError(Exception):
    """Raised when email connection fails."""
    pass


class AuthenticationError(Exception):
    """Raised when email authentication fails."""
    pass


class EmailConnectionManager:
    """Manages email connections with retry and error handling."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        """
        Initialize connection manager.
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
    
    def retry_on_failure(self, exceptions: tuple = None):
        """
        Decorator for retrying operations on failure.
        
        Args:
            exceptions: Tuple of exception types to retry on
        """
        if exceptions is None:
            exceptions = (ConnectionError, imaplib.IMAP4.error, smtplib.SMTPException)
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None
                
                for attempt in range(self.max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < self.max_retries:
                            wait_time = self.backoff_factor ** attempt
                            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time:.1f}s...")
                            time.sleep(wait_time)
                        else:
                            print(f"All {self.max_retries + 1} attempts failed.")
                
                raise last_exception
            return wrapper
        return decorator
    
    @staticmethod
    def create_imap_connection(config: EmailProviderConfig, credentials: Dict[str, str]) -> imaplib.IMAP4_SSL:
        """
        Create and authenticate IMAP connection.
        
        Args:
            config: Email provider configuration
            credentials: Authentication credentials
            
        Returns:
            Authenticated IMAP connection
            
        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        try:
            # Create IMAP connection
            if config.use_ssl:
                connection = imaplib.IMAP4_SSL(config.imap_server, config.imap_port)
            else:
                connection = imaplib.IMAP4(config.imap_server, config.imap_port)
                if config.use_starttls:
                    connection.starttls()
            
            # Authenticate
            try:
                connection.login(credentials['email'], credentials['password'])
            except imaplib.IMAP4.error as e:
                raise AuthenticationError(f"IMAP authentication failed: {e}")
            
            return connection
            
        except (OSError, imaplib.IMAP4.error) as e:
            raise ConnectionError(f"IMAP connection failed: {e}")
    
    @staticmethod 
    def create_smtp_connection(config: EmailProviderConfig, credentials: Dict[str, str]) -> smtplib.SMTP:
        """
        Create and authenticate SMTP connection.
        
        Args:
            config: Email provider configuration
            credentials: Authentication credentials
            
        Returns:
            Authenticated SMTP connection
            
        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        # 首先尝试标准SMTP连接
        connection = None
        try:
            print(f"正在连接SMTP服务器: {config.smtp_server}:{config.smtp_port}")
            
            # 如果端口是465，尝试SSL连接
            if config.smtp_port == 465:
                print("检测到465端口，尝试SMTP_SSL连接...")
                connection = smtplib.SMTP_SSL(
                    config.smtp_server, 
                    config.smtp_port,
                    timeout=60
                )
                print("SMTP_SSL连接建立成功")
            else:
                # Create SMTP connection with longer timeout and local hostname
                import socket
                local_hostname = socket.getfqdn()
                connection = smtplib.SMTP(
                    config.smtp_server, 
                    config.smtp_port, 
                    local_hostname=local_hostname,
                    timeout=60  # 增加超时时间到60秒
                )
                print("SMTP连接建立成功")
            
            # Enable debug output for troubleshooting
            # connection.set_debuglevel(1)  # Uncomment for detailed SMTP debug
            
            # 发送EHLO命令确保连接正常
            print("发送EHLO命令...")
            connection.ehlo()
            print("EHLO命令成功")
            
            # 只有在非SSL连接时才需要STARTTLS
            if config.use_starttls and config.smtp_port != 465:
                print("启用STARTTLS加密...")
                # 尝试不同的TLS配置
                try:
                    # 标准STARTTLS
                    connection.starttls()
                    print("STARTTLS启用成功")
                except Exception as e:
                    print(f"标准STARTTLS失败: {e}")
                    print("尝试兼容性STARTTLS...")
                    # 尝试兼容性设置
                    import ssl
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    connection.starttls(context=context)
                    print("兼容性STARTTLS启用成功")
                
                # STARTTLS后重新发送EHLO
                print("STARTTLS后重新发送EHLO...")
                connection.ehlo()
                print("STARTTLS后EHLO成功")
            
            # Authenticate
            print("正在进行SMTP身份验证...")
            try:
                connection.login(credentials['email'], credentials['password'])
                print("SMTP身份验证成功")
            except smtplib.SMTPAuthenticationError as e:
                raise AuthenticationError(f"SMTP authentication failed: {e}")
            
            return connection
            
        except (OSError, smtplib.SMTPException) as e:
            raise ConnectionError(f"SMTP connection failed: {e}")
    
    def execute_imap_operation(
        self, 
        connection: imaplib.IMAP4_SSL, 
        operation: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Execute IMAP operation with error handling.
        
        Args:
            connection: IMAP connection
            operation: Function to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Operation result
        """
        @self.retry_on_failure((imaplib.IMAP4.error,))
        def execute():
            try:
                return operation(connection, *args, **kwargs)
            except imaplib.IMAP4.abort as e:
                # Connection was aborted, need to reconnect
                raise ConnectionError(f"IMAP connection aborted: {e}")
        
        return execute()
    
    def execute_smtp_operation(
        self, 
        connection: smtplib.SMTP, 
        operation: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """
        Execute SMTP operation with error handling.
        
        Args:
            connection: SMTP connection
            operation: Function to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Operation result
        """
        @self.retry_on_failure((smtplib.SMTPException,))
        def execute():
            try:
                return operation(connection, *args, **kwargs)
            except smtplib.SMTPServerDisconnected as e:
                # Connection was disconnected, need to reconnect
                raise ConnectionError(f"SMTP connection disconnected: {e}")
        
        return execute()


class IMAPConnectionPool:
    """Pool of IMAP connections for reuse."""
    
    def __init__(self, config: EmailProviderConfig, credentials: Dict[str, str]):
        """
        Initialize connection pool.
        
        Args:
            config: Email provider configuration
            credentials: Authentication credentials
        """
        self.config = config
        self.credentials = credentials
        self.connection = None
        self.connection_manager = EmailConnectionManager()
    
    def get_connection(self) -> imaplib.IMAP4_SSL:
        """
        Get a valid IMAP connection.
        
        Returns:
            IMAP connection
        """
        if self.connection is None or not self._is_connection_alive():
            self._create_new_connection()
        
        return self.connection
    
    def _create_new_connection(self) -> None:
        """Create a new IMAP connection."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
        
        self.connection = self.connection_manager.create_imap_connection(
            self.config, 
            self.credentials
        )
    
    def _is_connection_alive(self) -> bool:
        """
        Check if the current connection is still alive.
        
        Returns:
            True if connection is alive, False otherwise
        """
        if not self.connection:
            return False
        
        try:
            # Try a simple NOOP command
            status, _ = self.connection.noop()
            return status == 'OK'
        except:
            return False
    
    def close(self) -> None:
        """Close the connection pool."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            self.connection = None


def handle_email_errors(func: Callable) -> Callable:
    """
    Decorator to handle common email errors gracefully.
    
    Args:
        func: Function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AuthenticationError as e:
            print(f"Authentication failed: {e}")
            print("Please check your email credentials and app password.")
            return None
        except ConnectionError as e:
            print(f"Connection failed: {e}")
            print("Please check your internet connection and email server settings.")
            return None
        except Exception as e:
            print(f"Unexpected error in {func.__name__}: {e}")
            return None
    
    return wrapper