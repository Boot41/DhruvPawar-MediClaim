/**
 * Main Application Context
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { Document, ChatResponse, CoverageAnalysis, ClaimFormPreview, WorkflowState } from '../services/api';
import { useAuth } from './AuthContext';

interface AppContextType {
  // Session
  sessionId: string | null;
  setSessionId: (id: string) => void;
  
  // Documents
  documents: Document[];
  setDocuments: (docs: Document[]) => void;
  addDocument: (doc: Document) => void;
  
  // Chat
  chatMessages: ChatResponse[];
  setChatMessages: (messages: ChatResponse[]) => void;
  addChatMessage: (message: ChatResponse) => void;
  
  // Coverage
  coverageAnalysis: CoverageAnalysis | null;
  setCoverageAnalysis: (analysis: CoverageAnalysis | null) => void;
  
  // Claims
  claimFormPreview: ClaimFormPreview | null;
  setClaimFormPreview: (preview: ClaimFormPreview | null) => void;
  
  // Workflow
  workflowState: WorkflowState | null;
  setWorkflowState: (state: WorkflowState | null) => void;
  
  // UI State
  currentStep: string;
  setCurrentStep: (step: string) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const { token } = useAuth();
  
  // Session
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // Documents
  const [documents, setDocuments] = useState<Document[]>([]);
  
  // Chat
  const [chatMessages, setChatMessages] = useState<ChatResponse[]>([]);
  
  // Coverage
  const [coverageAnalysis, setCoverageAnalysis] = useState<CoverageAnalysis | null>(null);
  
  // Claims
  const [claimFormPreview, setClaimFormPreview] = useState<ClaimFormPreview | null>(null);
  
  // Workflow
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  
  // UI State
  const [currentStep, setCurrentStep] = useState('document_upload');
  const [loading, setLoading] = useState(false);

  // Initialize session when user logs in
  useEffect(() => {
    if (token && !sessionId) {
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
    }
  }, [token, sessionId]);

  // Helper functions
  const addDocument = (doc: Document) => {
    setDocuments(prev => [...prev, doc]);
  };

  const addChatMessage = (message: ChatResponse) => {
    setChatMessages(prev => [...prev, message]);
  };

  const value = {
    sessionId,
    setSessionId,
    documents,
    setDocuments,
    addDocument,
    chatMessages,
    setChatMessages,
    addChatMessage,
    coverageAnalysis,
    setCoverageAnalysis,
    claimFormPreview,
    setClaimFormPreview,
    workflowState,
    setWorkflowState,
    currentStep,
    setCurrentStep,
    loading,
    setLoading,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};
