/**
 * Header Component
 */
import React from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { LogOut, User, FileText } from 'lucide-react';

const Header: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white shadow-sm border-b border-secondary-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-primary-600 rounded-lg">
              <FileText className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-secondary-900">MediClaim AI</h1>
              <p className="text-sm text-secondary-500">Insurance Claim Assistant</p>
            </div>
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {user && (
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2 text-secondary-600">
                  <User className="w-4 h-4" />
                  <span className="text-sm font-medium">{user.email}</span>
                </div>
                <button
                  onClick={logout}
                  className="flex items-center space-x-2 text-secondary-500 hover:text-secondary-700 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  <span className="text-sm">Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
