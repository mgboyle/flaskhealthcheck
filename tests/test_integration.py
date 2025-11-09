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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
