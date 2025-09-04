import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../../contexts/AuthContext';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ProgressSteps from './ProgressSteps';
import CoverageAnalysis from './CoverageAnalysis';
import VendorSelection from './VendorSelection';
import UserMenu from '../ui/UserMenu';
import { Card } from '../ui/Card';
import { Alert } from '../ui';
import apiService from '../../services/api';

const ChatContainer = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);
  const [sessionData, setSessionData] = useState({});
  const [showCoverageAnalysis, setShowCoverageAnalysis] = useState(false);
  const [showVendorSelection, setShowVendorSelection] = useState(false);
  const messagesEndRef = useRef(null);

  const stepMapping = {
    'initial': 0,
    'policy_uploaded': 1,
    'invoice_uploaded': 2,
    'coverage_calculated': 3,
    'vendor_selected': 4,
    'form_processed': 5,
    'completed': 6
  };

  useEffect(() => {
    initializeChat();
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const initializeChat = async () => {
    try {
      setLoading(true);
      const response = await apiService.startSession();
      
      if (response.message) {
        setMessages([{
          id: Date.now(),
          content: response.message,
          isBot: true,
          timestamp: new Date().toISOString()
        }]);
      }
      
      updateSessionState(response);
    } catch (err) {
      setError('Failed to initialize chat. Please refresh the page.');
      console.error('Chat initialization error:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateSessionState = (response) => {
    if (response.state) {
      setCurrentStep(stepMapping[response.state] || 0);
    }
    if (response.progress) {
      setProgress(response.progress);
    }
    if (response.coverage_analysis) {
      setSessionData(prev => ({ ...prev, coverage_analysis: response.coverage_analysis }));
      setShowCoverageAnalysis(true);
    }
    if (response.vendors) {
      setSessionData(prev => ({ ...prev, vendors: response.vendors }));
      setShowVendorSelection(true);
    }
    if (response.selected_vendor) {
      setSessionData(prev => ({ ...prev, selected_vendor: response.selected_vendor }));
      setShowVendorSelection(false);
    }
  };

  const handleSendMessage = async (message) => {
    const userMessage = {
      id: Date.now(),
      content: message,
      isBot: false,
      timestamp: new Date().toISOString(),
      status: 'sending'
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      const response = await apiService.sendMessage(message);
      
      // Update user message status
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, status: 'sent' }
          : msg
      ));

      // Add bot response - extract actual response content
      let botContent = response.message;
      if (response.data && response.data.response) {
        botContent = response.data.response;
      } else if (response.success && response.message === "Message processed" && response.data) {
        botContent = response.data.response || "I've processed your message. How else can I help you?";
      }
      
      if (botContent) {
        const botMessage = {
          id: Date.now() + 1,
          content: botContent,
          isBot: true,
          timestamp: new Date().toISOString()
        };
        setMessages(prev => [...prev, botMessage]);
      }

      updateSessionState(response);

    } catch (err) {
      setError('Failed to send message. Please try again.');
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, status: 'error' }
          : msg
      ));
      console.error('Send message error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file) => {
    try {
      setLoading(true);
      setError(null);
      
      // Determine file type based on current step or filename
      let fileType = 'policy'; // default
      if (currentStep === 0) {
        fileType = 'policy';
      } else if (currentStep === 1) {
        fileType = 'invoice';
      } else {
        // Infer from filename if step is ambiguous
        const fileName = file.name.toLowerCase();
        if (fileName.includes('policy') || fileName.includes('insurance')) {
          fileType = 'policy';
        } else if (fileName.includes('bill') || fileName.includes('invoice') || fileName.includes('receipt')) {
          fileType = 'invoice';
        }
      }
      
      // Add user message showing file upload
      const userMessage = {
        id: Date.now(),
        content: `📎 Uploading ${file.name} (${fileType} document)...`,
        isBot: false,
        timestamp: new Date().toISOString(),
        status: 'uploading'
      };
      setMessages(prev => [...prev, userMessage]);
      
      // Use the correct upload endpoint instead of chat
      const response = await apiService.uploadDocument(file, fileType);
      
      // Update user message status
      setMessages(prev => prev.map(msg => 
        msg.id === userMessage.id 
          ? { ...msg, status: 'uploaded', content: `✅ Uploaded ${file.name}` }
          : msg
      ));
      
      // Add bot response
      if (response.success) {
        let botContent = response.message || 'File uploaded successfully!';
        
        // Use agent response if available (contains extracted data summary)
        if (response.agent_response) {
          botContent = response.agent_response;
        }
        
        const botMessage = {
          id: Date.now() + 1,
          content: botContent,
          isBot: true,
          timestamp: new Date().toISOString()
        };
        
        setMessages(prev => [...prev, botMessage]);
        
        // Update session state based on file type
        const newStep = fileType === 'policy' ? 'policy_uploaded' : 'invoice_uploaded';
        updateSessionState({
          state: newStep,
          progress: fileType === 'policy' ? 25 : 50
        });
      } else {
        throw new Error(response.message || 'Upload failed');
      }
      
    } catch (err) {
      // Update user message to show error
      setMessages(prev => prev.map(msg => 
        msg.id && msg.status === 'uploading'
          ? { ...msg, status: 'error', content: `❌ Failed to upload ${file.name}` }
          : msg
      ));
      
      setError('Failed to upload file. Please try again.');
      console.error('File upload error:', err);
      
      // Add error message from bot
      const errorMessage = {
        id: Date.now() + 2,
        content: `I'm sorry, but I encountered an error while uploading your ${file.name}. Please make sure it's a valid PDF, JPG, or PNG file and try again.`,
        isBot: true,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleVendorSelect = async (vendor) => {
    setSessionData(prev => ({ ...prev, selected_vendor: vendor }));
    await handleSendMessage(vendor);
  };

  const handleDemoMode = () => {
    handleSendMessage('demo');
  };

  const handleRestart = () => {
    apiService.resetSession();
    setMessages([]);
    setCurrentStep(0);
    setProgress(0);
    setSessionData({});
    setShowCoverageAnalysis(false);
    setShowVendorSelection(false);
    initializeChat();
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">MediClaim AI Assistant</h1>
            <p className="text-sm text-gray-600">Your intelligent insurance claim processor</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex gap-2">
              <button
                onClick={handleDemoMode}
                className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
              >
                Demo Mode
              </button>
              <button
                onClick={handleRestart}
                className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
              >
                Restart
              </button>
            </div>
            <UserMenu />
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <ProgressSteps currentStep={currentStep} progress={progress} />

      {/* Error Alert */}
      {error && (
        <div className="p-4">
          <Alert variant="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </div>
      )}

      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto">
          <AnimatePresence>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
              >
                <ChatMessage
                  message={message.content}
                  isBot={message.isBot}
                  timestamp={message.timestamp}
                  status={message.status}
                />
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Coverage Analysis */}
          {showCoverageAnalysis && sessionData.coverage_analysis && (
            <div className="p-4">
              <CoverageAnalysis analysisData={sessionData.coverage_analysis} />
            </div>
          )}

          {/* Vendor Selection */}
          {showVendorSelection && (
            <div className="p-4">
              <VendorSelection
                vendors={sessionData.vendors}
                selectedVendor={sessionData.selected_vendor}
                onVendorSelect={handleVendorSelect}
              />
            </div>
          )}

          {loading && (
            <div className="p-4">
              <div className="flex items-center space-x-2 text-gray-500">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-sm">Processing...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Chat Input */}
      <div className="max-w-4xl mx-auto w-full">
        <ChatInput
          onSendMessage={handleSendMessage}
          onFileUpload={handleFileUpload}
          disabled={loading}
          showFileUpload={currentStep <= 2}
          placeholder={
            currentStep === 0 ? "Type 'demo' to see how it works, or describe your insurance policy..." :
            currentStep === 1 ? "Describe your medical bills or upload documents..." :
            "Type your message..."
          }
        />
      </div>
    </div>
  );
};

export default ChatContainer;
