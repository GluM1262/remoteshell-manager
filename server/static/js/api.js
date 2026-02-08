/**
 * API client for RemoteShell Manager
 */
class API {
    constructor(baseURL = '') {
        this.baseURL = baseURL;
    }

    /**
     * Fetch list of all devices
     * @returns {Promise<Array>} Array of device objects
     */
    async fetchDevices() {
        try {
            return await this._fetch('/api/devices');
        } catch (error) {
            console.error('Failed to fetch devices:', error);
            throw error;
        }
    }

    /**
     * Send command to a device
     * @param {string} deviceId - Target device ID
     * @param {string} command - Command to execute
     * @param {number} timeout - Command timeout in seconds
     * @returns {Promise<Object>} Command execution response
     */
    async sendCommand(deviceId, command, timeout = 30) {
        try {
            return await this._fetch('/api/command', {
                method: 'POST',
                body: JSON.stringify({
                    device_id: deviceId,
                    command: command,
                    timeout: timeout
                })
            });
        } catch (error) {
            console.error('Failed to send command:', error);
            throw error;
        }
    }

    /**
     * Get command execution status
     * @param {string} commandId - Command ID
     * @returns {Promise<Object>} Command status and results
     */
    async getCommandStatus(commandId) {
        try {
            return await this._fetch(`/api/command/${commandId}`);
        } catch (error) {
            console.error('Failed to get command status:', error);
            throw error;
        }
    }

    /**
     * Get command history with optional filters
     * @param {Object} filters - Filter options (device_id, status, limit)
     * @returns {Promise<Array>} Array of command history items
     */
    async getHistory(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.device_id) {
                params.append('device_id', filters.device_id);
            }
            if (filters.status) {
                params.append('status', filters.status);
            }
            if (filters.limit) {
                params.append('limit', filters.limit);
            }

            const queryString = params.toString();
            const endpoint = queryString ? `/api/history?${queryString}` : '/api/history';
            
            return await this._fetch(endpoint);
        } catch (error) {
            console.error('Failed to get history:', error);
            throw error;
        }
    }

    /**
     * Get command history for a specific device
     * @param {string} deviceId - Device ID
     * @param {number} limit - Maximum number of results
     * @returns {Promise<Array>} Array of command history items
     */
    async getDeviceHistory(deviceId, limit = 50) {
        try {
            return await this._fetch(`/api/devices/${deviceId}/history?limit=${limit}`);
        } catch (error) {
            console.error('Failed to get device history:', error);
            throw error;
        }
    }

    /**
     * Get system statistics
     * @returns {Promise<Object>} Statistics object
     */
    async getStatistics() {
        try {
            return await this._fetch('/api/statistics');
        } catch (error) {
            console.error('Failed to get statistics:', error);
            throw error;
        }
    }

    /**
     * Internal fetch wrapper
     * @private
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} Parsed JSON response
     */
    async _fetch(endpoint, options = {}) {
        const response = await fetch(this.baseURL + endpoint, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `API Error: ${response.statusText}`);
        }

        return response.json();
    }
}

// Create global API instance
const api = new API();
