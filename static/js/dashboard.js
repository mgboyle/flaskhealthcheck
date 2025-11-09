// Dashboard JavaScript for Service Health Monitor

let currentServiceId = null;
let services = {};

// DOM Elements
const servicesContainer = document.getElementById('servicesContainer');
const addServiceBtn = document.getElementById('addServiceBtn');
const runAllChecksBtn = document.getElementById('runAllChecksBtn');
const refreshBtn = document.getElementById('refreshBtn');
const serviceModal = document.getElementById('serviceModal');
const serviceForm = document.getElementById('serviceForm');
const serviceType = document.getElementById('serviceType');
const soapFields = document.getElementById('soapFields');
const restFields = document.getElementById('restFields');
const addRuleBtn = document.getElementById('addRuleBtn');
const validationRules = document.getElementById('validationRules');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadServices();
    setupEventListeners();
});

function setupEventListeners() {
    addServiceBtn.addEventListener('click', () => openServiceModal());
    refreshBtn.addEventListener('click', () => loadServices());
    runAllChecksBtn.addEventListener('click', () => runAllHealthchecks());
    
    // Service type change
    serviceType.addEventListener('change', () => {
        if (serviceType.value === 'soap') {
            soapFields.style.display = 'block';
            restFields.style.display = 'none';
        } else {
            soapFields.style.display = 'none';
            restFields.style.display = 'block';
        }
    });
    
    // Modal close
    document.querySelectorAll('.close-modal').forEach(el => {
        el.addEventListener('click', () => closeServiceModal());
    });
    
    // Click outside modal to close
    window.addEventListener('click', (e) => {
        if (e.target === serviceModal) {
            closeServiceModal();
        }
    });
    
    // Add validation rule
    addRuleBtn.addEventListener('click', () => addValidationRule());
    
    // Service form submit
    serviceForm.addEventListener('submit', (e) => {
        e.preventDefault();
        saveService();
    });
}

async function loadServices() {
    try {
        const response = await fetch('/api/services');
        const data = await response.json();
        
        if (data.success) {
            services = data.services;
            renderServices();
        }
    } catch (error) {
        console.error('Error loading services:', error);
        showNotification('Failed to load services', 'error');
    }
}

function renderServices() {
    if (Object.keys(services).length === 0) {
        servicesContainer.innerHTML = '<p class="empty-state">No services configured. Click "Add Service" to get started.</p>';
        return;
    }
    
    servicesContainer.innerHTML = '';
    
    Object.values(services).forEach(service => {
        const serviceElement = createServiceElement(service);
        servicesContainer.appendChild(serviceElement);
    });
}

function createServiceElement(service) {
    const div = document.createElement('div');
    div.className = 'service-item';
    div.setAttribute('data-service-id', service.id);
    
    const lastCheck = service.last_check ? new Date(service.last_check).toLocaleString() : 'Never';
    const lastResult = service.last_result;
    
    let statusHtml = '';
    if (lastResult) {
        const statusClass = lastResult.success ? 'success' : 'error';
        const statusText = lastResult.success ? 'Healthy' : 'Failed';
        statusHtml = `
            <div class="service-status">
                <span class="status-indicator ${statusClass}"></span>
                <span class="status-text"><strong>Status:</strong> ${statusText}</span>
                <span class="status-text"><strong>Last Check:</strong> ${lastCheck}</span>
            </div>
        `;
        
        if (!lastResult.success || (lastResult.validation && !lastResult.validation.passed)) {
            const errorMsg = lastResult.error || 'Validation failed';
            statusHtml += `
                <div class="service-result">
                    <strong>Error:</strong> ${errorMsg}
            `;
            
            if (lastResult.validation && lastResult.validation.failures.length > 0) {
                statusHtml += `
                    <div class="validation-failures">
                        <strong>Validation Failures:</strong>
                        <ul>
                            ${lastResult.validation.failures.map(f => `<li>${f}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            statusHtml += '</div>';
        }
    }
    
    div.innerHTML = `
        <div class="service-header">
            <div class="service-info">
                <div class="service-name">${service.name}</div>
                <div class="service-meta">
                    <span class="service-type-badge ${service.type}">${service.type.toUpperCase()}</span>
                    <span>${service.endpoint}</span>
                    ${service.method ? `<span>Method: ${service.method}</span>` : ''}
                </div>
            </div>
            <div class="service-actions">
                <button class="btn btn-sm btn-success" onclick="runHealthcheck('${service.id}')">▶ Check</button>
                <button class="btn btn-sm btn-secondary" onclick="editService('${service.id}')">✏️ Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteService('${service.id}')">🗑️ Delete</button>
            </div>
        </div>
        ${statusHtml}
    `;
    
    return div;
}

function openServiceModal(serviceId = null) {
    currentServiceId = serviceId;
    serviceForm.reset();
    validationRules.innerHTML = '';
    
    if (serviceId && services[serviceId]) {
        // Edit mode
        const service = services[serviceId];
        document.getElementById('modalTitle').textContent = 'Edit Service';
        document.getElementById('serviceName').value = service.name;
        document.getElementById('serviceType').value = service.type;
        document.getElementById('serviceEndpoint').value = service.endpoint;
        
        // Type-specific fields
        if (service.type === 'soap') {
            document.getElementById('soapMethod').value = service.method || '';
            soapFields.style.display = 'block';
            restFields.style.display = 'none';
        } else {
            document.getElementById('restMethod').value = service.method || 'GET';
            document.getElementById('restEndpoint').value = service.rest_endpoint || '';
            soapFields.style.display = 'none';
            restFields.style.display = 'block';
        }
        
        // Auth fields
        if (service.auth) {
            document.getElementById('authType').value = service.auth.auth_type || '';
            document.getElementById('authDomain').value = service.auth.domain || '';
            document.getElementById('authUsername').value = service.auth.username || '';
            document.getElementById('authPassword').value = service.auth.password || '';
        }
        
        // Validation rules
        if (service.validation_rules) {
            service.validation_rules.forEach(rule => {
                addValidationRule(rule);
            });
        }
    } else {
        // Add mode
        document.getElementById('modalTitle').textContent = 'Add Service';
    }
    
    serviceModal.classList.add('show');
}

function closeServiceModal() {
    serviceModal.classList.remove('show');
    currentServiceId = null;
}

async function saveService() {
    const serviceData = {
        name: document.getElementById('serviceName').value,
        type: document.getElementById('serviceType').value,
        endpoint: document.getElementById('serviceEndpoint').value
    };
    
    // Type-specific fields
    if (serviceData.type === 'soap') {
        serviceData.method = document.getElementById('soapMethod').value;
        serviceData.params = {};
    } else {
        serviceData.method = document.getElementById('restMethod').value;
        serviceData.rest_endpoint = document.getElementById('restEndpoint').value;
    }
    
    // Auth
    const authType = document.getElementById('authType').value;
    if (authType) {
        serviceData.auth = {
            auth_type: authType,
            domain: document.getElementById('authDomain').value,
            username: document.getElementById('authUsername').value,
            password: document.getElementById('authPassword').value
        };
    }
    
    // Validation rules
    serviceData.validation_rules = collectValidationRules();
    
    try {
        const url = currentServiceId ? `/api/services/${currentServiceId}` : '/api/services';
        const method = currentServiceId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(serviceData)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Service saved successfully', 'success');
            closeServiceModal();
            loadServices();
        } else {
            showNotification(data.error || 'Failed to save service', 'error');
        }
    } catch (error) {
        console.error('Error saving service:', error);
        showNotification('Failed to save service', 'error');
    }
}

