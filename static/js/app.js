// Main JavaScript for SOAP Health Check App

let currentWsdlUrl = '';
let currentMethod = '';
let currentParams = {};
let currentAuth = {};

// DOM Elements
const wsdlUrlInput = document.getElementById('wsdlUrl');
const loadWsdlBtn = document.getElementById('loadWsdlBtn');
const loadConfigBtn = document.getElementById('loadConfigBtn');
const wsdlStatus = document.getElementById('wsdlStatus');

// Auth elements
const authDomain = document.getElementById('authDomain');
const authUsername = document.getElementById('authUsername');
const authPassword = document.getElementById('authPassword');

const methodSection = document.getElementById('methodSection');
const methodSelect = document.getElementById('methodSelect');
const loadParamsBtn = document.getElementById('loadParamsBtn');
const methodStatus = document.getElementById('methodStatus');

const paramsSection = document.getElementById('paramsSection');
const paramsForm = document.getElementById('paramsForm');
const paramsList = document.getElementById('paramsList');
const saveConfigBtn = document.getElementById('saveConfigBtn');
const paramsStatus = document.getElementById('paramsStatus');

const responseSection = document.getElementById('responseSection');
const responseStatus = document.getElementById('responseStatus');
const responseBody = document.getElementById('responseBody');

// Utility functions
function showStatus(element, message, type) {
    element.textContent = message;
    element.className = `status-message ${type}`;
}

function hideStatus(element) {
    element.style.display = 'none';
}

function setButtonLoading(button, loading) {
    if (loading) {
        button.disabled = true;
        button.classList.add('loading');
        button.dataset.originalText = button.textContent;
        button.textContent = 'Loading...';
    } else {
        button.disabled = false;
        button.classList.remove('loading');
        if (button.dataset.originalText) {
            button.textContent = button.dataset.originalText;
        }
    }
}

// Event Handlers
loadWsdlBtn.addEventListener('click', async () => {
    const wsdlUrl = wsdlUrlInput.value.trim();
    
    if (!wsdlUrl) {
        showStatus(wsdlStatus, 'Please enter a WSDL URL', 'error');
        return;
    }
    
    setButtonLoading(loadWsdlBtn, true);
    hideStatus(wsdlStatus);
    
    try {
        // Collect authentication credentials if provided
        const auth = {};
        const username = authUsername.value.trim();
        const password = authPassword.value.trim();
        const domain = authDomain.value.trim();
        
        if (username || password) {
            auth.username = username;
            auth.password = password;
            if (domain) {
                auth.domain = domain;
            }
            currentAuth = auth;
        } else {
            currentAuth = {};
        }
        
        const response = await fetch('/api/load-wsdl', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                wsdl_url: wsdlUrl,
                auth: auth
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            currentWsdlUrl = wsdlUrl;
            
            // Populate method dropdown
            methodSelect.innerHTML = '<option value="">-- Select a method --</option>';
            data.methods.forEach(method => {
                const option = document.createElement('option');
                option.value = method;
                option.textContent = method;
                methodSelect.appendChild(option);
            });
            
            showStatus(wsdlStatus, `✓ WSDL loaded successfully! Found ${data.methods.length} methods.`, 'success');
            methodSection.style.display = 'block';
            
            // Hide other sections
            paramsSection.style.display = 'none';
            responseSection.style.display = 'none';
        } else {
            showStatus(wsdlStatus, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(wsdlStatus, `Network error: ${error.message}`, 'error');
    } finally {
        setButtonLoading(loadWsdlBtn, false);
    }
});

loadParamsBtn.addEventListener('click', async () => {
    const methodName = methodSelect.value;
    
    if (!methodName) {
        showStatus(methodStatus, 'Please select a method', 'error');
        return;
    }
    
    setButtonLoading(loadParamsBtn, true);
    hideStatus(methodStatus);
    
    try {
        const response = await fetch('/api/get-method-params', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ method_name: methodName })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            currentMethod = methodName;
            
            // Build parameters form
            paramsList.innerHTML = '';
            
            if (data.params.length === 0) {
                paramsList.innerHTML = '<p style="color: #64748b;">This method requires no parameters.</p>';
            } else {
                data.params.forEach(param => {
                    const paramDiv = document.createElement('div');
                    paramDiv.className = 'param-input';
                    
                    const label = document.createElement('label');
                    label.className = 'param-label';
                    label.innerHTML = `
                        ${param.name}
                        ${param.required ? '<span class="required">*</span>' : ''}
                        <span class="type">(${param.type})</span>
                    `;
                    
                    const input = document.createElement('input');
                    input.type = 'text';
                    input.name = param.name;
                    input.className = 'input-field';
                    input.placeholder = `Enter ${param.name}`;
                    input.required = param.required;
                    
                    paramDiv.appendChild(label);
                    paramDiv.appendChild(input);
                    paramsList.appendChild(paramDiv);
                });
            }
            
            showStatus(methodStatus, `✓ Parameters loaded for method: ${methodName}`, 'success');
            paramsSection.style.display = 'block';
            responseSection.style.display = 'none';
        } else {
            showStatus(methodStatus, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(methodStatus, `Network error: ${error.message}`, 'error');
    } finally {
        setButtonLoading(loadParamsBtn, false);
    }
});

paramsForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    hideStatus(paramsStatus);
    
    // Collect parameters
    const formData = new FormData(paramsForm);
    const params = {};
    formData.forEach((value, key) => {
        if (value.trim()) {
            params[key] = value.trim();
        }
    });
    
    currentParams = params;
    
    const submitBtn = paramsForm.querySelector('button[type="submit"]');
    setButtonLoading(submitBtn, true);
    
    try {
        const response = await fetch('/api/execute-method', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                method_name: currentMethod,
                params: params
            })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showStatus(paramsStatus, '✓ Method executed successfully!', 'success');
            
            // Display response
            responseStatus.textContent = 'Success';
            responseStatus.className = 'status-badge success';
            responseBody.textContent = JSON.stringify(data.result, null, 2);
            responseSection.style.display = 'block';
        } else {
            showStatus(paramsStatus, `Error: ${data.error}`, 'error');
            
            // Display error response
            responseStatus.textContent = 'Error';
            responseStatus.className = 'status-badge error';
            responseBody.textContent = data.error;
            responseSection.style.display = 'block';
        }
    } catch (error) {
        showStatus(paramsStatus, `Network error: ${error.message}`, 'error');
    } finally {
        setButtonLoading(submitBtn, false);
    }
});

