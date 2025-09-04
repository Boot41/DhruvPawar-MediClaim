import React, { createContext, useContext, useState, useEffect } from 'react';
import apiService from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    // Check for stored token on app load
    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('userData');
    const sessionId = localStorage.getItem('sessionId');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setIsAuthenticated(true);
        apiService.setAuthToken(token);
        
        // Restore session ID if available
        if (sessionId) {
          apiService.setSessionId(sessionId);
        }
      } catch (error) {
        console.error('Error parsing stored user data:', error);
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
        localStorage.removeItem('sessionId');
      }
    }
    setLoading(false);
  }, []);

  const login = async (credentials) => {
    try {
      const response = await apiService.login(credentials);
      
      if (response.success) {
        const { access_token, user: userData, session_id } = response.data;
        
        // Store auth data
        localStorage.setItem('authToken', access_token);
        localStorage.setItem('userData', JSON.stringify(userData));
        localStorage.setItem('sessionId', session_id);
        
        // Update state
        setUser(userData);
        setIsAuthenticated(true);
        apiService.setAuthToken(access_token);
        apiService.setSessionId(session_id);
        
        return { success: true, user: userData };
      } else {
        return { success: false, error: response.message || 'Login failed' };
      }
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const register = async (userData) => {
    try {
      const response = await apiService.register(userData);
      
      if (response.success) {
        return { success: true, message: 'Registration successful. Please login.' };
      } else {
        return { success: false, error: response.message || 'Registration failed' };
      }
    } catch (error) {
      console.error('Registration error:', error);
      return { success: false, error: 'Network error. Please try again.' };
    }
  };

  const logout = () => {
    // Clear stored data
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    localStorage.removeItem('sessionId');
    
    // Clear API service
    apiService.logout();
    
    // Update state
    setUser(null);
    setIsAuthenticated(false);
  };

  const value = {
    user,
    isAuthenticated,
    loading,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
