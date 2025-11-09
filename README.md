# Flask SOAP Health Check

A modern, user-friendly web application for testing and monitoring SOAP web services. Load WSDL endpoints, select methods, execute calls, and view responses with a beautiful UI.

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

✨ **Modern UI** - Clean, responsive interface with gradient design  
🔍 **WSDL Loading** - Automatically parse WSDL files and discover methods  
🔐 **Windows Authentication** - Optional NTLM and Kerberos authentication for secured endpoints  
⚙️ **Dynamic Forms** - Auto-generate parameter forms based on method signatures  
📊 **Response Viewer** - Pretty-print JSON responses with syntax highlighting  
💾 **Config Persistence** - Save and load configurations in JSON format  
🐳 **Docker Ready** - Containerized for easy deployment  
✅ **Fully Tested** - Comprehensive integration tests included

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

### 1. Load WSDL Endpoint

Enter a WSDL URL (e.g., `https://www.w3schools.com/xml/tempconvert.asmx?WSDL`) and click **Load WSDL**.

#### Windows Authentication (Optional)

If your SOAP endpoint requires Windows Authentication, expand the **🔐 Windows Authentication** section and provide:
- **Authentication Type**: Select either NTLM or Kerberos
- **Domain** (optional for NTLM): Your Windows domain
- **Username**: Your username
- **Password**: Your password

The application supports both NTLM and Kerberos authentication for secured SOAP endpoints.

### 2. Select Method

Choose a method from the dropdown list and click **Load Parameters**.

### 3. Enter Parameters

Fill in the required parameters in the auto-generated form.

### 4. Execute & View Response

Click **Execute Method** to call the SOAP service and view the response.

### 5. Save Configuration (Optional)

Click **Save Configuration** to persist your settings (including authentication credentials) for later use.

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

## Running Tests

```bash
# Install test dependencies (if not already installed)
pip install -r requirements.txt

# Run all tests
pytest tests/test_integration.py -v

# Run specific test
pytest tests/test_integration.py::TestIntegration::test_complete_workflow -v
```

### Test Coverage

The integration tests verify:
- ✅ WSDL loading and method discovery
- ✅ Parameter extraction
- ✅ SOAP method execution
- ✅ Configuration persistence
- ✅ Complete end-to-end workflow with CelsiusToFahrenheit

## Project Structure

```
flaskhealthcheck/
├── app.py                      # Main Flask application
├── soap_client.py              # SOAP client wrapper (zeep)
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── README.md                   # This file
├── .gitignore                  # Git ignore rules
├── templates/
│   └── index.html             # Main UI template
├── static/
│   ├── css/
│   │   └── style.css          # Modern CSS styles
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