/**
 * Main App Component
 */
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AppProvider, useApp } from './contexts/AppContext';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import DocumentUpload from './components/DocumentUpload';
import ChatInterface from './components/ChatInterface';
import ClaimFormGenerator from './components/ClaimFormGenerator';
import LoginForm from './components/Auth/LoginForm';
import RegisterForm from './components/Auth/RegisterForm';

const MainApp: React.FC = () => {
  const { currentStep } = useApp();

  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'document_upload':
        return <DocumentUpload />;
      case 'chat':
        return <ChatInterface />;
      case 'claim_form':
        return <ClaimFormGenerator />;
      case 'submit':
        return <ClaimFormGenerator />;
      default:
        return <DocumentUpload />;
    }
  };

  return (
    <div className="min-h-screen bg-secondary-50">
      <Header />
      
      <div className="flex">
        <Sidebar />
        
        <main className="flex-1 p-6">
          {renderCurrentStep()}
        </main>
      </div>
    </div>
  );
};

const AppContent: React.FC = () => {
  const { token, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-secondary-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-secondary-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={!token ? <LoginForm /> : <Navigate to="/" replace />} 
        />
        <Route 
          path="/register" 
          element={!token ? <RegisterForm /> : <Navigate to="/" replace />} 
        />
        <Route 
          path="/" 
          element={token ? <MainApp /> : <Navigate to="/login" replace />} 
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </AuthProvider>
  );
};

export default App;