"""
SOAP Client module for handling WSDL operations
Uses zeep library for SOAP/WSDL interactions
Supports Windows Authentication via NTLM and Kerberos
"""
from zeep import Client
from zeep.exceptions import Fault, TransportError
from zeep.wsdl.utils import etree_to_string
from zeep.transports import Transport
from requests import Session
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SOAPClient:
    """SOAP Client wrapper for WSDL operations"""
    
    def __init__(self, wsdl_url, username=None, password=None, domain=None, auth_type='ntlm'):
        """
        Initialize SOAP client with WSDL URL and optional Windows Authentication
        
        Args:
            wsdl_url (str): URL to the WSDL file
            username (str, optional): Username for Windows Authentication
            password (str, optional): Password for Windows Authentication
            domain (str, optional): Domain for Windows Authentication (NTLM only)
            auth_type (str, optional): Authentication type - 'ntlm' or 'kerberos'. Default is 'ntlm'
        """
        try:
            self.wsdl_url = wsdl_url
            self.username = username
            self.password = password
            self.domain = domain
            self.auth_type = auth_type
            
            # Setup authentication if credentials provided
            if username and password and auth_type == 'kerberos':
                # Kerberos authentication
                if not KERBEROS_AVAILABLE:
                    raise ImportError("Kerberos authentication requested but requests_kerberos is not installed. "
                                    "Install it with: pip install requests-kerberos")
                session = Session()
                session.auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL)
                transport = Transport(session=session)
                self.client = Client(wsdl_url, transport=transport)
                logger.info(f"Successfully loaded WSDL from {wsdl_url} with Kerberos Authentication")
            elif username and password:
                # NTLM authentication (default)
                session = Session()
                # Format username with domain if provided
                auth_username = f"{domain}\\{username}" if domain else username
                session.auth = HttpNtlmAuth(auth_username, password)
                transport = Transport(session=session)
                self.client = Client(wsdl_url, transport=transport)
                logger.info(f"Successfully loaded WSDL from {wsdl_url} with NTLM Authentication")
            else:
                self.client = Client(wsdl_url)
                logger.info(f"Successfully loaded WSDL from {wsdl_url}")
            
            self.service = self.client.service
        except Exception as e:
            logger.error(f"Failed to load WSDL from {wsdl_url}: {str(e)}")
            raise
    
    def get_methods(self):
        """
        Get all available methods from the WSDL
        
        Returns:
            list: List of method names
        """
        methods = []
        for service in self.client.wsdl.services.values():
            for port in service.ports.values():
                for operation in port.binding._operations.values():
                    methods.append(operation.name)
        return methods
    
    def get_method_params(self, method_name):
        """
        Get parameter information for a specific method
        
        Args:
            method_name (str): Name of the method
            
        Returns:
            list: List of parameter dictionaries with name and type
        """
        params = []
        
        for service in self.client.wsdl.services.values():
            for port in service.ports.values():
                if method_name in port.binding._operations:
                    operation = port.binding._operations[method_name]
                    
                    # Get input message
                    if operation.input:
                        input_msg = operation.input.body.type
                        
                        # Extract parameter information
                        if hasattr(input_msg, 'elements'):
                            for element in input_msg.elements:
                                param_info = {
                                    'name': element[0],
                                    'type': str(element[1].type.name) if hasattr(element[1].type, 'name') else 'string',
                                    'required': element[1].is_optional == False
                                }
                                params.append(param_info)
        
        return params
    
    def get_method_example_payload(self, method_name):
        """
        Generate an example payload for a method based on WSDL schema
        
        Args:
            method_name (str): Name of the method
            
        Returns:
            dict: Example payload with nested structure for complex types
        """
        try:
            for service in self.client.wsdl.services.values():
                for port in service.ports.values():
                    if method_name in port.binding._operations:
                        operation = port.binding._operations[method_name]
                        
                        # Get input message
                        if operation.input:
                            input_msg = operation.input.body.type
                            
                            # Generate example from schema
                            if hasattr(input_msg, 'elements'):
                                example = {}
                                for element in input_msg.elements:
                                    param_name = element[0]
                                    param_type = element[1].type
                                    example[param_name] = self._generate_example_value(param_type, param_name)
                                return example
            
            return {}
        except Exception as e:
            logger.error(f"Error generating example payload for {method_name}: {str(e)}")
            return {}
    
    def _generate_example_value(self, param_type, param_name='value'):
        """
        Generate an example value based on parameter type
        
        Args:
            param_type: The parameter type from WSDL schema
            param_name: The parameter name for context
            
        Returns:
            Example value (string, dict, list, etc.)
        """
        # Check if it's a complex type
        if hasattr(param_type, 'elements'):
            # Complex type - recursively generate nested structure
            example = {}
            for element in param_type.elements:
                nested_name = element[0]
                nested_type = element[1].type
                example[nested_name] = self._generate_example_value(nested_type, nested_name)
            return example
        
        # Simple types - return example values
        type_name = str(param_type.name) if hasattr(param_type, 'name') else 'string'
        type_name_lower = type_name.lower()
        
        # Generate contextual examples based on type and name
        if 'int' in type_name_lower or 'long' in type_name_lower:
            return 0
        elif 'bool' in type_name_lower:
            return False
        elif 'decimal' in type_name_lower or 'double' in type_name_lower or 'float' in type_name_lower:
            return 0.0
        elif 'date' in type_name_lower:
            return '2025-01-01'
        elif 'time' in type_name_lower:
            return '12:00:00'
        else:
            # String or unknown type - provide contextual example
            name_lower = param_name.lower()
            if 'email' in name_lower:
                return 'user@example.com'
            elif 'phone' in name_lower:
                return '555-1234'
            elif 'name' in name_lower:
                return 'John Doe'
            elif 'address' in name_lower:
                return '123 Main St'
            elif 'city' in name_lower:
                return 'New York'
            elif 'country' in name_lower:
                return 'USA'
            elif 'code' in name_lower or 'id' in name_lower:
                return 'ABC123'
            else:
                return f'example_{param_name}'
    
    def execute_method(self, method_name, params):
        """
        Execute a SOAP method with provided parameters
        
        Args:
            method_name (str): Name of the method to execute
            params (dict): Dictionary of parameter name-value pairs
            
        Returns:
            dict: Result of the SOAP call
        """
        try:
            # Get the method from the service
            method = getattr(self.service, method_name)
            
            # Execute the method with unpacked parameters
            result = method(**params)
            
            # Convert result to serializable format
            if hasattr(result, '__dict__'):
                return self._serialize_object(result)
            else:
                return {'result': str(result)}
                
        except Fault as e:
            logger.error(f"SOAP Fault: {str(e)}")
            raise Exception(f"SOAP Fault: {str(e)}")
        except TransportError as e:
            logger.error(f"Transport Error: {str(e)}")
            raise Exception(f"Transport Error: {str(e)}")
        except Exception as e:
            logger.error(f"Error executing method {method_name}: {str(e)}")
            raise
    
    def _serialize_object(self, obj):
        """
        Serialize zeep object to dictionary
        
        Args:
            obj: Object to serialize
            
        Returns:
            dict: Serialized object
        """
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if not key.startswith('_'):
                    if hasattr(value, '__dict__'):
                        result[key] = self._serialize_object(value)
                    elif isinstance(value, list):
                        result[key] = [self._serialize_object(item) if hasattr(item, '__dict__') else item for item in value]
                    else:
                        result[key] = value
            return result
        else:
            return str(obj)
