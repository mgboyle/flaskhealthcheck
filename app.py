"""
Flask WSDL/SOAP Health Check Application
Main application entry point
Supports SOAP and REST services with health checks and validation
"""
from flask import Flask, render_template, request, jsonify
import json
import os
import logging
from soap_client import SOAPClient
from rest_client import RESTClient
from service_manager import ServiceManager
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = 'config.json'

# Global SOAP client instance (for backward compatibility)
soap_client = None

# Service manager instance
service_manager = ServiceManager()


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """Render the dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/load-wsdl', methods=['POST'])
def load_wsdl():
    """Load WSDL and return available methods"""
    global soap_client
    
    try:
        data = request.get_json()
        wsdl_url = data.get('wsdl_url')
        
        if not wsdl_url:
            return jsonify({'error': 'WSDL URL is required'}), 400
        
        # Get optional Windows Authentication credentials
        auth = data.get('auth', {})
        username = auth.get('username')
        password = auth.get('password')
        domain = auth.get('domain')
        auth_type = auth.get('auth_type', 'ntlm')  # Default to NTLM for backward compatibility
        
        # Create SOAP client with optional authentication
        soap_client = SOAPClient(wsdl_url, username=username, password=password, domain=domain, auth_type=auth_type)
        methods = soap_client.get_methods()
        
        return jsonify({
            'success': True,
            'methods': methods
        })
        
    except Exception as e:
        logger.error(f"Error loading WSDL: {wsdl_url if 'wsdl_url' in locals() else 'unknown'}")
        return jsonify({'error': 'Failed to load WSDL. Please check the URL and try again.'}), 500


@app.route('/api/get-method-params', methods=['POST'])
def get_method_params():
    """Get parameters for a specific method"""
    global soap_client
    
    try:
        data = request.get_json()
        method_name = data.get('method_name')
        
        if not soap_client:
            logger.error("No WSDL loaded - soap_client is None")
            return jsonify({
                'error': 'No WSDL loaded. Please load a WSDL first.',
                'details': 'The SOAP client is not initialized. Click "Load WSDL & Discover Methods" to load the WSDL.'
            }), 400
        
        if not method_name:
            return jsonify({
                'error': 'Method name is required',
                'details': 'Please select or enter a method name.'
            }), 400
        
        logger.info(f"Getting params and example payload for method: {method_name}")
        params = soap_client.get_method_params(method_name)
        example_payload = soap_client.get_method_example_payload(method_name)
        
        logger.info(f"Successfully generated example payload for {method_name}: {example_payload}")
        
        return jsonify({
            'success': True,
            'params': params,
            'example_payload': example_payload
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting method params for {method_name if 'method_name' in locals() else 'unknown'}: {error_msg}", exc_info=True)
        return jsonify({
            'error': 'Failed to get method parameters',
            'details': error_msg
        }), 500


@app.route('/api/execute-method', methods=['POST'])
def execute_method():
    """Execute a SOAP method with provided parameters"""
    global soap_client
    
    try:
        data = request.get_json()
        method_name = data.get('method_name')
        params = data.get('params', {})
        
        if not soap_client:
            return jsonify({'error': 'No WSDL loaded'}), 400
        
        if not method_name:
            return jsonify({'error': 'Method name is required'}), 400
        
        result = soap_client.execute_method(method_name, params)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error executing method: {method_name if 'method_name' in locals() else 'unknown'}")
        return jsonify({'error': 'Failed to execute method. Please check parameters and try again.'}), 500


@app.route('/api/save-config', methods=['POST'])
def save_config():
    """Save current configuration to JSON file"""
    try:
        data = request.get_json()
        
        config = {
            'wsdl_url': data.get('wsdl_url'),
            'method_name': data.get('method_name'),
            'params': data.get('params', {}),
            'auth': data.get('auth', {})
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        
        return jsonify({
            'success': True,
            'message': 'Configuration saved successfully'
        })
        
    except Exception as e:
        logger.error("Error saving configuration")
        return jsonify({'error': 'Failed to save configuration. Please try again.'}), 500


@app.route('/api/load-config', methods=['GET'])
def load_config():
    """Load configuration from JSON file"""
    try:
        if not os.path.exists(CONFIG_FILE):
            return jsonify({
                'success': False,
                'message': 'No saved configuration found'
            })
        
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        return jsonify({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        logger.error("Error loading configuration")
        return jsonify({'error': 'Failed to load configuration. Please try again.'}), 500


# ============ NEW SERVICE MANAGEMENT ENDPOINTS ============

@app.route('/api/services', methods=['GET'])
def get_services():
    """Get all services"""
    try:
        services = service_manager.get_all_services()
        return jsonify({
            'success': True,
            'services': services
        })
    except Exception as e:
        logger.error(f"Error getting services: {str(e)}")
        return jsonify({'error': 'Failed to get services'}), 500


@app.route('/api/services', methods=['POST'])
def add_service():
    """Add a new service"""
    try:
        data = request.get_json()
        
        # Generate service ID if not provided
        service_id = data.get('id', str(uuid.uuid4()))
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Service name is required'}), 400
        if not data.get('type'):
            return jsonify({'error': 'Service type is required'}), 400
        if not data.get('endpoint'):
            return jsonify({'error': 'Service endpoint is required'}), 400
        
        service = service_manager.add_service(service_id, data)
        
        return jsonify({
            'success': True,
            'service': service
        })
        
    except Exception as e:
        logger.error(f"Error adding service: {str(e)}")
        return jsonify({'error': 'Failed to add service'}), 500


@app.route('/api/services/<service_id>', methods=['GET'])
def get_service(service_id):
    """Get a specific service"""
    try:
        service = service_manager.get_service(service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        return jsonify({
            'success': True,
            'service': service
        })
    except Exception as e:
        logger.error(f"Error getting service: {str(e)}")
        return jsonify({'error': 'Failed to get service'}), 500


@app.route('/api/services/<service_id>', methods=['PUT'])
def update_service(service_id):
    """Update a service"""
    try:
        data = request.get_json()
        data['id'] = service_id
        
        service = service_manager.add_service(service_id, data)
        
        return jsonify({
            'success': True,
            'service': service
        })
    except Exception as e:
        logger.error(f"Error updating service: {str(e)}")
        return jsonify({'error': 'Failed to update service'}), 500


@app.route('/api/services/<service_id>', methods=['DELETE'])
def delete_service(service_id):
    """Delete a service"""
    try:
        result = service_manager.delete_service(service_id)
        if not result:
            return jsonify({'error': 'Service not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Service deleted successfully'
        })
    except Exception as e:
        logger.error(f"Error deleting service: {str(e)}")
        return jsonify({'error': 'Failed to delete service'}), 500


@app.route('/api/services/<service_id>/healthcheck', methods=['POST'])
def run_healthcheck(service_id):
    """Run health check for a specific service"""
    try:
        service = service_manager.get_service(service_id)
        if not service:
            return jsonify({'error': 'Service not found'}), 404
        
        logger.info(f"Running health check for service: {service.get('name', service_id)}")
        result = _execute_healthcheck(service)
        
        # Update the service with the result
        service_manager.update_health_check_result(service_id, result)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error running health check for service {service_id}: {error_msg}", exc_info=True)
        return jsonify({
            'error': 'Failed to run health check',
            'details': error_msg
        }), 500


@app.route('/api/healthcheck/all', methods=['POST'])
def run_all_healthchecks():
    """Run health checks for all services"""
    try:
        services = service_manager.get_all_services()
        results = {}
        
        for service_id, service in services.items():
            try:
                result = _execute_healthcheck(service)
                service_manager.update_health_check_result(service_id, result)
                results[service_id] = result
            except Exception as e:
                results[service_id] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': None
                }
        
        return jsonify({
            'success': True,
            'results': results
        })
        
    except Exception as e:
        logger.error("Error running all health checks")
        return jsonify({'error': 'Failed to run all health checks. Please try again.'}), 500


def _execute_healthcheck(service):
    """
    Execute health check for a service
    
    Args:
        service (dict): Service configuration
        
    Returns:
        dict: Health check result
    """
    from datetime import datetime
    
    service_type = service.get('type')
    endpoint = service.get('endpoint')
    auth = service.get('auth', {})
    validation_rules = service.get('validation_rules', [])
    
    try:
        if service_type == 'soap':
            # SOAP service health check
            logger.info(f"Executing SOAP health check for endpoint: {endpoint}")
            client = SOAPClient(
                endpoint,
                username=auth.get('username'),
                password=auth.get('password'),
                domain=auth.get('domain'),
                auth_type=auth.get('auth_type', 'ntlm')
            )
            
            method_name = service.get('method')
            params = service.get('params', {})
            
            logger.info(f"Calling SOAP method '{method_name}' with params: {params}")
            response_data = client.execute_method(method_name, params)
            logger.info(f"SOAP method response: {response_data}")
            
            response = {
                'status_code': 200,
                'body': response_data,
                'success': True
            }
            
        elif service_type == 'rest':
            # REST service health check
            logger.info(f"Executing REST health check for endpoint: {endpoint}")
            client = RESTClient(
                endpoint,
                username=auth.get('username'),
                password=auth.get('password'),
                domain=auth.get('domain'),
                auth_type=auth.get('auth_type', 'ntlm')
            )
            
            method = service.get('method', 'GET')
            rest_endpoint = service.get('rest_endpoint', '')
            params = service.get('params', {})
            headers = service.get('headers', {})
            body = service.get('body')
            
            logger.info(f"Calling REST {method} {rest_endpoint} with params: {params}")
            response = client.execute_request(
                endpoint=rest_endpoint,
                method=method,
                params=params if method == 'GET' else None,
                headers=headers,
                body=body
            )
            logger.info(f"REST response status: {response.get('status_code')}")
        else:
            raise ValueError(f"Unknown service type: {service_type}")
        
        # Validate response
        validation_result = service_manager.validate_response(response, validation_rules)
        
        result = {
            'success': response.get('success', False) and validation_result['passed'],
            'response': response,
            'validation': validation_result,
            'timestamp': datetime.now().isoformat()
        }
        
        if not result['success']:
            logger.warning(f"Health check failed for {service.get('name', 'unknown')}: validation={validation_result}")
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Health check error for {service.get('name', 'unknown')}: {error_msg}", exc_info=True)
        return {
            'success': False,
            'error': error_msg,
            'timestamp': datetime.now().isoformat()
        }


if __name__ == '__main__':
    # Only enable debug in development mode
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
