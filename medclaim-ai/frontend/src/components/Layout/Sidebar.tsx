/**
 * Sidebar Component
 */
import React from 'react';
import { useApp } from '../../contexts/AppContext';
import { 
  Upload, 
  MessageCircle, 
  FileText, 
  CheckCircle
} from 'lucide-react';

const steps = [
  { id: 'document_upload', label: 'Upload Documents', icon: Upload },
  { id: 'chat', label: 'Ask Questions', icon: MessageCircle },
  { id: 'claim_form', label: 'File Claim', icon: FileText },
  { id: 'submit', label: 'Submit Claim', icon: CheckCircle },
];

const Sidebar: React.FC = () => {
  const { currentStep, setCurrentStep } = useApp();

  return (
    <aside className="w-64 bg-secondary-50 border-r border-secondary-200 min-h-screen">
      <div className="p-6">
        <h2 className="text-lg font-semibold text-secondary-900 mb-6">Process Steps</h2>
        
        <nav className="space-y-2">
          {steps.map((step, index) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = steps.findIndex(s => s.id === currentStep) > index;
            
            return (
              <button
                key={step.id}
                onClick={() => setCurrentStep(step.id)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left transition-colors ${
                  isActive
                    ? 'bg-primary-100 text-primary-700 border border-primary-200'
                    : isCompleted
                    ? 'bg-green-50 text-green-700 hover:bg-green-100'
                    : 'text-secondary-600 hover:bg-secondary-100'
                }`}
              >
                <div className="flex-shrink-0">
                  {isCompleted ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <Icon className={`w-5 h-5 ${isActive ? 'text-primary-600' : 'text-secondary-400'}`} />
                  )}
                </div>
                <div>
                  <div className="font-medium">{step.label}</div>
                  <div className="text-xs text-secondary-500">
                    Step {index + 1} of {steps.length}
                  </div>
                </div>
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
};

export default Sidebar;
