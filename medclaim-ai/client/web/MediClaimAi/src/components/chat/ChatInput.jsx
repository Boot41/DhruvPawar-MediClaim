import React, { useState, useRef } from 'react';
import { Send, Paperclip } from 'lucide-react';
import Button from '../ui/Button';
import FileUpload from '../ui/FileUpload';

const ChatInput = ({ 
  onSendMessage, 
  onFileUpload, 
  disabled = false, 
  placeholder = "Type your message...",
  showFileUpload = false 
}) => {
  const [message, setMessage] = useState('');
  const [showUpload, setShowUpload] = useState(false);
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (message.trim() && !disabled) {
      onSendMessage(message.trim());
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  };

  const handleFileSelect = (file) => {
    if (file && onFileUpload) {
      onFileUpload(file);
      setShowUpload(false);
    }
  };

  return (
    <div className="border-t border-gray-200 bg-white p-4">
      {showUpload && (
        <div className="mb-4">
          <FileUpload
            onFileSelect={handleFileSelect}
            label="Upload Document"
            description="Upload your policy document or medical bill (PDF, JPG, PNG)"
            accept=".pdf,.jpg,.jpeg,.png"
            maxSize={10 * 1024 * 1024} // 10MB
          />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowUpload(false)}
            className="mt-2"
          >
            Cancel
          </Button>
        </div>
      )}
      
      <form onSubmit={handleSubmit} className="flex gap-2 items-end">
        <div className="flex-1">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleTextareaChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder}
            disabled={disabled}
            rows={1}
            className="w-full resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed max-h-32"
            style={{ minHeight: '40px' }}
          />
        </div>
        
        {showFileUpload && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => setShowUpload(!showUpload)}
            className="h-10 w-10 p-0"
            disabled={disabled}
          >
            <Paperclip className="h-4 w-4" />
          </Button>
        )}
        
        <Button
          type="submit"
          disabled={disabled || !message.trim()}
          className="h-10 w-10 p-0"
        >
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
};

export default ChatInput;
