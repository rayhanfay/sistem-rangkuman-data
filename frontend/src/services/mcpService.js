import { auth } from '../utils/firebase';

class McpService {
  constructor() {
    this.socket = null;
    this.pendingRequests = new Map();
    this.status = 'disconnected';
    this.statusListeners = [];
    this.eventListeners = new Map(); 
    this.requestIdCounter = 1;
  }

  connect() {
    if (this.socket && this.socket.readyState < 2) {
      console.warn("MCP service already connected or connecting.");
      return;
    }
    
    this.setStatus('connecting');
    
    const apiUrl = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
    const wsUrl = apiUrl.replace(/^http/, 'ws') + '/mcp';
    
    console.log(`Connecting to MCP server at ${wsUrl}`);

    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log("MCP WebSocket connection established.");
      this.setStatus('connected');
      this.initialize();
    };

    this.socket.onmessage = (event) => {
      try {
        const response = JSON.parse(event.data);
        console.log("MCP Message Received:", response);
        
        if (response.id && this.pendingRequests.has(response.id)) {
          const { resolve, reject } = this.pendingRequests.get(response.id);
          if (response.error) {
            reject(new Error(`MCP Error ${response.error.code}: ${response.error.message}`));
          } else {
            resolve(response.result);
          }
          this.pendingRequests.delete(response.id);
        } 
        else if (response.method && this.eventListeners.has(response.method)) {
          this.eventListeners.get(response.method).forEach(callback => callback(response.params));
        }
      } catch (error) {
        console.error("Failed to parse MCP message:", error);
      }
    };

    this.socket.onerror = (error) => {
      console.error("MCP WebSocket error:", error);
      this.setStatus('disconnected');
    };

    this.socket.onclose = () => {
      console.log("MCP WebSocket connection closed.");
      this.setStatus('disconnected');
      this.pendingRequests.forEach(({ reject }) => reject(new Error('Connection closed')));
      this.pendingRequests.clear();
    };
  }

  async call(method, params = {}) {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      return Promise.reject(new Error('MCP service is not connected.'));
    }
    
    const requestId = this.requestIdCounter++;
    const request = {
      jsonrpc: '2.0',
      method,
      params,
      id: requestId,
    };

    console.log("MCP Request Sent:", request);
    this.socket.send(JSON.stringify(request));

    return new Promise((resolve, reject) => {
      this.pendingRequests.set(requestId, { resolve, reject });
    });
  }

  async initialize() {
    try {
      const result = await this.call('initialize', {
        clientInfo: { name: 'PHR Web Frontend', version: '1.0.0' },
        protocolVersion: '2024-11-05'
      });
      console.log("MCP Server Initialized:", result);
    } catch (error) {
      console.error("MCP Initialization failed:", error);
    }
  }

  on(eventName, callback) {
    if (!this.eventListeners.has(eventName)) {
        this.eventListeners.set(eventName, []);
    }
    this.eventListeners.get(eventName).push(callback);
    return () => {
        const listeners = this.eventListeners.get(eventName);
        if (listeners) {
            this.eventListeners.set(eventName, listeners.filter(cb => cb !== callback));
        }
    };
  }

  setStatus(newStatus) {
    this.status = newStatus;
    this.statusListeners.forEach(listener => listener(newStatus));
  }
  
  onStatusChange(callback) {
    this.statusListeners.push(callback);
    return () => {
      this.statusListeners = this.statusListeners.filter(l => l !== callback);
    };
  }
}

const mcpServiceInstance = new McpService();
export default mcpServiceInstance;