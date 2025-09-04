// API service for communicating with FastAPI backend
class ApiService {
  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
    this.sessionId = null;
    this.authToken = null;
    this.userId = null;
  }

  // Set authentication token
  setAuthToken(token) {
    this.authToken = token;
  }

  // Set session ID
  setSessionId(sessionId) {
    this.sessionId = sessionId;
  }

  // Get headers with authentication
  getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    return headers;
  }

  // Get multipart headers for file uploads
  getMultipartHeaders() {
    const headers = {};
    
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    
    return headers;
  }

  async makeRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const defaultOptions = {
      headers: this.getHeaders(),
      credentials: 'include', // Include cookies for session management
    };

    const config = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Authentication methods
  async register(userData) {
    return this.makeRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  async login(credentials) {
    const response = await this.makeRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials)
    });
    
    if (response.success) {
      this.setAuthToken(response.data.access_token);
      this.setSessionId(response.data.session_id);
      this.userId = response.data.user.id;
    }
    
    return response;
  }

  // Session management
  async createSession() {
    return this.makeRequest('/sessions', {
      method: 'POST'
    });
  }

  async startSession() {
    // Check if we already have a session ID from login
    let sessionId = this.sessionId || localStorage.getItem('sessionId');
    
    if (!sessionId) {
      // Create a new session only if we don't have one
      const sessionResponse = await this.createSession();
      if (sessionResponse.success) {
        sessionId = sessionResponse.data.session_id;
        this.setSessionId(sessionId);
        localStorage.setItem('sessionId', sessionId);
      } else {
        throw new Error('Failed to create session');
      }
    } else {
      // Use existing session
      this.setSessionId(sessionId);
    }
    
    // Get initial session state
    try {
      const stateResponse = await this.getSessionState();
      return {
        message: "Hello! I'm your MediClaim AI assistant. I can help you process insurance claims by analyzing your policy documents and medical bills. How can I assist you today?",
        state: stateResponse.current_step || 'initial',
        progress: 0
      };
    } catch (error) {
      return {
        message: "Hello! I'm your MediClaim AI assistant. How can I help you today?",
        state: 'initial',
        progress: 0
      };
    }
  }

  async getSessionState() {
    return this.makeRequest(`/sessions/${this.sessionId}/state`);
  }

  // Document upload
  async uploadDocument(file, fileType) {
    // Ensure we have a session ID
    if (!this.sessionId) {
      throw new Error('No active session. Please refresh the page.');
    }
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);
    formData.append('session_id', this.sessionId);

    console.log('Uploading document:', {
      fileName: file.name,
      fileType: fileType,
      sessionId: this.sessionId,
      hasAuthToken: !!this.authToken
    });

    // For file uploads, bypass makeRequest to avoid JSON Content-Type header
    const url = `${this.baseURL}/upload-document`;
    const headers = {};
    
    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }
    // DO NOT set Content-Type - let browser set it with boundary

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        headers: headers,
        credentials: 'include'
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Upload error response:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }
      
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Upload request failed:', error);
      throw error;
    }
  }

  // Chat with AI agent
  async sendMessage(message) {
    return this.makeRequest('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message: message,
        session_id: this.sessionId
      })
    });
  }

  // Get vendors
  async getVendors() {
    return this.makeRequest('/vendors');
  }

  // Claim management
  async createClaim(claimData) {
    return this.makeRequest('/claims', {
      method: 'POST',
      body: JSON.stringify(claimData)
    });
  }

  async getClaim(claimId) {
    return this.makeRequest(`/claims/${claimId}`);
  }

  async updateClaim(claimId, updateData) {
    return this.makeRequest(`/claims/${claimId}`, {
      method: 'PUT',
      body: JSON.stringify(updateData)
    });
  }

  // Coverage analysis
  async calculateCoverage(policyDocumentId, invoiceDocumentId) {
    const formData = new FormData();
    formData.append('policy_document_id', policyDocumentId);
    formData.append('invoice_document_id', invoiceDocumentId);

    return this.makeRequest('/calculate-coverage', {
      method: 'POST',
      body: formData,
      headers: this.getMultipartHeaders()
    });
  }

  // Form generation and download
  async generateClaimForm(claimId, vendorId) {
    return this.makeRequest('/file-claim', {
      method: 'POST',
      body: JSON.stringify({
        claim_id: claimId,
        vendor_id: vendorId
      })
    });
  }

  async downloadForm(claimId) {
    const url = `${this.baseURL}/forms/${claimId}/download`;
    const response = await fetch(url, {
      headers: this.getHeaders()
    });
    
    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`);
    }
    
    return response.blob();
  }

  // Health check
  async healthCheck() {
    return this.makeRequest('/health');
  }

  // Utility methods
  async fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve({
          filename: file.name,
          content: base64,
          type: file.type,
          size: file.size
        });
      };
      reader.onerror = error => reject(error);
    });
  }

  // Session management
  resetSession() {
    this.sessionId = null;
  }

  logout() {
    this.authToken = null;
    this.sessionId = null;
    this.userId = null;
  }

  isAuthenticated() {
    return !!this.authToken;
  }
}

export default new ApiService();
