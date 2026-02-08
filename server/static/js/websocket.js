/**
 * WebSocket client for real-time updates
 */
class WSClient {
    constructor() {
        this.ws = null;
        this.listeners = {};
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
        this.isConnecting = false;
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
            console.log('WebSocket already connected or connecting');
            return;
        }

        this.isConnecting = true;
        
        // Determine WebSocket URL based on current location
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        console.log('Connecting to WebSocket:', wsUrl);

        try {
            this.ws = new WebSocket(wsUrl);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.emit('connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('WebSocket message received:', data);
                    
                    // Emit event based on message type
                    if (data.type) {
                        this.emit(data.type, data);
                    }
                    
                    // Always emit generic 'message' event
                    this.emit('message', data);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };

            this.ws.onclose = (event) => {
                console.log('WebSocket closed:', event.code, event.reason);
                this.isConnecting = false;
                this.emit('disconnected', event);

                // Attempt to reconnect if not closed intentionally
                if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
                    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                    
                    setTimeout(() => {
                        this.connect();
                    }, delay);
                } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
                    console.error('Max reconnection attempts reached');
                    this.emit('reconnect_failed');
                }
            };
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.isConnecting = false;
            this.emit('error', error);
        }
    }

    /**
     * Disconnect from WebSocket server
     */
    disconnect() {
        if (this.ws) {
            console.log('Disconnecting WebSocket');
            this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
            this.ws.close();
            this.ws = null;
        }
    }

    /**
     * Send message through WebSocket
     * @param {Object} message - Message to send
     */
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
            console.log('WebSocket message sent:', message);
        } else {
            console.error('WebSocket is not connected');
            throw new Error('WebSocket is not connected');
        }
    }

    /**
     * Register event listener
     * @param {string} event - Event name
     * @param {Function} callback - Event callback
     */
    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    /**
     * Remove event listener
     * @param {string} event - Event name
     * @param {Function} callback - Event callback to remove
     */
    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    /**
     * Emit event to all registered listeners
     * @private
     * @param {string} event - Event name
     * @param {*} data - Event data
     */
    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for '${event}':`, error);
                }
            });
        }
    }

    /**
     * Check if WebSocket is connected
     * @returns {boolean} Connection status
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

// Create global WebSocket client instance
const wsClient = new WSClient();
