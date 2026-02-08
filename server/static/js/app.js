/**
 * Main application logic for RemoteShell Manager
 */

// State management
const state = {
    devices: [],
    selectedDevice: null,
    history: [],
    currentCommand: null,
    filters: {
        device: '',
        status: ''
    }
};

// Initialize application
async function init() {
    console.log('Initializing RemoteShell Manager...');
    
    try {
        // Load initial data
        await loadDevices();
        await loadHistory();
        
        // Setup event listeners
        setupEventListeners();
        
        // Setup WebSocket connection
        setupWebSocket();
        
        // Start auto-refresh
        startAutoRefresh();
        
        console.log('Application initialized successfully');
    } catch (error) {
        console.error('Failed to initialize application:', error);
        showError('Failed to initialize application: ' + error.message);
    }
}

// Load devices list
async function loadDevices() {
    try {
        const devices = await api.fetchDevices();
        state.devices = devices;
        renderDevices(devices);
        updateDeviceSelect(devices);
        updateStats(devices);
    } catch (error) {
        console.error('Failed to load devices:', error);
        // Show placeholder when API is not available
        renderDevices([]);
        showMessage('No devices connected yet. Make sure the server is running.', 'info');
    }
}

// Render devices list
function renderDevices(devices) {
    const container = document.getElementById('devices-list');
    
    if (devices.length === 0) {
        container.innerHTML = '<div class="empty-state">No devices connected</div>';
        return;
    }
    
    container.innerHTML = devices.map(device => `
        <div class="device-item ${device.status || 'offline'}" data-device-id="${device.device_id}">
            <div class="device-header">
                <span class="status-indicator ${device.status || 'offline'}"></span>
                <strong>${device.device_id}</strong>
            </div>
            <div class="device-info">
                <span>Status: ${device.status || 'offline'}</span>
                <span>Queue: ${device.queue_size || 0}</span>
            </div>
        </div>
    `).join('');
    
    // Add click handlers to device items
    container.querySelectorAll('.device-item').forEach(item => {
        item.addEventListener('click', () => {
            const deviceId = item.dataset.deviceId;
            selectDevice(deviceId);
        });
    });
}

// Select a device
function selectDevice(deviceId) {
    state.selectedDevice = deviceId;
    document.getElementById('device-select').value = deviceId;
    
    // Highlight selected device
    document.querySelectorAll('.device-item').forEach(item => {
        if (item.dataset.deviceId === deviceId) {
            item.style.border = '2px solid #2563eb';
        } else {
            item.style.border = '';
        }
    });
}

// Update device select dropdown
function updateDeviceSelect(devices) {
    const select = document.getElementById('device-select');
    const historySelect = document.getElementById('history-device-filter');
    
    // Clear existing options except the first one
    select.innerHTML = '<option value="">Select device...</option>';
    historySelect.innerHTML = '<option value="">All Devices</option>';
    
    devices.forEach(device => {
        const option = document.createElement('option');
        option.value = device.device_id;
        option.textContent = device.device_id;
        select.appendChild(option);
        
        const historyOption = option.cloneNode(true);
        historySelect.appendChild(historyOption);
    });
}

// Update statistics in header
function updateStats(devices) {
    const totalDevices = devices.length;
    const onlineDevices = devices.filter(d => d.status === 'online').length;
    
    document.getElementById('total-devices').textContent = `Devices: ${totalDevices}`;
    document.getElementById('online-devices').textContent = `Online: ${onlineDevices}`;
}

// Send command
async function sendCommand(e) {
    e.preventDefault();
    
    const deviceId = document.getElementById('device-select').value;
    const command = document.getElementById('command-input').value.trim();
    const timeout = parseInt(document.getElementById('timeout-input').value);

    if (!deviceId || !command) {
        showError('Please select a device and enter a command');
        return;
    }

    try {
        showLoading(true);
        hideResult();
        
        const result = await api.sendCommand(deviceId, command, timeout);
        state.currentCommand = result.command_id;
        
        console.log('Command sent:', result);
        showMessage('Command sent successfully. Waiting for response...', 'info');
        
        // Poll for result
        pollCommandStatus(result.command_id);
    } catch (error) {
        console.error('Failed to send command:', error);
        showError('Failed to send command: ' + error.message);
        showLoading(false);
    }
}

// Poll command status
async function pollCommandStatus(commandId) {
    const maxAttempts = 60; // 1 minute with 1s intervals
    let attempts = 0;

    const poll = async () => {
        try {
            const status = await api.getCommandStatus(commandId);
            console.log('Command status:', status);
            
            if (status.status === 'completed' || status.status === 'failed') {
                displayResult(status);
                await loadHistory(); // Refresh history
                showLoading(false);
                return;
            }

            if (attempts < maxAttempts) {
                attempts++;
                setTimeout(poll, 1000);
            } else {
                showError('Command timed out while waiting for response');
                showLoading(false);
            }
        } catch (error) {
            console.error('Failed to get command status:', error);
            showError('Failed to get command status: ' + error.message);
            showLoading(false);
        }
    };

    poll();
}

