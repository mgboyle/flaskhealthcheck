"""
Flask WSDL/SOAP Health Check Application
Main application entry point
"""
from flask import Flask, render_template, request, jsonify
import json
import os
import logging
from soap_client import SOAPClient

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration file path
CONFIG_FILE = 'config.json'

# Global SOAP client instance
soap_client = None


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


@app.route('/api/load-wsdl', methods=['POST'])
def load_wsdl():
    """Load WSDL and return available methods"""
    global soap_client
    
    try:
        data = request.get_json()
        wsdl_url = data.get('wsdl_url')
        
        if not wsdl_url:
            return jsonify({'error': 'WSDL URL is required'}), 400
        
        # Create SOAP client
        soap_client = SOAPClient(wsdl_url)
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
            return jsonify({'error': 'No WSDL loaded'}), 400
        
        if not method_name:
            return jsonify({'error': 'Method name is required'}), 400
        
        params = soap_client.get_method_params(method_name)
        
        return jsonify({
            'success': True,
            'params': params
        })
        
    except Exception as e:
        logger.error(f"Error getting method params: {method_name if 'method_name' in locals() else 'unknown'}")
        return jsonify({'error': 'Failed to get method parameters. Please try again.'}), 500


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
            'params': data.get('params', {})
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


if __name__ == '__main__':
    # Only enable debug in development mode
    debug_mode = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
