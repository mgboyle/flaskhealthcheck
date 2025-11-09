"""
Service Manager module for managing multiple services and health checks
Supports SOAP and REST services with validation rules
"""
import json
import os
import logging
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ServiceManager:
    """Manager for multiple services and their health checks"""
    
    def __init__(self, storage_file='services.json'):
        """
        Initialize Service Manager
        
        Args:
            storage_file (str): Path to JSON file for storing service configurations
        """
        self.storage_file = storage_file
        self.services = self._load_services()
    
    def _load_services(self):
        """Load services from storage file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading services: {str(e)}")
                return {}
        return {}
    
    def _save_services(self):
        """Save services to storage file"""
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(self.services, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving services: {str(e)}")
            raise
    
    def add_service(self, service_id, service_config):
        """
        Add or update a service
        
        Args:
            service_id (str): Unique service identifier
            service_config (dict): Service configuration
                - name (str): Service name
                - type (str): 'soap' or 'rest'
                - endpoint (str): Service endpoint URL
                - method (str): Method/operation name
                - params (dict): Parameters for the method
                - auth (dict, optional): Authentication configuration
                - validation_rules (list, optional): List of validation rules
        """
        service_config['id'] = service_id
        service_config['created_at'] = service_config.get('created_at', datetime.now().isoformat())
        service_config['updated_at'] = datetime.now().isoformat()
        service_config['last_check'] = None
        service_config['last_result'] = None
        
        self.services[service_id] = service_config
        self._save_services()
        return service_config
    
    def get_service(self, service_id):
        """Get a specific service"""
        return self.services.get(service_id)
    
    def get_all_services(self):
        """Get all services"""
        return self.services
    
    def delete_service(self, service_id):
        """Delete a service"""
        if service_id in self.services:
            del self.services[service_id]
            self._save_services()
            return True
        return False
    
    def update_health_check_result(self, service_id, result):
        """
        Update the health check result for a service
        
        Args:
            service_id (str): Service identifier
            result (dict): Health check result
        """
        if service_id in self.services:
            self.services[service_id]['last_check'] = datetime.now().isoformat()
            self.services[service_id]['last_result'] = result
            self._save_services()
    
    def validate_response(self, response, validation_rules):
        """
        Validate response against validation rules
        
        Args:
            response (dict): Service response
            validation_rules (list): List of validation rule dictionaries
                Each rule can have:
                - type (str): 'status_code', 'contains', 'regex', 'json_path', 'equals'
                - field (str): Field to validate (for json_path, equals)
                - value: Expected value
                - pattern (str): Regex pattern (for regex)
                
        Returns:
            dict: Validation result with 'passed' boolean and 'failures' list
        """
        if not validation_rules:
            return {'passed': True, 'failures': []}
        
        failures = []
        
        for rule in validation_rules:
            rule_type = rule.get('type')
            
            try:
                if rule_type == 'status_code':
                    expected = rule.get('value')
                    actual = response.get('status_code')
                    if actual != expected:
                        failures.append(f"Status code {actual} != {expected}")
                
                elif rule_type == 'contains':
                    text = str(response.get('body', ''))
                    search_text = rule.get('value')
                    if search_text not in text:
                        failures.append(f"Response does not contain '{search_text}'")
                
                elif rule_type == 'regex':
                    text = str(response.get('body', ''))
                    pattern = rule.get('pattern')
                    if not re.search(pattern, text):
                        failures.append(f"Response does not match regex '{pattern}'")
                
                elif rule_type == 'json_path':
                    field = rule.get('field')
                    expected = rule.get('value')
                    body = response.get('body', {})
                    
                    # Simple json path evaluation (supports dot notation)
                    value = self._get_nested_value(body, field)
                    if value != expected:
                        failures.append(f"Field '{field}' value {value} != {expected}")
                
                elif rule_type == 'equals':
                    field = rule.get('field')
                    expected = rule.get('value')
                    body = response.get('body', {})
                    
                    value = self._get_nested_value(body, field)
                    if value != expected:
                        failures.append(f"Field '{field}' value {value} != {expected}")
                
            except Exception as e:
                failures.append(f"Validation error for rule {rule_type}: {str(e)}")
        
        return {
            'passed': len(failures) == 0,
            'failures': failures
        }
    
    def _get_nested_value(self, data, path):
        """
        Get nested value from dictionary using dot notation
        
        Args:
            data: Dictionary or object
            path (str): Dot-separated path (e.g., 'result.value')
            
        Returns:
            Value at the path or None
        """
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return None
        
        return value