function addValidationRule(ruleData = null) {
    const ruleDiv = document.createElement('div');
    ruleDiv.className = 'rule-item';
    
    const ruleId = Date.now();
    
    ruleDiv.innerHTML = `
        <div class="rule-header">
            <strong>Validation Rule</strong>
            <button type="button" class="btn btn-danger btn-sm" onclick="this.closest('.rule-item').remove()">Remove</button>
        </div>
        <div class="form-group">
            <label>Rule Type</label>
            <select class="input-field rule-type" data-rule-id="${ruleId}">
                <option value="status_code">Status Code</option>
                <option value="contains">Contains Text</option>
                <option value="regex">Regex Match</option>
                <option value="json_path">JSON Path</option>
                <option value="equals">Field Equals</option>
            </select>
        </div>
        <div class="form-group">
            <label>Field/Path</label>
            <input type="text" class="input-field rule-field" placeholder="e.g., result.value">
        </div>
        <div class="form-group">
            <label>Expected Value</label>
            <input type="text" class="input-field rule-value" placeholder="e.g., 200, success">
        </div>
        <div class="form-group">
            <label>Pattern (for regex)</label>
            <input type="text" class="input-field rule-pattern" placeholder="e.g., ^\\d+$">
        </div>
    `;
    
    if (ruleData) {
        ruleDiv.querySelector('.rule-type').value = ruleData.type || 'status_code';
        ruleDiv.querySelector('.rule-field').value = ruleData.field || '';
        ruleDiv.querySelector('.rule-value').value = ruleData.value || '';
        ruleDiv.querySelector('.rule-pattern').value = ruleData.pattern || '';
    }
    
    validationRules.appendChild(ruleDiv);
}

function collectValidationRules() {
    const rules = [];
    document.querySelectorAll('.rule-item').forEach(ruleDiv => {
        const rule = {
            type: ruleDiv.querySelector('.rule-type').value,
            field: ruleDiv.querySelector('.rule-field').value,
            value: ruleDiv.querySelector('.rule-value').value,
            pattern: ruleDiv.querySelector('.rule-pattern').value
        };
        rules.push(rule);
    });
    return rules;
}

async function runHealthcheck(serviceId) {
    try {
        showNotification(`Running health check for ${services[serviceId].name}...`, 'info');
        
        const response = await fetch(`/api/services/${serviceId}/healthcheck`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            if (result.success) {
                showNotification('Health check passed!', 'success');
            } else {
                showNotification('Health check failed', 'error');
            }
            loadServices();
        } else {
            showNotification(data.error || 'Health check failed', 'error');
        }
    } catch (error) {
        console.error('Error running health check:', error);
        showNotification('Failed to run health check', 'error');
    }
}

async function runAllHealthchecks() {
    try {
        showNotification('Running health checks for all services...', 'info');
        
        const response = await fetch('/api/healthcheck/all', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            const total = Object.keys(data.results).length;
            const passed = Object.values(data.results).filter(r => r.success).length;
            showNotification(`Health checks complete: ${passed}/${total} passed`, 'success');
            loadServices();
        } else {
            showNotification('Failed to run health checks', 'error');
        }
    } catch (error) {
        console.error('Error running all health checks:', error);
        showNotification('Failed to run health checks', 'error');
    }
}

function editService(serviceId) {
    openServiceModal(serviceId);
}

async function deleteService(serviceId) {
    if (!confirm(`Are you sure you want to delete ${services[serviceId].name}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/services/${serviceId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Service deleted successfully', 'success');
            loadServices();
        } else {
            showNotification(data.error || 'Failed to delete service', 'error');
        }
    } catch (error) {
        console.error('Error deleting service:', error);
        showNotification('Failed to delete service', 'error');
    }
}

function showNotification(message, type) {
    // Simple notification - could be enhanced with a toast library
    console.log(`[${type.toUpperCase()}] ${message}`);
    alert(message);
}
