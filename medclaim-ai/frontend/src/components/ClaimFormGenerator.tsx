/**
 * Claim Form Generator Component
 */
import React, { useState, useEffect } from 'react';
import { useApp } from '../contexts/AppContext';
import { claimAPI, vendorAPI, documentAPI } from '../services/api';
import { FileText, Download, CheckCircle, AlertCircle, Loader, Edit3 } from 'lucide-react';
import PDFViewer from './PDFViewer';

const ClaimFormGenerator: React.FC = () => {
  const { sessionId, claimFormPreview, setClaimFormPreview } = useApp();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState<any>(null);
  const [vendors, setVendors] = useState<any[]>([]);
  const [selectedVendor, setSelectedVendor] = useState<string | null>(null);
  const [formType, setFormType] = useState<'synthetic' | 'vendor'>('synthetic');
  const [showVendorSelection, setShowVendorSelection] = useState(false);
  const [recentDocuments, setRecentDocuments] = useState<any[]>([]);
  const [selectedDocuments, setSelectedDocuments] = useState<string[]>([]);
  const [loadingDocuments, setLoadingDocuments] = useState(false);

  // Load vendors and recent documents on component mount
  useEffect(() => {
    const loadData = async () => {
      try {
        // Load vendors
        const vendorList = await vendorAPI.getVendors();
        setVendors(vendorList);
        
        // Load recent documents
        const docsSummary = await documentAPI.getDocumentsSummary();
        if (docsSummary.recent_documents) {
          setRecentDocuments(docsSummary.recent_documents);
          // Auto-select all documents by default
          setSelectedDocuments(docsSummary.recent_documents.map((doc: any) => doc.id));
        }
      } catch (err) {
        console.error('Failed to load data:', err);
      }
    };
    loadData();
  }, []);

  const generateSyntheticForm = async () => {
    if (!sessionId) {
      setError('No active session');
      return;
    }

    if (selectedDocuments.length === 0) {
      setError('Please select at least one document to generate the form');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await claimAPI.generateSyntheticForm(sessionId, selectedDocuments);
      setClaimFormPreview(result);
      setFormData(result.form_data);
    } catch (err: any) {
      console.error('Synthetic form generation error:', err);
      setError(err.response?.data?.detail || 'Failed to generate synthetic form');
    } finally {
      setLoading(false);
    }
  };

  const generateVendorForm = async (vendorId: string) => {
    if (!sessionId) {
      setError('No active session');
      return;
    }

    if (selectedDocuments.length === 0) {
      setError('Please select at least one document to generate the form');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await claimAPI.generateVendorForm(sessionId, vendorId, selectedDocuments);
      setClaimFormPreview(result);
      setFormData(result.form_data);
    } catch (err: any) {
      console.error('Vendor form generation error:', err);
      setError(err.response?.data?.detail || 'Failed to generate vendor form');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentToggle = (documentId: string) => {
    setSelectedDocuments(prev => 
      prev.includes(documentId) 
        ? prev.filter(id => id !== documentId)
        : [...prev, documentId]
    );
  };

  const selectAllDocuments = () => {
    setSelectedDocuments(recentDocuments.map(doc => doc.id));
  };

  const deselectAllDocuments = () => {
    setSelectedDocuments([]);
  };

  const handleFieldChange = (field: string, value: string) => {
    setFormData((prev: any) => ({
      ...prev,
      [field]: value
    }));
    
    // Update the claim form preview with new data
    if (claimFormPreview) {
      setClaimFormPreview({
        ...claimFormPreview,
        form_data: {
          ...claimFormPreview.form_data,
          [field]: value
        }
      });
    }
  };

  const regeneratePDF = async () => {
    if (!sessionId) {
      setError('No session available');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Use the update form API to regenerate with current form data
      const result = await claimAPI.updateForm(sessionId, selectedDocuments, formData);
      
      setClaimFormPreview(result);
      setFormData(result.form_data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to regenerate PDF');
    } finally {
      setLoading(false);
    }
  };

  const submitClaim = async () => {
    if (!claimFormPreview) return;

    try {
      await claimAPI.submit(claimFormPreview.form_data.claim_id || 'temp', formData);
      alert('Claim submitted successfully!');
    } catch (err: any) {
      console.error('Claim submission error:', err);
      alert('Failed to submit claim. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <Loader className="w-8 h-8 animate-spin mx-auto text-primary-600 mb-4" />
          <p className="text-secondary-600">Generating your claim form...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">Generation Error</h3>
          <p className="text-secondary-600 mb-4">{error}</p>
          <button
            onClick={generateSyntheticForm}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!claimFormPreview) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-secondary-900 mb-2">File Your Claim</h2>
          <p className="text-secondary-600">
            Choose how you'd like to file your claim - either with a popular vendor form or a synthetic form.
          </p>
        </div>

        {/* Document Selection */}
        {recentDocuments.length > 0 && (
          <div className="card mb-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-secondary-900">Select Documents to Include</h3>
              <div className="flex space-x-2">
                <button
                  onClick={selectAllDocuments}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  Select All
                </button>
                <span className="text-secondary-400">|</span>
                <button
                  onClick={deselectAllDocuments}
                  className="text-sm text-secondary-600 hover:text-secondary-700"
                >
                  Deselect All
                </button>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${
                    selectedDocuments.includes(doc.id)
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-secondary-200 hover:border-primary-300'
                  }`}
                  onClick={() => handleDocumentToggle(doc.id)}
                >
                  <div className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      checked={selectedDocuments.includes(doc.id)}
                      onChange={() => handleDocumentToggle(doc.id)}
                      className="mt-1 h-4 w-4 text-primary-600 focus:ring-primary-500 border-secondary-300 rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <FileText className="w-4 h-4 text-primary-600" />
                        <p className="text-sm font-medium text-secondary-900 truncate">
                          {doc.original_filename || doc.filename}
                        </p>
                      </div>
                      <p className="text-xs text-secondary-600 capitalize mt-1">
                        {doc.file_type.replace('_', ' ')}
                      </p>
                      <p className="text-xs text-secondary-500 mt-1">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="mt-4 text-sm text-secondary-600">
              {selectedDocuments.length} of {recentDocuments.length} documents selected
            </div>
          </div>
        )}

        {/* Form Type Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Synthetic Form Option */}
          <div 
            className={`border-2 rounded-lg p-6 cursor-pointer transition-all ${
              formType === 'synthetic' 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-secondary-200 hover:border-primary-300'
            }`}
            onClick={() => setFormType('synthetic')}
          >
            <div className="text-center">
              <FileText className="w-12 h-12 text-primary-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-secondary-900 mb-2">Synthetic Form</h3>
              <p className="text-secondary-600 mb-4">
                Generate a custom claim form based on your documents
              </p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  generateSyntheticForm();
                }}
                className="btn-primary w-full"
                disabled={loading}
              >
                {loading ? 'Generating...' : 'Generate Synthetic Form'}
              </button>
            </div>
          </div>

          {/* Vendor Form Option */}
          <div 
            className={`border-2 rounded-lg p-6 cursor-pointer transition-all ${
              formType === 'vendor' 
                ? 'border-primary-500 bg-primary-50' 
                : 'border-secondary-200 hover:border-primary-300'
            }`}
            onClick={() => setFormType('vendor')}
          >
            <div className="text-center">
              <FileText className="w-12 h-12 text-primary-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-secondary-900 mb-2">Vendor Form</h3>
              <p className="text-secondary-600 mb-4">
                Use a predefined form from popular insurance vendors
              </p>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setShowVendorSelection(true);
                }}
                className="btn-primary w-full"
                disabled={loading}
              >
                {loading ? 'Loading...' : 'Select Vendor Form'}
              </button>
            </div>
          </div>
        </div>

        {/* Vendor Selection Modal */}
        {showVendorSelection && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-secondary-900 mb-4">Select Vendor</h3>
              <div className="space-y-2">
                {vendors.map((vendor) => (
                  <button
                    key={vendor.id}
                    onClick={() => {
                      setSelectedVendor(vendor.id);
                      setShowVendorSelection(false);
                      generateVendorForm(vendor.id);
                    }}
                    className="w-full text-left p-3 border border-secondary-200 rounded-lg hover:bg-secondary-50"
                  >
                    <div className="font-medium text-secondary-900">{vendor.display_name}</div>
                    <div className="text-sm text-secondary-600">{vendor.name}</div>
                  </button>
                ))}
              </div>
              <button
                onClick={() => setShowVendorSelection(false)}
                className="mt-4 w-full btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-secondary-900 mb-2">Claim Form Preview</h2>
          <p className="text-secondary-600">
            Review and edit the information before submitting your claim.
          </p>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setEditing(!editing)}
            className="btn-secondary"
          >
            <Edit3 className="w-4 h-4 mr-2" />
            {editing ? 'View Only' : 'Edit'}
          </button>
          
          <button
            onClick={() => window.print()}
            className="btn-secondary"
          >
            <Download className="w-4 h-4 mr-2" />
            Print
          </button>
          
          {claimFormPreview.pdf_filename && (
            <a
              href={`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/claims/download-pdf/${claimFormPreview.pdf_filename}`}
              download
              className="btn-primary"
            >
              <Download className="w-4 h-4 mr-2" />
              Download PDF
            </a>
          )}
        </div>
      </div>

      {/* Missing Fields Alert */}
      {claimFormPreview.missing_fields && claimFormPreview.missing_fields.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div>
              <h3 className="font-medium text-yellow-800">Missing Information</h3>
              <p className="text-yellow-700 text-sm mt-1">
                The following fields need to be filled out:
              </p>
              <ul className="text-yellow-700 text-sm mt-2 list-disc list-inside">
                {claimFormPreview.missing_fields.map((field: string, index: number) => (
                  <li key={index}>{field}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Missing Fields Input Form */}
      {claimFormPreview.missing_fields && claimFormPreview.missing_fields.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-secondary-900">Fill Missing Information</h3>
            <button
              onClick={regeneratePDF}
              disabled={loading}
              className="btn-primary text-sm"
            >
              {loading ? (
                <>
                  <Loader className="w-4 h-4 mr-2 animate-spin" />
                  Updating PDF...
                </>
              ) : (
                <>
                  <Edit3 className="w-4 h-4 mr-2" />
                  Update PDF
                </>
              )}
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {claimFormPreview.missing_fields.map((field: string, index: number) => {
              const fieldKey = field.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '');
              const fieldValue = formData?.[fieldKey] || '';
              
              return (
                <div key={index}>
                  <label className="block text-sm font-medium text-secondary-700 mb-1">
                    {field}
                  </label>
                  {fieldKey.includes('date') ? (
                    <input
                      type="date"
                      value={fieldValue}
                      onChange={(e) => handleFieldChange(fieldKey, e.target.value)}
                      className="input-field"
                      placeholder={`Enter ${field.toLowerCase()}`}
                    />
                  ) : fieldKey.includes('amount') || fieldKey.includes('number') ? (
                    <input
                      type="number"
                      value={fieldValue}
                      onChange={(e) => handleFieldChange(fieldKey, e.target.value)}
                      className="input-field"
                      placeholder={`Enter ${field.toLowerCase()}`}
                    />
                  ) : fieldKey.includes('email') ? (
                    <input
                      type="email"
                      value={fieldValue}
                      onChange={(e) => handleFieldChange(fieldKey, e.target.value)}
                      className="input-field"
                      placeholder={`Enter ${field.toLowerCase()}`}
                    />
                  ) : fieldKey.includes('phone') || fieldKey.includes('contact') ? (
                    <input
                      type="tel"
                      value={fieldValue}
                      onChange={(e) => handleFieldChange(fieldKey, e.target.value)}
                      className="input-field"
                      placeholder={`Enter ${field.toLowerCase()}`}
                    />
                  ) : (
                    <input
                      type="text"
                      value={fieldValue}
                      onChange={(e) => handleFieldChange(fieldKey, e.target.value)}
                      className="input-field"
                      placeholder={`Enter ${field.toLowerCase()}`}
                    />
                  )}
                </div>
              );
            })}
          </div>
          
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-blue-800 text-sm">
              <CheckCircle className="w-4 h-4 inline mr-2" />
              Fill in the missing information above and click "Update PDF" to regenerate the form with your data.
            </p>
          </div>
        </div>
      )}

      {/* PDF Preview */}
      {claimFormPreview.pdf_filename && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-secondary-900">PDF Preview</h3>
            <div className="flex space-x-2">
              <a
                href={`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/claims/download-pdf/${claimFormPreview.pdf_filename}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary text-sm"
              >
                <Download className="w-4 h-4 mr-2" />
                Open in New Tab
              </a>
            </div>
          </div>
          <PDFViewer
            pdfUrl={`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/claims/download-pdf/${claimFormPreview.pdf_filename}`}
            filename={claimFormPreview.pdf_filename}
          />
        </div>
      )}

      {/* Form Preview */}
      <div className="card">
        <h3 className="text-lg font-semibold text-secondary-900 mb-6">Insurance Claim Form</h3>
        
        <div className="space-y-6">
          {/* Patient Information */}
          <div>
            <h4 className="font-medium text-secondary-900 mb-4 border-b border-secondary-200 pb-2">
              Patient Information
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Patient Name
                </label>
                {editing ? (
                  <input
                    type="text"
                    value={formData?.patient_name || ''}
                    onChange={(e) => handleFieldChange('patient_name', e.target.value)}
                    className="input-field"
                  />
                ) : (
                  <p className="text-secondary-900 py-2">{formData?.patient_name || 'N/A'}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Policy Number
                </label>
                {editing ? (
                  <input
                    type="text"
                    value={formData?.policy_number || ''}
                    onChange={(e) => handleFieldChange('policy_number', e.target.value)}
                    className="input-field"
                  />
                ) : (
                  <p className="text-secondary-900 py-2">{formData?.policy_number || 'N/A'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Insurance Information */}
          <div>
            <h4 className="font-medium text-secondary-900 mb-4 border-b border-secondary-200 pb-2">
              Insurance Information
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Insurance Company
                </label>
                {editing ? (
                  <input
                    type="text"
                    value={formData?.insurer_name || ''}
                    onChange={(e) => handleFieldChange('insurer_name', e.target.value)}
                    className="input-field"
                  />
                ) : (
                  <p className="text-secondary-900 py-2">{formData?.insurer_name || 'N/A'}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Coverage Amount
                </label>
                {editing ? (
                  <input
                    type="text"
                    value={formData?.coverage_amount || ''}
                    onChange={(e) => handleFieldChange('coverage_amount', e.target.value)}
                    className="input-field"
                  />
                ) : (
                  <p className="text-secondary-900 py-2">₹{formData?.coverage_amount || 'N/A'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Medical Information */}
          <div>
            <h4 className="font-medium text-secondary-900 mb-4 border-b border-secondary-200 pb-2">
              Medical Information
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Hospital/Facility
                </label>
                {editing ? (
                  <input
                    type="text"
                    value={formData?.hospital_name || ''}
                    onChange={(e) => handleFieldChange('hospital_name', e.target.value)}
                    className="input-field"
                  />
                ) : (
                  <p className="text-secondary-900 py-2">{formData?.hospital_name || 'N/A'}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Service Date
                </label>
                {editing ? (
                  <input
                    type="date"
                    value={formData?.service_date || ''}
                    onChange={(e) => handleFieldChange('service_date', e.target.value)}
                    className="input-field"
                  />
                ) : (
                  <p className="text-secondary-900 py-2">{formData?.service_date || 'N/A'}</p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-1">
                  Total Amount
                </label>
                {editing ? (
                  <input
                    type="number"
                    value={formData?.total_amount || ''}
                    onChange={(e) => handleFieldChange('total_amount', e.target.value)}
                    className="input-field"
                  />
                ) : (
                  <p className="text-secondary-900 py-2">₹{formData?.total_amount || 'N/A'}</p>
                )}
              </div>
            </div>
          </div>

          {/* Procedures */}
          {formData?.procedures && formData.procedures.length > 0 && (
            <div>
              <h4 className="font-medium text-secondary-900 mb-4 border-b border-secondary-200 pb-2">
                Procedures/Treatments
              </h4>
              <div className="space-y-2">
                {formData.procedures.map((procedure: string, index: number) => (
                  <div key={index} className="flex items-center space-x-2">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-secondary-900">{procedure}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <button
          onClick={generateSyntheticForm}
          className="btn-secondary"
        >
          Regenerate Form
        </button>
        
        <button
          onClick={submitClaim}
          className="btn-primary"
        >
          <CheckCircle className="w-4 h-4 mr-2" />
          Submit Claim
        </button>
      </div>
    </div>
  );
};

export default ClaimFormGenerator;
