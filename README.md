# Flask Service Health Check

A modern, comprehensive web application for testing and monitoring both SOAP and REST web services. Features a service dashboard with health checks, validation rules, and Windows Authentication support.

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

### Core Functionality
✨ **Modern UI** - Clean, responsive interface with gradient design  
🔍 **SOAP Support** - Full WSDL parsing, method discovery, and execution  
🌐 **REST Support** - Complete REST API testing with all HTTP methods  
🔐 **Windows Authentication** - Optional NTLM and Kerberos for both SOAP and REST  
📊 **Service Dashboard** - Manage and monitor multiple services from one place  
⚡ **Health Checks** - Automated health monitoring with customizable validation  
✓ **Validation Rules** - Status codes, text matching, regex, and JSON path validation  
⚙️ **Dynamic Forms** - Auto-generate parameter forms based on schemas  
💾 **Config Persistence** - Save and load service configurations  
🐳 **Docker Ready** - Containerized for easy deployment  
✅ **Fully Tested** - 36+ comprehensive integration tests

## Quick Start

### Using Python

```bash
# Clone the repository
git clone https://github.com/mgboyle/flaskhealthcheck.git
cd flaskhealthcheck

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

Visit http://localhost:5000 in your browser.

### Using Docker

```bash
# Build the Docker image
docker build -t flask-soap-healthcheck .

# Run the container
docker run -p 5000:5000 flask-soap-healthcheck
```

Visit http://localhost:5000 in your browser.

## Usage

The application has two main interfaces:

### SOAP Tester (http://localhost:5000)

Individual SOAP service testing with immediate feedback.

#### 1. Load WSDL Endpoint

Enter a WSDL URL (e.g., `https://www.w3schools.com/xml/tempconvert.asmx?WSDL`) and click **Load WSDL**.

##### Windows Authentication (Optional)

If your SOAP endpoint requires Windows Authentication, expand the **🔐 Windows Authentication** section and provide:
- **Authentication Type**: Select either NTLM or Kerberos
- **Domain** (optional for NTLM): Your Windows domain
- **Username**: Your username
- **Password**: Your password

The application supports both NTLM and Kerberos authentication for secured endpoints.

#### 2. Select Method

Choose a method from the dropdown list and click **Load Parameters**.

#### 3. Enter Parameters

Fill in the required parameters in the auto-generated form.

#### 4. Execute & View Response

Click **Execute Method** to call the SOAP service and view the response.

#### 5. Save Configuration (Optional)

Click **Save Configuration** to persist your settings (including authentication credentials) for later use.

### Service Dashboard (http://localhost:5000/dashboard)

Centralized management and monitoring of multiple services (SOAP and REST).

#### Adding a Service

1. Click **+ Add Service**
2. Fill in service details:
   - **Name**: Descriptive service name
   - **Type**: SOAP or REST
   - **Endpoint**: Service URL
   - **Method**: SOAP method name or HTTP method (GET, POST, etc.)
   - **Authentication** (optional): NTLM or Kerberos credentials
   - **Validation Rules** (optional): Define success criteria

#### Running Health Checks

- **Single Service**: Click **▶ Check** on any service
- **All Services**: Click **▶ Run All Checks**
- Results show real-time status with success/failure indicators

#### Validation Rules

Add validation rules to verify response content:
- **Status Code**: Check HTTP status (e.g., 200)
- **Contains**: Verify response contains specific text
- **Regex**: Match response against regex pattern
- **JSON Path**: Validate nested JSON values (e.g., `result.status = "ok"`)
- **Equals**: Check exact field values

## Example: Temperature Converter

Try the built-in example with W3Schools Temperature Converter:

1. **WSDL URL**: `https://www.w3schools.com/xml/tempconvert.asmx?WSDL`
2. **Method**: `CelsiusToFahrenheit`
3. **Parameter**: `Celsius = 0`
4. **Expected Result**: `32` (0°C = 32°F)

## API Endpoints

### POST /api/load-wsdl
Load a WSDL file and retrieve available methods.

**Request:**
```json
{
  "wsdl_url": "https://example.com/service?WSDL",
  "auth": {
    "auth_type": "ntlm",
    "username": "user",
    "password": "pass",
    "domain": "DOMAIN"
  }
}
```

**Note**: The `auth` object is optional. Include it only when Windows Authentication is required.
- For **NTLM**: Set `auth_type` to `"ntlm"` and optionally include `domain`
- For **Kerberos**: Set `auth_type` to `"kerberos"` (domain not used)

**Response:**
```json
{
  "success": true,
  "methods": ["Method1", "Method2"]
}
```

