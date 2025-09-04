/**
 * Coverage Analysis Component
 */
import React, { useState, useEffect } from 'react';
import { useApp } from '../contexts/AppContext';
import { coverageAPI } from '../services/api';
import { Calculator, TrendingUp, DollarSign, AlertCircle, CheckCircle, Loader } from 'lucide-react';

const CoverageAnalysis: React.FC = () => {
  const { sessionId, coverageAnalysis, setCoverageAnalysis, documents } = useApp();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculateCoverage = async () => {
    if (!sessionId) {
      setError('No active session');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const analysis = await coverageAPI.calculate(sessionId);
      setCoverageAnalysis(analysis);
    } catch (err: any) {
      console.error('Coverage calculation error:', err);
      setError(err.response?.data?.detail || 'Failed to calculate coverage');
    } finally {
      setLoading(false);
    }
  };

  // Auto-calculate if we have both policy and invoice documents
  useEffect(() => {
    const hasPolicy = documents.some(doc => doc.file_type === 'policy');
    const hasInvoice = documents.some(doc => doc.file_type === 'invoice');
    
    if (hasPolicy && hasInvoice && !coverageAnalysis) {
      calculateCoverage();
    }
  }, [documents]);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <Loader className="w-8 h-8 animate-spin mx-auto text-primary-600 mb-4" />
          <p className="text-secondary-600">Calculating your coverage...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">Calculation Error</h3>
          <p className="text-secondary-600 mb-4">{error}</p>
          <button
            onClick={calculateCoverage}
            className="btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!coverageAnalysis) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-secondary-900 mb-2">Coverage Analysis</h2>
          <p className="text-secondary-600">
            Calculate how much your insurance will cover for your medical expenses.
          </p>
        </div>

        <div className="text-center py-12">
          <Calculator className="w-12 h-12 text-primary-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-secondary-900 mb-2">Ready to Calculate</h3>
          <p className="text-secondary-600 mb-4">
            Make sure you have uploaded both your policy and invoice documents.
          </p>
          <button
            onClick={calculateCoverage}
            className="btn-primary"
          >
            Calculate Coverage
          </button>
        </div>
      </div>
    );
  }

  const {
    total_cost,
    deductible_applied,
    insurance_covers,
    out_of_pocket,
    coverage_percentage
  } = coverageAnalysis;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-secondary-900 mb-2">Coverage Analysis</h2>
        <p className="text-secondary-600">
          Based on your policy and invoice documents, here's what your insurance will cover:
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <DollarSign className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-secondary-600">Total Cost</p>
              <p className="text-2xl font-bold text-secondary-900">₹{total_cost.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <AlertCircle className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-secondary-600">Deductible</p>
              <p className="text-2xl font-bold text-secondary-900">₹{deductible_applied.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-secondary-600">Insurance Covers</p>
              <p className="text-2xl font-bold text-green-600">₹{insurance_covers.toLocaleString()}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-lg">
              <TrendingUp className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-secondary-600">Out of Pocket</p>
              <p className="text-2xl font-bold text-red-600">₹{out_of_pocket.toLocaleString()}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Coverage Percentage */}
      <div className="card">
        <h3 className="text-lg font-semibold text-secondary-900 mb-4">Coverage Breakdown</h3>
        
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm font-medium text-secondary-600 mb-2">
              <span>Coverage Percentage</span>
              <span>{coverage_percentage.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-secondary-200 rounded-full h-3">
              <div
                className="bg-primary-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(coverage_percentage, 100)}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t border-secondary-200">
            <div>
              <h4 className="font-medium text-secondary-900 mb-2">What's Covered</h4>
              <ul className="text-sm text-secondary-600 space-y-1">
                <li>• Medical procedures and treatments</li>
                <li>• Hospital room and board</li>
                <li>• Prescription medications</li>
                <li>• Diagnostic tests and lab work</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium text-secondary-900 mb-2">Your Responsibility</h4>
              <ul className="text-sm text-secondary-600 space-y-1">
                <li>• Deductible: ₹{deductible_applied.toLocaleString()}</li>
                <li>• Co-pay: ₹{(out_of_pocket - deductible_applied).toLocaleString()}</li>
                <li>• Total out-of-pocket: ₹{out_of_pocket.toLocaleString()}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-between">
        <button
          onClick={calculateCoverage}
          className="btn-secondary"
        >
          Recalculate
        </button>
        
        <button
          onClick={() => window.print()}
          className="btn-primary"
        >
          Print Report
        </button>
      </div>
    </div>
  );
};

export default CoverageAnalysis;
