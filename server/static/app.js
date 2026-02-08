const API_BASE = window.location.origin;

function showMessage(message, type = 'info') {
    const container = document.getElementById('messageContainer');
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.textContent = message;
    container.appendChild(div);
    
    setTimeout(() => div.remove(), 5000);
}

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
        }
        
        return data;
    } catch (error) {
        showMessage(error.message, 'error');
        throw error;
    }
}

async function refreshDevices() {
    try {
        const data = await apiRequest('/api/devices');
        const tbody = document.getElementById('devicesBody');
        const select = document.getElementById('deviceSelect');
        
        if (data.devices.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No devices registered</td></tr>';
            select.innerHTML = '<option value="">No devices available</option>';
            return;
        }
        
        tbody.innerHTML = data.devices.map(device => `
            <tr>
                <td>${device.device_id}</td>
                <td>
                    <span class="badge ${device.is_online ? 'success' : 'warning'}">
                        ${device.is_online ? 'Online' : 'Offline'}
                    </span>
                </td>
                <td class="timestamp">${formatTimestamp(device.last_seen)}</td>
                <td>
                    <button onclick="viewDeviceHistory('${device.device_id}')" style="padding: 5px 10px; font-size: 12px;">History</button>
                </td>
            </tr>
        `).join('');
        
        select.innerHTML = '<option value="">Select device...</option>' + 
            data.devices.map(device => 
                `<option value="${device.device_id}">${device.device_id} ${device.is_online ? '(online)' : '(offline)'}</option>`
            ).join('');
    } catch (error) {
        console.error('Error refreshing devices:', error);
    }
}

async function sendCommand() {
    const deviceId = document.getElementById('deviceSelect').value;
    const command = document.getElementById('commandInput').value;
    const timeout = document.getElementById('timeoutInput').value;
    
    if (!deviceId) {
        showMessage('Please select a device', 'error');
        return;
    }
    
    if (!command) {
        showMessage('Please enter a command', 'error');
        return;
    }
    
    try {
        let url = `/api/devices/${deviceId}/command?command=${encodeURIComponent(command)}`;
        if (timeout) {
            url += `&timeout=${timeout}`;
        }
        
        const data = await apiRequest(url, { method: 'POST' });
        showMessage(`Command ${data.status}: ${command}`, 'success');
        
        // Clear input
        document.getElementById('commandInput').value = '';
        
        // Refresh history after a delay
        setTimeout(refreshHistory, 1000);
    } catch (error) {
        console.error('Error sending command:', error);
    }
}

async function refreshHistory() {
    try {
        const data = await apiRequest('/api/history?limit=50');
        const tbody = document.getElementById('historyBody');
        
        if (data.history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No command history</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.history.map(entry => `
            <tr>
                <td class="timestamp">${formatTimestamp(entry.created_at)}</td>
                <td>${entry.device_id}</td>
                <td><code>${escapeHtml(entry.command)}</code></td>
                <td>
                    <span class="badge ${getStatusClass(entry.status)}">
                        ${entry.status}
                    </span>
                </td>
                <td>${entry.exit_code !== null ? entry.exit_code : '-'}</td>
                <td>${entry.execution_time ? entry.execution_time.toFixed(2) + 's' : '-'}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error refreshing history:', error);
    }
}

async function viewDeviceHistory(deviceId) {
    showMessage(`Viewing history for ${deviceId}`, 'info');
}

function formatTimestamp(timestamp) {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
}

function getStatusClass(status) {
    if (status === 'completed' || status === 'sent') return 'success';
    if (status === 'pending' || status === 'queued') return 'warning';
    return 'error';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-refresh
setInterval(() => {
    refreshDevices();
    refreshHistory();
}, 5000);

// Initial load
refreshDevices();
refreshHistory();

// Enable Enter key for command input
document.getElementById('commandInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        sendCommand();
    }
});
