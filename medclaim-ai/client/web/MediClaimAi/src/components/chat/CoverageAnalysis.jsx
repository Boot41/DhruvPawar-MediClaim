import React from 'react';
import { motion } from 'framer-motion';
import { DollarSign, TrendingUp, Shield, AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';

const CoverageAnalysis = ({ analysisData }) => {
  if (!analysisData) return null;

  const {
    total_claim = 0,
    covered_amount = 0,
    out_of_pocket = 0,
    coverage_percentage = 0,
    deductible_applied = 0,
    copay_applied = 0
  } = analysisData;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(amount);
  };

  const analysisCards = [
    {
      title: 'Total Claim Amount',
      value: formatCurrency(total_claim),
      icon: DollarSign,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50'
    },
    {
      title: 'Insurance Coverage',
      value: formatCurrency(covered_amount),
      icon: Shield,
      color: 'text-green-600',
      bgColor: 'bg-green-50'
    },
    {
      title: 'Your Out-of-Pocket',
      value: formatCurrency(out_of_pocket),
      icon: AlertTriangle,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50'
    },
    {
      title: 'Coverage Percentage',
      value: `${coverage_percentage.toFixed(1)}%`,
      icon: TrendingUp,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50'
    }
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {analysisCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className={`p-2 rounded-lg ${card.bgColor}`}>
                      <Icon className={`h-5 w-5 ${card.color}`} />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-600">{card.title}</p>
                      <p className="text-lg font-bold text-gray-900">{card.value}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          );
        })}
      </div>

      {(deductible_applied > 0 || copay_applied > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Breakdown Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {deductible_applied > 0 && (
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Deductible Applied</span>
                  <span className="font-medium">{formatCurrency(deductible_applied)}</span>
                </div>
              )}
              {copay_applied > 0 && (
                <div className="flex justify-between items-center py-2 border-b border-gray-100">
                  <span className="text-gray-600">Co-pay Applied</span>
                  <span className="font-medium">{formatCurrency(copay_applied)}</span>
                </div>
              )}
              <div className="flex justify-between items-center py-2 font-semibold">
                <span className="text-gray-900">Final Coverage</span>
                <span className="text-green-600">{formatCurrency(covered_amount)}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
};

export default CoverageAnalysis;
