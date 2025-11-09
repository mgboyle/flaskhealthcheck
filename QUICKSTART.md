# Quick Start Guide

## Installation

### Option 1: Local Python Installation

1. Clone the repository:
```bash
git clone https://github.com/mgboyle/flaskhealthcheck.git
cd flaskhealthcheck
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

### Option 2: Docker

1. Build the Docker image:
```bash
docker build -t flask-soap-healthcheck .
```

2. Run the container:
```bash
docker run -p 5000:5000 flask-soap-healthcheck
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Using the Application

### Step 1: Load a WSDL

Enter a WSDL URL in the input field. For example:
```
https://www.w3schools.com/xml/tempconvert.asmx?WSDL
```

Click **Load WSDL** to parse the WSDL and discover available methods.

### Step 2: Select a Method

From the dropdown, select a method you want to test. For example:
- `CelsiusToFahrenheit`
- `FahrenheitToCelsius`

Click **Load Parameters** to see the required parameters for this method.

### Step 3: Enter Parameters

Fill in the parameter values in the dynamically generated form. For example:
- **Celsius**: `0` (to convert to Fahrenheit)

### Step 4: Execute and View Response

Click **Execute Method** to call the SOAP service.

The response will be displayed in a formatted JSON view below. For example:
```json
{
  "result": "32"
}
```

### Step 5: Save Configuration (Optional)

Click **Save Configuration** to persist your settings to a `config.json` file.

Later, click **Load Saved Config** to restore your saved configuration.

## Testing

Run the integration tests:
```bash
pytest tests/test_integration.py -v
```

Expected output:
```
11 passed in 0.27s
```

## Troubleshooting

### Port Already in Use

If port 5000 is already in use, you can change it by modifying `app.py`:
```python
app.run(host='0.0.0.0', port=8080, debug=True)
```

### WSDL Loading Fails

- Ensure the WSDL URL is accessible from your network
- Check if the WSDL endpoint requires authentication
- Verify the URL returns valid XML

### Dependencies Not Installing

- Ensure you have Python 3.11 or later installed
- Try upgrading pip: `pip install --upgrade pip`
- Use a virtual environment: `python -m venv venv && source venv/bin/activate`

## Example WSDL Endpoints

Try these public SOAP services:

1. **Temperature Converter** (W3Schools)
   - WSDL: `https://www.w3schools.com/xml/tempconvert.asmx?WSDL`
   - Methods: `CelsiusToFahrenheit`, `FahrenheitToCelsius`

2. **Country Information** (Note: May not always be available)
   - WSDL: `http://webservices.oorsprong.org/websamples.countryinfo/CountryInfoService.wso?WSDL`

## API Documentation

See the main [README.md](README.md) for detailed API endpoint documentation.
