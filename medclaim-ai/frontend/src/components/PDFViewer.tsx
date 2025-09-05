/**
 * PDF Viewer Component
 */
import React, { useState, useEffect } from 'react';
import { Download, ExternalLink, AlertCircle } from 'lucide-react';

interface PDFViewerProps {
  pdfUrl: string;
  filename: string;
  className?: string;
}

const PDFViewer: React.FC<PDFViewerProps> = ({ pdfUrl, filename, className = '' }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [pdfDataUrl, setPdfDataUrl] = useState<string | null>(null);

  useEffect(() => {
    const fetchPDF = async () => {
      try {
        setIsLoading(true);
        setHasError(false);
        
        // Get auth token
        const token = localStorage.getItem('access_token');
        if (!token) {
          throw new Error('No authentication token found');
        }
        
        // Fetch PDF with authentication
        const response = await fetch(pdfUrl, {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch PDF: ${response.status}`);
        }
        
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setPdfDataUrl(url);
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching PDF:', error);
        setHasError(true);
        setIsLoading(false);
      }
    };
    
    fetchPDF();
    
    // Cleanup blob URL on unmount
    return () => {
      if (pdfDataUrl) {
        URL.revokeObjectURL(pdfDataUrl);
      }
    };
  }, [pdfUrl, pdfDataUrl]);

  if (isLoading) {
    return (
      <div className={`flex items-center justify-center h-96 bg-gray-50 ${className}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-secondary-600">Loading PDF...</p>
        </div>
      </div>
    );
  }

  if (hasError) {
    return (
      <div className={`flex items-center justify-center h-96 bg-gray-50 ${className}`}>
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-secondary-900 mb-2">Unable to Load PDF</h4>
          <p className="text-secondary-600 mb-4">
            There was an error loading the PDF preview.
          </p>
          <div className="flex space-x-2 justify-center">
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-primary"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Open PDF
            </a>
            <a
              href={pdfUrl}
              download={filename}
              className="btn-secondary"
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`border border-secondary-200 rounded-lg overflow-hidden ${className}`}>
      <iframe
        src={pdfDataUrl || pdfUrl}
        width="100%"
        height="600"
        className="border-0"
        title={`PDF Preview - ${filename}`}
        onLoad={() => {
          console.log('PDF iframe loaded successfully');
          setIsLoading(false);
        }}
        onError={(e) => {
          console.error('PDF iframe failed to load:', e);
          setHasError(true);
        }}
      />
      <div className="bg-gray-50 p-3 text-center text-sm text-gray-600 border-t">
        <div className="flex items-center justify-center space-x-4">
          <span>PDF Preview</span>
          <span className="text-gray-400">|</span>
          <a 
            href={pdfUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 flex items-center"
          >
            <ExternalLink className="w-4 h-4 mr-1" />
            Open in New Tab
          </a>
          <span className="text-gray-400">|</span>
          <a 
            href={pdfUrl}
            download={filename}
            className="text-primary-600 hover:text-primary-700 flex items-center"
          >
            <Download className="w-4 h-4 mr-1" />
            Download
          </a>
        </div>
      </div>
    </div>
  );
};

export default PDFViewer;
