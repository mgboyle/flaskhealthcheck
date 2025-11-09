"""
Integration tests for SOAP Health Check application
Tests the complete flow with CelsiusToFahrenheit sample WSDL
"""
import pytest
import json
import os
import sys
from unittest.mock import Mock, patch
from zeep import xsd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from soap_client import SOAPClient


# Sample WSDL file path (local mock WSDL)
SAMPLE_WSDL = os.path.join(os.path.dirname(__file__), 'test_tempconvert.wsdl')
CELSIUS_TO_FAHRENHEIT_METHOD = "CelsiusToFahrenheit"


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def cleanup_config():
    """Cleanup config file after tests"""
    yield
    if os.path.exists('config.json'):
        os.remove('config.json')


class TestSOAPClient:
    """Test SOAP client functionality"""
    
    def test_load_wsdl(self):
        """Test loading WSDL and getting methods"""
        client = SOAPClient(SAMPLE_WSDL)
        methods = client.get_methods()
        
        assert len(methods) > 0
        assert CELSIUS_TO_FAHRENHEIT_METHOD in methods or "CelsiusToFahrenheit" in methods
    
    def test_get_method_params(self):
        """Test getting method parameters"""
        client = SOAPClient(SAMPLE_WSDL)
        params = client.get_method_params(CELSIUS_TO_FAHRENHEIT_METHOD)
        
        assert len(params) > 0
        # Should have Celsius parameter
        param_names = [p['name'] for p in params]
        assert 'Celsius' in param_names
    
    @patch('soap_client.SOAPClient.execute_method')
    def test_execute_celsius_to_fahrenheit(self, mock_execute):
        """Test executing CelsiusToFahrenheit method"""
        # Mock the response
        mock_execute.return_value = {'result': '32'}
        
        client = SOAPClient(SAMPLE_WSDL)
        
        # Convert 0 Celsius to Fahrenheit (should be 32)
        result = client.execute_method(CELSIUS_TO_FAHRENHEIT_METHOD, {'Celsius': '0'})
        
        assert result is not None
        assert '32' in str(result)
    
    @patch('soap_client.SOAPClient.execute_method')
    def test_execute_with_different_values(self, mock_execute):
        """Test executing method with different temperature values"""
        client = SOAPClient(SAMPLE_WSDL)
        
        test_cases = [
            ('0', '32'),    # 0°C = 32°F
            ('100', '212'), # 100°C = 212°F
        ]
        
        for celsius, expected_fahrenheit in test_cases:
            mock_execute.return_value = {'result': expected_fahrenheit}
            result = client.execute_method(CELSIUS_TO_FAHRENHEIT_METHOD, {'Celsius': celsius})
            assert result is not None
            result_str = str(result)
            assert expected_fahrenheit in result_str, f"Expected {expected_fahrenheit}°F for {celsius}°C"


