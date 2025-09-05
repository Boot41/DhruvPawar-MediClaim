/**
 * API Service for communicating with the backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Types
export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface Document {
  id: string;
  filename: string;
  original_filename: string;
  file_type: string;
  upload_status: string;
  extracted_data?: any;
  total_chunks?: number;
  created_at: string;
}

export interface ChatMessage {
  message: string;
  session_id: string;
}

export interface ChatResponse {
  response: string;
  agent_name: string;
  metadata?: any;
  timestamp: string;
}

export interface CoverageAnalysis {
  total_cost: number;
  deductible_applied: number;
  insurance_covers: number;
  out_of_pocket: number;
  coverage_percentage: number;
}

export interface ClaimFormPreview {
  form_data: any;
  preview_html: string;
  missing_fields: string[];
  pdf_path?: string;
  pdf_filename?: string;
}

export interface Vendor {
  id: string;
  name: string;
  display_name: string;
  form_template_url?: string;
  is_active: boolean;
}

export interface WorkflowState {
  current_step: string;
  step_data?: any;
  conversation_history?: any[];
}

// Auth API
export const authAPI = {
  register: async (email: string, password: string, fullName?: string) => {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', {
      email,
      password,
    });
    return response.data;
  },

  createSession: async () => {
    const response = await api.post('/auth/session');
    return response.data;
  },
};

// Document API
export const documentAPI = {
  upload: async (file: File, fileType: string, sessionId: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);
    formData.append('session_id', sessionId);

    const response = await api.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  getDocuments: async () => {
    const response = await api.get('/api/documents');
    return response.data;
  },

  getDocumentsSummary: async () => {
    const response = await api.get('/api/documents/summary');
    return response.data;
  },
};

// Chat API
export const chatAPI = {
  sendMessage: async (message: string, sessionId: string) => {
    const response = await api.post('/api/chat', {
      message,
      session_id: sessionId,
    });
    return response.data;
  },

  getHistory: async (sessionId: string) => {
    const response = await api.get(`/api/chat/history/${sessionId}`);
    return response.data;
  },
};


// Claim API
export const claimAPI = {
  generateForm: async (sessionId: string) => {
    const response = await api.post('/api/claims/generate-form', {
      session_id: sessionId,
    });
    return response.data;
  },

  submit: async (claimId: string, approvedData: any) => {
    const response = await api.post('/api/claims/submit', {
      claim_id: claimId,
      approved_data: approvedData,
    });
    return response.data;
  },
};

// Vendor API
export const vendorAPI = {
  getVendors: async () => {
    const response = await api.get('/api/vendors');
    return response.data;
  },
};

// Workflow API
export const workflowAPI = {
  getState: async (sessionId: string) => {
    const response = await api.get(`/api/workflow/${sessionId}`);
    return response.data;
  },

  updateState: async (sessionId: string, workflowData: WorkflowState) => {
    const response = await api.post(`/api/workflow/${sessionId}/update`, workflowData);
    return response.data;
  },
};

export default api;
