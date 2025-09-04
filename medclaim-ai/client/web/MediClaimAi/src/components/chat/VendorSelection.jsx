import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Building, Check } from 'lucide-react';
import { Card, CardContent } from '../ui/Card';
import Button from '../ui/Button';

const VendorSelection = ({ vendors = [], onVendorSelect, selectedVendor }) => {
  const [hoveredVendor, setHoveredVendor] = useState(null);

  const defaultVendors = [
    'Star Health Insurance',
    'HDFC ERGO Health Insurance',
    'ICICI Lombard Health Insurance',
    'Bajaj Allianz Health Insurance',
    'New India Assurance Health Insurance'
  ];

  const vendorList = vendors.length > 0 ? vendors : defaultVendors;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-2">
          Select Your Insurance Provider
        </h3>
        <p className="text-gray-600">
          Choose your insurance company to proceed with the claim form
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {vendorList.map((vendor, index) => (
          <motion.div
            key={vendor}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: index * 0.1 }}
            onMouseEnter={() => setHoveredVendor(vendor)}
            onMouseLeave={() => setHoveredVendor(null)}
          >
            <Card 
              className={`cursor-pointer transition-all duration-200 hover:shadow-lg ${
                selectedVendor === vendor 
                  ? 'ring-2 ring-blue-500 bg-blue-50' 
                  : hoveredVendor === vendor 
                    ? 'shadow-md' 
                    : ''
              }`}
              onClick={() => onVendorSelect(vendor)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${
                      selectedVendor === vendor ? 'bg-blue-100' : 'bg-gray-100'
                    }`}>
                      <Building className={`h-5 w-5 ${
                        selectedVendor === vendor ? 'text-blue-600' : 'text-gray-600'
                      }`} />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{vendor}</p>
                      <p className="text-sm text-gray-500">Insurance Provider</p>
                    </div>
                  </div>
                  
                  {selectedVendor === vendor && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="w-6 h-6 bg-blue-600 rounded-full flex items-center justify-center"
                    >
                      <Check className="h-4 w-4 text-white" />
                    </motion.div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500 mb-4">
          Don't see your provider? You can enter it manually:
        </p>
        <div className="flex gap-2 max-w-md mx-auto">
          <input
            type="text"
            placeholder="Enter insurance provider name"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => {
              if (e.key === 'Enter' && e.target.value.trim()) {
                onVendorSelect(e.target.value.trim());
                e.target.value = '';
              }
            }}
          />
          <Button
            onClick={(e) => {
              const input = e.target.parentElement.querySelector('input');
              if (input.value.trim()) {
                onVendorSelect(input.value.trim());
                input.value = '';
              }
            }}
          >
            Add
          </Button>
        </div>
      </div>
    </motion.div>
  );
};

export default VendorSelection;