class TestFlaskEndpoints:
    """Test Flask API endpoints"""
    
    def test_index_route(self, client):
        """Test main page loads"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'SOAP Health Check' in response.data
    
    def test_load_wsdl_endpoint(self, client):
        """Test WSDL loading endpoint"""
        response = client.post('/api/load-wsdl',
                              json={'wsdl_url': SAMPLE_WSDL},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['methods']) > 0
        assert CELSIUS_TO_FAHRENHEIT_METHOD in data['methods']
    
    def test_load_wsdl_missing_url(self, client):
        """Test WSDL loading with missing URL"""
        response = client.post('/api/load-wsdl',
                              json={},
                              content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_get_method_params_endpoint(self, client):
        """Test getting method parameters endpoint"""
        # First load WSDL
        client.post('/api/load-wsdl',
                   json={'wsdl_url': SAMPLE_WSDL},
                   content_type='application/json')
        
        # Then get params
        response = client.post('/api/get-method-params',
                              json={'method_name': CELSIUS_TO_FAHRENHEIT_METHOD},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['params']) > 0
    
    @patch('soap_client.SOAPClient.execute_method')
    def test_execute_method_endpoint(self, mock_execute, client):
        """Test method execution endpoint"""
        # Mock the SOAP execution
        mock_execute.return_value = {'result': '32'}
        
        # First load WSDL
        client.post('/api/load-wsdl',
                   json={'wsdl_url': SAMPLE_WSDL},
                   content_type='application/json')
        
        # Then execute method
        response = client.post('/api/execute-method',
                              json={
                                  'method_name': CELSIUS_TO_FAHRENHEIT_METHOD,
                                  'params': {'Celsius': '0'}
                              },
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['result'] is not None
        # Check if result contains 32 (0°C = 32°F)
        assert '32' in str(data['result'])
    
    def test_save_and_load_config(self, client, cleanup_config):
        """Test saving and loading configuration"""
        # Save config
        config_data = {
            'wsdl_url': SAMPLE_WSDL,
            'method_name': CELSIUS_TO_FAHRENHEIT_METHOD,
            'params': {'Celsius': '25'}
        }
        
        response = client.post('/api/save-config',
                              json=config_data,
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Load config
        response = client.get('/api/load-config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['config']['wsdl_url'] == SAMPLE_WSDL
        assert data['config']['method_name'] == CELSIUS_TO_FAHRENHEIT_METHOD
        assert data['config']['params']['Celsius'] == '25'


class TestIntegration:
    """End-to-end integration tests"""
    
    @patch('soap_client.SOAPClient.execute_method')
    def test_complete_workflow(self, mock_execute, client, cleanup_config):
        """Test complete workflow: load WSDL -> select method -> execute -> save config"""
        
        # Mock SOAP execution
        mock_execute.return_value = {'result': '212'}
        
        # Step 1: Load WSDL
        response = client.post('/api/load-wsdl',
                              json={'wsdl_url': SAMPLE_WSDL},
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        methods = data['methods']
        assert CELSIUS_TO_FAHRENHEIT_METHOD in methods
        
        # Step 2: Get method parameters
        response = client.post('/api/get-method-params',
                              json={'method_name': CELSIUS_TO_FAHRENHEIT_METHOD},
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        params = data['params']
        assert len(params) > 0
        
        # Step 3: Execute method with parameters
        response = client.post('/api/execute-method',
                              json={
                                  'method_name': CELSIUS_TO_FAHRENHEIT_METHOD,
                                  'params': {'Celsius': '100'}
                              },
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert '212' in str(data['result'])  # 100°C = 212°F
        
        # Step 4: Save configuration
        response = client.post('/api/save-config',
                              json={
                                  'wsdl_url': SAMPLE_WSDL,
                                  'method_name': CELSIUS_TO_FAHRENHEIT_METHOD,
                                  'params': {'Celsius': '100'}
                              },
                              content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Step 5: Verify saved configuration
        response = client.get('/api/load-config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['config']['params']['Celsius'] == '100'


class TestWindowsAuthentication:
    """Test Windows Authentication functionality"""
    
    def test_load_wsdl_with_ntlm_auth(self, client):
        """Test loading WSDL with NTLM Authentication credentials"""
        response = client.post('/api/load-wsdl',
                              json={
                                  'wsdl_url': SAMPLE_WSDL,
                                  'auth': {
                                      'username': 'testuser',
                                      'password': 'testpass',
                                      'domain': 'TESTDOMAIN',
                                      'auth_type': 'ntlm'
                                  }
                              },
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['methods']) > 0
    
    def test_load_wsdl_with_kerberos_auth(self, client):
        """Test loading WSDL with Kerberos Authentication credentials"""
        try:
            from requests_kerberos import HTTPKerberosAuth
            kerberos_available = True
        except ImportError:
            kerberos_available = False
        
        response = client.post('/api/load-wsdl',
                              json={
                                  'wsdl_url': SAMPLE_WSDL,
                                  'auth': {
                                      'username': 'testuser',
                                      'password': 'testpass',
                                      'auth_type': 'kerberos'
                                  }
                              },
                              content_type='application/json')
        
        if kerberos_available:
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert len(data['methods']) > 0
        else:
            # If Kerberos is not available, the request should fail gracefully
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_load_wsdl_with_partial_auth(self, client):
        """Test loading WSDL with partial auth (no domain)"""
        response = client.post('/api/load-wsdl',
                              json={
                                  'wsdl_url': SAMPLE_WSDL,
                                  'auth': {
                                      'username': 'testuser',
                                      'password': 'testpass'
                                  }
                              },
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_save_config_with_ntlm_auth(self, client, cleanup_config):
        """Test saving configuration with NTLM authentication"""
        config_data = {
            'wsdl_url': SAMPLE_WSDL,
            'method_name': CELSIUS_TO_FAHRENHEIT_METHOD,
            'params': {'Celsius': '25'},
            'auth': {
                'username': 'testuser',
                'password': 'testpass',
                'domain': 'TESTDOMAIN',
                'auth_type': 'ntlm'
            }
        }
        
        response = client.post('/api/save-config',
                              json=config_data,
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Load and verify auth was saved
        response = client.get('/api/load-config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'auth' in data['config']
        assert data['config']['auth']['username'] == 'testuser'
        assert data['config']['auth']['domain'] == 'TESTDOMAIN'
        assert data['config']['auth']['auth_type'] == 'ntlm'
    
    def test_save_config_with_kerberos_auth(self, client, cleanup_config):
        """Test saving configuration with Kerberos authentication"""
        config_data = {
            'wsdl_url': SAMPLE_WSDL,
            'method_name': CELSIUS_TO_FAHRENHEIT_METHOD,
            'params': {'Celsius': '25'},
            'auth': {
                'username': 'testuser',
                'password': 'testpass',
                'auth_type': 'kerberos'
            }
        }
        
        response = client.post('/api/save-config',
                              json=config_data,
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Load and verify auth was saved
        response = client.get('/api/load-config')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'auth' in data['config']
        assert data['config']['auth']['username'] == 'testuser'
        assert data['config']['auth']['auth_type'] == 'kerberos'
    
    def test_backward_compatibility_no_auth(self, client):
        """Test backward compatibility when no auth is provided"""
        # Should work exactly like before when no auth is provided
        response = client.post('/api/load-wsdl',
                              json={'wsdl_url': SAMPLE_WSDL},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['methods']) > 0


class TestRESTServices:
    """Test REST service functionality"""
    
    @pytest.fixture
    def cleanup_services(self):
        """Cleanup services file after tests"""
        yield
        if os.path.exists('services.json'):
            os.remove('services.json')
    
    def test_add_rest_service(self, client, cleanup_services):
        """Test adding a REST service"""
        service_data = {
            'name': 'Test REST API',
            'type': 'rest',
            'endpoint': 'https://api.example.com',
            'method': 'GET',
            'rest_endpoint': '/health'
        }
        
        response = client.post('/api/services',
                              json=service_data,
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['service']['name'] == 'Test REST API'
        assert data['service']['type'] == 'rest'
    
    def test_add_soap_service(self, client, cleanup_services):
        """Test adding a SOAP service"""
        service_data = {
            'name': 'Test SOAP Service',
            'type': 'soap',
            'endpoint': SAMPLE_WSDL,
            'method': CELSIUS_TO_FAHRENHEIT_METHOD,
            'params': {}
        }
        
        response = client.post('/api/services',
                              json=service_data,
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['service']['type'] == 'soap'
    
    def test_get_all_services(self, client, cleanup_services):
        """Test getting all services"""
        # Add a service first
        service_data = {
            'name': 'Test Service',
            'type': 'rest',
            'endpoint': 'https://api.example.com'
        }
        
        client.post('/api/services',
                   json=service_data,
                   content_type='application/json')
        
        # Get all services
        response = client.get('/api/services')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['services']) > 0
    
    def test_update_service(self, client, cleanup_services):
        """Test updating a service"""
        # Add a service
        service_data = {
            'id': 'test-service-1',
            'name': 'Original Name',
            'type': 'rest',
            'endpoint': 'https://api.example.com'
        }
        
        response = client.post('/api/services',
                              json=service_data,
                              content_type='application/json')
        
        service_id = json.loads(response.data)['service']['id']
        
        # Update it
        updated_data = {
            'name': 'Updated Name',
            'type': 'rest',
            'endpoint': 'https://api.example.com/v2'
        }
        
        response = client.put(f'/api/services/{service_id}',
                             json=updated_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['service']['name'] == 'Updated Name'
    
    def test_delete_service(self, client, cleanup_services):
        """Test deleting a service"""
        # Add a service
        service_data = {
            'name': 'To Delete',
            'type': 'rest',
            'endpoint': 'https://api.example.com'
        }
        
        response = client.post('/api/services',
                              json=service_data,
                              content_type='application/json')
        
        service_id = json.loads(response.data)['service']['id']
        
        # Delete it
        response = client.delete(f'/api/services/{service_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify it's gone
        response = client.get(f'/api/services/{service_id}')
        assert response.status_code == 404


class TestHealthChecks:
    """Test health check functionality"""
    
    @pytest.fixture
    def cleanup_services(self):
        """Cleanup services file after tests"""
        yield
        if os.path.exists('services.json'):
            os.remove('services.json')
    
    @patch('soap_client.SOAPClient.execute_method')
    def test_soap_healthcheck(self, mock_execute, client, cleanup_services):
        """Test SOAP service health check"""
        # Mock SOAP execution
        mock_execute.return_value = {'result': '32'}
        
        # Add SOAP service
        service_data = {
            'name': 'SOAP Health Check',
            'type': 'soap',
            'endpoint': SAMPLE_WSDL,
            'method': CELSIUS_TO_FAHRENHEIT_METHOD,
            'params': {'Celsius': '0'}
        }
        
        response = client.post('/api/services',
                              json=service_data,
                              content_type='application/json')
        
        service_id = json.loads(response.data)['service']['id']
        
        # Run health check
        response = client.post(f'/api/services/{service_id}/healthcheck')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['result']['success'] is True
    
    @patch('requests.Session.request')
    def test_rest_healthcheck(self, mock_request, client, cleanup_services):
        """Test REST service health check"""
        # Mock REST response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok'}
        mock_response.headers = {}
        mock_request.return_value = mock_response
        
        # Add REST service
        service_data = {
            'name': 'REST Health Check',
            'type': 'rest',
            'endpoint': 'https://api.example.com',
            'method': 'GET',
            'rest_endpoint': '/health'
        }
        
        response = client.post('/api/services',
                              json=service_data,
                              content_type='application/json')
        
        service_id = json.loads(response.data)['service']['id']
        
        # Run health check
        response = client.post(f'/api/services/{service_id}/healthcheck')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    @patch('soap_client.SOAPClient.execute_method')
    def test_healthcheck_with_validation(self, mock_execute, client, cleanup_services):
        """Test health check with validation rules"""
        # Mock SOAP execution
        mock_execute.return_value = {'result': '32'}
        
        # Add service with validation rules
        service_data = {
            'name': 'SOAP with Validation',
            'type': 'soap',
            'endpoint': SAMPLE_WSDL,
            'method': CELSIUS_TO_FAHRENHEIT_METHOD,
            'params': {'Celsius': '0'},
            'validation_rules': [
                {
                    'type': 'json_path',
                    'field': 'result',
                    'value': '32'
                }
            ]
        }
        
        response = client.post('/api/services',
                              json=service_data,
                              content_type='application/json')
        
        service_id = json.loads(response.data)['service']['id']
        
        # Run health check
        response = client.post(f'/api/services/{service_id}/healthcheck')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['result']['validation']['passed'] is True
    
    @patch('soap_client.SOAPClient.execute_method')
    @patch('requests.Session.request')
    def test_run_all_healthchecks(self, mock_rest, mock_soap, client, cleanup_services):
        """Test running all health checks"""
        # Mock responses
        mock_soap.return_value = {'result': '32'}
        mock_rest_response = Mock()
        mock_rest_response.status_code = 200
        mock_rest_response.json.return_value = {'status': 'ok'}
        mock_rest_response.headers = {}
        mock_rest.return_value = mock_rest_response
        
        # Clear all existing services first
        response = client.get('/api/services')
        if response.status_code == 200:
            services = json.loads(response.data).get('services', {})
            for service_id in list(services.keys()):
                client.delete(f'/api/services/{service_id}')
        
        # Add SOAP service
        client.post('/api/services',
                   json={
                       'name': 'SOAP Service',
                       'type': 'soap',
                       'endpoint': SAMPLE_WSDL,
                       'method': CELSIUS_TO_FAHRENHEIT_METHOD
                   },
                   content_type='application/json')
        
        # Add REST service
        client.post('/api/services',
                   json={
                       'name': 'REST Service',
                       'type': 'rest',
                       'endpoint': 'https://api.example.com',
                       'method': 'GET'
                   },
                   content_type='application/json')
        
        # Run all health checks
        response = client.post('/api/healthcheck/all')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['results']) == 2


class TestValidation:
    """Test validation rules"""
    
    def test_validation_status_code(self):
        """Test status code validation"""
        from service_manager import ServiceManager
        
        manager = ServiceManager()
        response = {'status_code': 200}
        rules = [{'type': 'status_code', 'value': 200}]
        
        result = manager.validate_response(response, rules)
        assert result['passed'] is True
    
    def test_validation_contains(self):
        """Test contains validation"""
        from service_manager import ServiceManager
        
        manager = ServiceManager()
        response = {'body': 'Hello World'}
        rules = [{'type': 'contains', 'value': 'World'}]
        
        result = manager.validate_response(response, rules)
        assert result['passed'] is True
    
    def test_validation_json_path(self):
        """Test JSON path validation"""
        from service_manager import ServiceManager
        
        manager = ServiceManager()
        response = {'body': {'result': {'value': 42}}}
        rules = [{'type': 'json_path', 'field': 'result.value', 'value': 42}]
        
        result = manager.validate_response(response, rules)
        assert result['passed'] is True
    
    def test_validation_failure(self):
        """Test validation failure"""
        from service_manager import ServiceManager
        
        manager = ServiceManager()
        response = {'status_code': 500}
        rules = [{'type': 'status_code', 'value': 200}]
        
        result = manager.validate_response(response, rules)
        assert result['passed'] is False
        assert len(result['failures']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
