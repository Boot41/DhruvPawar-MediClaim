import React from 'react';
import { clsx } from 'clsx';
import { Check, Circle, FileText, Calculator, Building, ClipboardCheck, Download } from 'lucide-react';
import { motion } from 'framer-motion';

const ProgressSteps = ({ currentStep = 0, progress = 0 }) => {
  const steps = [
    {
      id: 'initial',
      title: 'Welcome',
      description: 'Getting started',
      icon: Circle
    },
    {
      id: 'policy_uploaded',
      title: 'Policy Document',
      description: 'Upload insurance policy',
      icon: FileText
    },
    {
      id: 'invoice_uploaded',
      title: 'Medical Bills',
      description: 'Upload medical invoices',
      icon: FileText
    },
    {
      id: 'coverage_calculated',
      title: 'Coverage Analysis',
      description: 'Calculate coverage',
      icon: Calculator
    },
    {
      id: 'vendor_selected',
      title: 'Insurance Provider',
      description: 'Select your provider',
      icon: Building
    },
    {
      id: 'form_processed',
      title: 'Form Processing',
      description: 'Process claim form',
      icon: ClipboardCheck
    },
    {
      id: 'completed',
      title: 'Completed',
      description: 'Download your form',
      icon: Download
    }
  ];

  const getStepStatus = (index) => {
    if (index < currentStep) return 'completed';
    if (index === currentStep) return 'current';
    return 'upcoming';
  };

  return (
    <div className="bg-white border-b border-gray-200 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => {
            const status = getStepStatus(index);
            const Icon = step.icon;
            
            return (
              <div key={step.id} className="flex items-center">
                <div className="flex flex-col items-center">
                  <motion.div
                    initial={{ scale: 0.8 }}
                    animate={{ scale: 1 }}
                    className={clsx(
                      'w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300',
                      status === 'completed' && 'bg-green-600 border-green-600 text-white',
                      status === 'current' && 'bg-blue-600 border-blue-600 text-white',
                      status === 'upcoming' && 'bg-gray-100 border-gray-300 text-gray-400'
                    )}
                  >
                    {status === 'completed' ? (
                      <Check className="h-5 w-5" />
                    ) : (
                      <Icon className="h-5 w-5" />
                    )}
                  </motion.div>
                  
                  <div className="mt-2 text-center">
                    <p className={clsx(
                      'text-xs font-medium',
                      status === 'completed' && 'text-green-600',
                      status === 'current' && 'text-blue-600',
                      status === 'upcoming' && 'text-gray-400'
                    )}>
                      {step.title}
                    </p>
                    <p className="text-xs text-gray-500 hidden sm:block">
                      {step.description}
                    </p>
                  </div>
                </div>
                
                {index < steps.length - 1 && (
                  <div className={clsx(
                    'flex-1 h-0.5 mx-4 transition-all duration-300',
                    index < currentStep ? 'bg-green-600' : 'bg-gray-300'
                  )} />
                )}
              </div>
            );
          })}
        </div>
        
        {progress > 0 && (
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Overall Progress</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5 }}
                className="bg-blue-600 h-2 rounded-full"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProgressSteps;
