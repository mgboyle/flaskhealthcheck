"""
SOAP Client module for handling WSDL operations
Uses zeep library for SOAP/WSDL interactions
Supports Windows Authentication via NTLM
"""
from zeep import Client
from zeep.exceptions import Fault, TransportError
from zeep.wsdl.utils import etree_to_string
from zeep.transports import Transport
from requests import Session
from requests_ntlm import HttpNtlmAuth
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SOAPClient:
    """SOAP Client wrapper for WSDL operations"""
    
    def __init__(self, wsdl_url, username=None, password=None, domain=None):
        """
        Initialize SOAP client with WSDL URL and optional Windows Authentication
        
        Args:
            wsdl_url (str): URL to the WSDL file
            username (str, optional): Username for Windows Authentication
            password (str, optional): Password for Windows Authentication
            domain (str, optional): Domain for Windows Authentication
        """
        try:
            self.wsdl_url = wsdl_url
            self.username = username
            self.password = password
            self.domain = domain
            
            # Setup authentication if credentials provided
            if username and password:
                session = Session()
                # Format username with domain if provided
                auth_username = f"{domain}\\{username}" if domain else username
                session.auth = HttpNtlmAuth(auth_username, password)
                transport = Transport(session=session)
                self.client = Client(wsdl_url, transport=transport)
                logger.info(f"Successfully loaded WSDL from {wsdl_url} with Windows Authentication")
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