### POST /api/get-method-params
Get parameters for a specific method.

**Request:**
```json
{
  "method_name": "CelsiusToFahrenheit"
}
```

**Response:**
```json
{
  "success": true,
  "params": [
    {
      "name": "Celsius",
      "type": "string",
      "required": true
    }
  ]
}
```

### POST /api/execute-method
Execute a SOAP method.

**Request:**
```json
{
  "method_name": "CelsiusToFahrenheit",
  "params": {
    "Celsius": "0"
  }
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "result": "32"
  }
}
```

### POST /api/save-config
Save current configuration to JSON file.

### GET /api/load-config
Load previously saved configuration.

### Service Management Endpoints

#### GET /api/services
Get all configured services.

**Response:**
```json
{
  "success": true,
  "services": {
    "service-id-1": {
      "id": "service-id-1",
      "name": "My API",
      "type": "rest",
      "endpoint": "https://api.example.com",
      "method": "GET",
      "last_check": "2025-11-09T22:00:00",
      "last_result": {...}
    }
  }
}
```

#### POST /api/services
Add a new service.

**Request:**
```json
{
  "name": "My API",
  "type": "rest",
  "endpoint": "https://api.example.com",
  "method": "GET",
  "rest_endpoint": "/health",
  "auth": {
    "auth_type": "ntlm",
    "username": "user",
    "password": "pass"
  },
  "validation_rules": [
    {
      "type": "status_code",
      "value": 200
    }
  ]
}
```

#### PUT /api/services/<service_id>
Update an existing service.

#### DELETE /api/services/<service_id>
Delete a service.

#### POST /api/services/<service_id>/healthcheck
Run health check for a specific service.

**Response:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "response": {...},
    "validation": {
      "passed": true,
      "failures": []
    },
    "timestamp": "2025-11-09T22:00:00"
  }
}
```

#### POST /api/healthcheck/all
Run health checks for all services.

## Running Tests

```bash
# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest tests/test_integration.py -v

# Run specific test class
pytest tests/test_integration.py::TestRESTServices -v
```

### Test Coverage

The integration tests verify:
- ✅ WSDL loading and method discovery
- ✅ Parameter extraction
- ✅ SOAP method execution
- ✅ NTLM and Kerberos authentication
- ✅ Configuration persistence
- ✅ REST service CRUD operations
- ✅ Service manager functionality
- ✅ Health checks for SOAP and REST
- ✅ Validation rules (all types)
- ✅ Complete end-to-end workflows

**Total: 36+ integration tests**

## Project Structure

```
flaskhealthcheck/
├── app.py                      # Main Flask application
├── soap_client.py              # SOAP client wrapper (zeep)
├── rest_client.py              # REST client wrapper
├── service_manager.py          # Service & validation manager
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
├── templates/
│   ├── index.html             # SOAP tester UI
│   └── dashboard.html         # Service dashboard UI
├── static/
│   ├── css/
│   │   ├── style.css          # Base styles
│   │   └── dashboard.css      # Dashboard styles
│   └── js/
│       ├── app.js             # SOAP tester logic
│       └── dashboard.js       # Dashboard logic
└── tests/
    ├── test_integration.py    # Integration tests
    └── test_tempconvert.wsdl  # Mock WSDL
```
│   └── js/
│       └── app.js             # Frontend JavaScript
└── tests/
    └── test_integration.py    # Integration tests
```

## Technology Stack

- **Backend**: Flask 3.0.0
- **SOAP Client**: Zeep 4.2.1
- **Frontend**: Vanilla JavaScript, Modern CSS
- **Testing**: Pytest 7.4.3
- **Containerization**: Docker

## Configuration

The application saves configurations to `config.json` in the root directory. This file contains:

```json
{
  "wsdl_url": "https://example.com/service?WSDL",
  "method_name": "MethodName",
  "params": {
    "param1": "value1"
  }
}
```

## Environment Variables

- `SECRET_KEY`: Flask secret key (default: 'dev-secret-key-change-in-production')
- `FLASK_APP`: Application entry point (default: 'app.py')

## Troubleshooting

### WSDL Loading Fails

- Ensure the WSDL URL is accessible and returns valid XML
- Check for network/firewall restrictions
- Verify the WSDL endpoint supports HTTPS if required

### Method Execution Fails

- Verify all required parameters are provided
- Check parameter types match the WSDL schema
- Review SOAP service logs if available

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- SOAP client powered by [Zeep](https://docs.python-zeep.org/)
- Sample WSDL from [W3Schools](https://www.w3schools.com/)

## Support

For issues, questions, or contributions, please open an issue on GitHub.