// Display command result
function displayResult(result) {
    const panel = document.getElementById('result-panel');
    const content = document.getElementById('result-content');
    
    const statusClass = result.status === 'completed' ? 'completed' : 'failed';
    const statusIcon = result.status === 'completed' ? '✓' : '✗';
    
    panel.style.display = 'block';
    content.innerHTML = `
        <div class="result-header">
            <div><strong>Command:</strong> ${escapeHtml(result.command)}</div>
            <div><strong>Device:</strong> ${escapeHtml(result.device_id)}</div>
            <div><strong>Status:</strong> <span class="status-badge ${statusClass}">${result.status} ${statusIcon}</span></div>
            <div><strong>Exit Code:</strong> ${result.exit_code !== undefined ? result.exit_code : 'N/A'}</div>
            <div><strong>Execution Time:</strong> ${result.execution_time ? result.execution_time.toFixed(3) : 'N/A'}s</div>
        </div>
        <div class="result-output">
            <h4>stdout:</h4>
            <pre>${escapeHtml(result.stdout || '(empty)')}</pre>
            ${result.stderr ? `<h4>stderr:</h4><pre>${escapeHtml(result.stderr)}</pre>` : ''}
        </div>
    `;
    
    // Scroll to result
    panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Hide result panel
function hideResult() {
    document.getElementById('result-panel').style.display = 'none';
}

// Load and render history
async function loadHistory(filters = {}) {
    try {
        const mergedFilters = { ...state.filters, ...filters };
        const history = await api.getHistory(mergedFilters);
        state.history = history;
        renderHistory(history);
    } catch (error) {
        console.error('Failed to load history:', error);
        renderHistory([]);
    }
}

// Render history list
function renderHistory(history) {
    const container = document.getElementById('history-list');
    
    if (history.length === 0) {
        container.innerHTML = '<div class="empty-state">No command history</div>';
        return;
    }

    container.innerHTML = history.map(item => {
        const statusIcon = getStatusIcon(item.status);
        return `
            <div class="history-item" data-command-id="${item.command_id}">
                <div>
                    <span class="timestamp">${formatTime(item.created_at)}</span>
                    <strong>${escapeHtml(item.device_id)}</strong>
                    <code>${escapeHtml(item.command)}</code>
                </div>
                <span class="status-badge ${item.status}">${item.status} ${statusIcon}</span>
            </div>
        `;
    }).join('');
    
    // Add click handlers to view details
    container.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', async () => {
            const commandId = item.dataset.commandId;
            await viewCommandDetails(commandId);
        });
    });
}

// View command details
async function viewCommandDetails(commandId) {
    try {
        const result = await api.getCommandStatus(commandId);
        displayResult(result);
    } catch (error) {
        console.error('Failed to load command details:', error);
        showError('Failed to load command details: ' + error.message);
    }
}

// Filter history
async function filterHistory() {
    state.filters.device = document.getElementById('history-device-filter').value;
    state.filters.status = document.getElementById('history-status-filter').value;
    
    const filters = {};
    if (state.filters.device) filters.device_id = state.filters.device;
    if (state.filters.status) filters.status = state.filters.status;
    
    await loadHistory(filters);
}

// Clear filters
function clearFilters() {
    document.getElementById('history-device-filter').value = '';
    document.getElementById('history-status-filter').value = '';
    state.filters = { device: '', status: '' };
    loadHistory();
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('command-form').addEventListener('submit', sendCommand);
    document.getElementById('refresh-devices').addEventListener('click', () => {
        showMessage('Refreshing devices...', 'info');
        loadDevices();
    });
    document.getElementById('history-device-filter').addEventListener('change', filterHistory);
    document.getElementById('history-status-filter').addEventListener('change', filterHistory);
    document.getElementById('clear-filters').addEventListener('click', clearFilters);
}

// Setup WebSocket connection
function setupWebSocket() {
    // Connect to WebSocket
    wsClient.connect();
    
    // Handle device updates
    wsClient.on('device_status', (data) => {
        console.log('Device status update:', data);
        loadDevices();
    });
    
    // Handle command updates
    wsClient.on('command_update', (data) => {
        console.log('Command update:', data);
        if (data.command_id === state.currentCommand) {
            if (data.status === 'completed' || data.status === 'failed') {
                displayResult(data);
                loadHistory();
            }
        }
    });
    
    // Handle connection events
    wsClient.on('connected', () => {
        console.log('WebSocket connected');
        showMessage('Connected to server', 'success');
    });
    
    wsClient.on('disconnected', () => {
        console.log('WebSocket disconnected');
        showMessage('Disconnected from server. Attempting to reconnect...', 'warning');
    });
    
    wsClient.on('error', (error) => {
        console.error('WebSocket error:', error);
    });
}

// Auto-refresh devices every 10 seconds
function startAutoRefresh() {
    setInterval(() => {
        loadDevices();
    }, 10000);
}

// Utility functions

function formatTime(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
}

function getStatusIcon(status) {
    switch (status) {
        case 'completed':
            return '✓';
        case 'failed':
            return '✗';
        case 'pending':
            return '⏱';
        case 'executing':
            return '⚙';
        default:
            return '';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showError(message) {
    showMessage(message, 'error');
}

function showMessage(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = type === 'error' ? 'error-message' : 
                            type === 'success' ? 'success-message' : 
                            'loading';
    notification.textContent = message;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.maxWidth = '400px';
    notification.style.animation = 'slideIn 0.3s ease';
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

function showLoading(loading) {
    const btn = document.getElementById('send-btn');
    if (loading) {
        btn.disabled = true;
        btn.textContent = '⏳ Sending...';
    } else {
        btn.disabled = false;
        btn.textContent = '▶️ Send Command';
    }
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize on page load
document.addEventListener('DOMContentLoaded', init);
