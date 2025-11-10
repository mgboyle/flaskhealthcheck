"""
REST Client module for handling REST API operations
Supports Windows Authentication via NTLM and Kerberos
"""
import requests
from requests_ntlm import HttpNtlmAuth

# Try to import Kerberos support, but make it optional
try:
    from requests_kerberos import HTTPKerberosAuth, OPTIONAL
    KERBEROS_AVAILABLE = True
except ImportError:
    KERBEROS_AVAILABLE = False
    HTTPKerberosAuth = None
    OPTIONAL = None

import logging
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RESTClient:
    """REST Client wrapper for API operations"""
    
    def __init__(self, base_url, username=None, password=None, domain=None, auth_type='ntlm'):
        """
        Initialize REST client with base URL and optional Windows Authentication
        
        Args:
            base_url (str): Base URL for the REST API
            username (str, optional): Username for Windows Authentication
            password (str, optional): Password for Windows Authentication
            domain (str, optional): Domain for Windows Authentication (NTLM only)
            auth_type (str, optional): Authentication type - 'ntlm' or 'kerberos'. Default is 'ntlm'
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.domain = domain
        self.auth_type = auth_type
        self.session = requests.Session()
        
        # Setup authentication if credentials provided
        if username and password and auth_type == 'kerberos':
            if not KERBEROS_AVAILABLE:
                raise ImportError("Kerberos authentication requested but requests_kerberos is not installed. "
                                "Install it with: pip install requests-kerberos")
            self.session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
            logger.info(f"Initialized REST client for {base_url} with Kerberos Authentication")
        elif username and password:
            auth_username = f"{domain}\\{username}" if domain else username
            self.session.auth = HttpNtlmAuth(auth_username, password)
            logger.info(f"Initialized REST client for {base_url} with NTLM Authentication")
        else:
            logger.info(f"Initialized REST client for {base_url}")
    
    def execute_request(self, endpoint, method='GET', params=None, headers=None, body=None):
        """
        Execute a REST request
        
        Args:
            endpoint (str): API endpoint path
            method (str): HTTP method (GET, POST, PUT, DELETE, etc.)
            params (dict, optional): Query parameters
            headers (dict, optional): Request headers
            body (dict, optional): Request body (for POST/PUT)
            
        Returns:
            dict: Response data and metadata
        """
        try:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"
            
            # Set default headers
            if headers is None:
                headers = {}
            if 'Content-Type' not in headers and body is not None:
                headers['Content-Type'] = 'application/json'
            
            # Execute request
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                headers=headers,
                json=body if isinstance(body, dict) else None,
                data=body if not isinstance(body, dict) else None,
                timeout=30
            )
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'body': response_data,
                'success': 200 <= response.status_code < 300
            }
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout for {url}")
            raise Exception("Request timeout")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {str(e)}")
            raise Exception(f"Connection error: {str(e)}")
        except Exception as e:
            logger.error(f"Error executing REST request to {url}: {str(e)}")
            raise
