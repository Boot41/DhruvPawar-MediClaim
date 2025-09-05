/**
 * Claim Form Generator Component
 */
import React, { useState, useEffect } from 'react';
import { useApp } from '../contexts/AppContext';
import { claimAPI, vendorAPI } from '../services/api';
import { FileText, Download, CheckCircle, AlertCircle, Loader, Edit3 } from 'lucide-react';

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

  // Load vendors on component mount
  useEffect(() => {
    const loadVendors = async () => {
      try {
        const vendorList = await vendorAPI.getVendors();
        setVendors(vendorList);
      } catch (err) {
        console.error('Failed to load vendors:', err);
      }
    };
    loadVendors();
  }, []);

  const generateForm = async () => {
    if (!sessionId) {
      setError('No active session');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const preview = await claimAPI.generateForm(sessionId);
      setClaimFormPreview(preview);
      setFormData(preview.form_data);
    } catch (err: any) {
      console.error('Form generation error:', err);
      setError(err.response?.data?.detail || 'Failed to generate claim form');
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field: string, value: string) => {
    setFormData((prev: any) => ({
      ...prev,
      [field]: value
    }));
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
            onClick={generateForm}
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


        <div className="text-center py-12">
          <FileText className="w-12 h-12 text-primary-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">Ready to Generate</h3>
          <p className="text-secondary-600 mb-4">
            Make sure you have uploaded your policy and invoice documents.
          </p>
          <button
            onClick={generateForm}
            className="btn-primary"
          >
            Generate Claim Form
          </button>
        </div>
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
              href={`/api/claims/download-pdf/${claimFormPreview.pdf_filename}`}
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
          onClick={generateForm}
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
