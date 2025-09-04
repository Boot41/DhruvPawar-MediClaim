import React from 'react';
import { clsx } from 'clsx';
import { Bot, User, CheckCircle, AlertCircle, Clock } from 'lucide-react';
import { motion } from 'framer-motion';

const ChatMessage = ({ message, isBot = false, timestamp, status = 'sent' }) => {
  const messageVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  const StatusIcon = () => {
    switch (status) {
      case 'sending':
        return <Clock className="h-3 w-3 text-gray-400" />;
      case 'sent':
        return <CheckCircle className="h-3 w-3 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <motion.div
      variants={messageVariants}
      initial="hidden"
      animate="visible"
      className={clsx(
        'flex gap-3 p-4',
        isBot ? 'bg-gray-50' : 'bg-white'
      )}
    >
      <div className="flex-shrink-0">
        <div className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center',
          isBot ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
        )}>
          {isBot ? <Bot className="h-4 w-4" /> : <User className="h-4 w-4" />}
        </div>
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm font-medium text-gray-900">
            {isBot ? 'MediClaim Assistant' : 'You'}
          </span>
          {timestamp && (
            <span className="text-xs text-gray-500">
              {new Date(timestamp).toLocaleTimeString()}
            </span>
          )}
          {!isBot && <StatusIcon />}
        </div>
        
        <div className="prose prose-sm max-w-none">
          {typeof message === 'string' ? (
            <div 
              className="text-gray-700 whitespace-pre-wrap"
              dangerouslySetInnerHTML={{ 
                __html: message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                              .replace(/\n/g, '<br/>') 
              }}
            />
          ) : (
            <div className="text-gray-700">{message}</div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default ChatMessage;