saveConfigBtn.addEventListener('click', async () => {
    hideStatus(paramsStatus);
    
    const config = {
        wsdl_url: currentWsdlUrl,
        method_name: currentMethod,
        params: currentParams,
        auth: currentAuth
    };
    
    setButtonLoading(saveConfigBtn, true);
    
    try {
        const response = await fetch('/api/save-config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showStatus(paramsStatus, '✓ Configuration saved successfully!', 'success');
        } else {
            showStatus(paramsStatus, `Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(paramsStatus, `Network error: ${error.message}`, 'error');
    } finally {
        setButtonLoading(saveConfigBtn, false);
    }
});

loadConfigBtn.addEventListener('click', async () => {
    setButtonLoading(loadConfigBtn, true);
    hideStatus(wsdlStatus);
    
    try {
        const response = await fetch('/api/load-config');
        const data = await response.json();
        
        if (response.ok && data.success && data.config) {
            const config = data.config;
            
            // Set WSDL URL
            wsdlUrlInput.value = config.wsdl_url;
            
            // Restore authentication fields if present
            if (config.auth) {
                authDomain.value = config.auth.domain || '';
                authUsername.value = config.auth.username || '';
                authPassword.value = config.auth.password || '';
                currentAuth = config.auth;
            }
            
            showStatus(wsdlStatus, '✓ Configuration loaded! Click "Load WSDL" to apply.', 'info');
            
            // Auto-load WSDL if requested
            if (confirm('Configuration loaded. Load WSDL automatically?')) {
                loadWsdlBtn.click();
                
                // Wait a bit and select method
                setTimeout(() => {
                    methodSelect.value = config.method_name;
                    
                    // Auto-load params if requested
                    if (config.method_name) {
                        loadParamsBtn.click();
                        
                        // Wait and populate params
                        setTimeout(() => {
                            Object.keys(config.params || {}).forEach(key => {
                                const input = paramsForm.querySelector(`[name="${key}"]`);
                                if (input) {
                                    input.value = config.params[key];
                                }
                            });
                        }, 1000);
                    }
                }, 1000);
            }
        } else {
            showStatus(wsdlStatus, data.message || 'No saved configuration found', 'info');
        }
    } catch (error) {
        showStatus(wsdlStatus, `Network error: ${error.message}`, 'error');
    } finally {
        setButtonLoading(loadConfigBtn, false);
    }
});

// Set default WSDL for demo
window.addEventListener('DOMContentLoaded', () => {
    wsdlUrlInput.value = 'https://www.w3schools.com/xml/tempconvert.asmx?WSDL';
});
