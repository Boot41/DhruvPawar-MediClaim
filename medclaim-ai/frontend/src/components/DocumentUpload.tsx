/**
 * Document Upload Component
 */
import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useApp } from '../contexts/AppContext';
import { documentAPI } from '../services/api';
import { Upload, FileText, AlertCircle, CheckCircle, Loader } from 'lucide-react';

const DocumentUpload: React.FC = () => {
  const { sessionId, addDocument, setLoading, loading } = useApp();
  const [uploading, setUploading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (!sessionId) {
      setError('No active session. Please refresh the page.');
      return;
    }

    for (const file of acceptedFiles) {
      setUploading(file.name);
      setError(null);

      try {
        // Determine file type based on filename or content
        let fileType = 'medical_record';
        if (file.name.toLowerCase().includes('policy')) {
          fileType = 'policy';
        } else if (file.name.toLowerCase().includes('invoice') || file.name.toLowerCase().includes('bill')) {
          fileType = 'invoice';
        }

        const response = await documentAPI.upload(file, fileType, sessionId);
        addDocument(response);
        
        // Show success message
        setSuccess(`${file.name} uploaded successfully! Document is being processed.`);
        setUploading(null);
        
        // Clear success message after 5 seconds
        setTimeout(() => setSuccess(null), 5000);
        
      } catch (err: any) {
        console.error('Upload error:', err);
        setError(err.response?.data?.detail || 'Upload failed. Please try again.');
        setUploading(null);
      }
    }
  }, [sessionId, addDocument]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
    },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-secondary-900 mb-2">Upload Documents</h2>
        <p className="text-secondary-600">
          Upload your insurance policy, medical invoices, and other relevant documents.
          Our AI will analyze and extract key information for claim processing.
        </p>
      </div>

      {/* Upload Area */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-400 bg-primary-50'
            : 'border-secondary-300 hover:border-primary-400 hover:bg-secondary-50'
        }`}
      >
        <input {...getInputProps()} />
        
        <div className="space-y-4">
          <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
            <Upload className="w-8 h-8 text-primary-600" />
          </div>
          
          <div>
            <p className="text-lg font-medium text-secondary-900">
              {isDragActive ? 'Drop files here' : 'Drag & drop files here'}
            </p>
            <p className="text-secondary-500">
              or click to select files
            </p>
          </div>
          
          <div className="text-sm text-secondary-400">
            <p>Supported formats: PDF, JPG, PNG</p>
            <p>Maximum file size: 10MB</p>
          </div>
        </div>
      </div>

      {/* Upload Status */}
      {uploading && (
        <div className="flex items-center space-x-3 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <Loader className="w-5 h-5 text-blue-600 animate-spin" />
          <span className="text-blue-700">Uploading {uploading}...</span>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="flex items-center space-x-3 p-4 bg-green-50 border border-green-200 rounded-lg">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className="text-green-700">{success}</span>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="flex items-center space-x-3 p-4 bg-red-50 border border-red-200 rounded-lg">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* Upload Tips */}
      <div className="bg-secondary-50 border border-secondary-200 rounded-lg p-4">
        <h3 className="font-medium text-secondary-900 mb-2">Upload Tips:</h3>
        <ul className="text-sm text-secondary-600 space-y-1">
          <li>• Upload clear, high-quality images or PDFs</li>
          <li>• Include policy documents for coverage information</li>
          <li>• Upload medical invoices and bills</li>
          <li>• Ensure all text is readable and not blurry</li>
        </ul>
      </div>
    </div>
  );
};

export default DocumentUpload;
