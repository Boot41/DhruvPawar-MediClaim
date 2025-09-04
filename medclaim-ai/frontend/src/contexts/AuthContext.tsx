/**
 * Authentication Context
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User, authAPI } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('access_token');
    const storedEmail = localStorage.getItem('user_email');
    if (storedToken && storedEmail) {
      setToken(storedToken);
      setUser({
        id: '',
        email: storedEmail,
        full_name: '',
        is_active: true,
        created_at: new Date().toISOString()
      });
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await authAPI.login(email, password);
      const { access_token } = response;
      
      setToken(access_token);
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user_email', email);
      
      // Set user data (basic info from login)
      setUser({
        id: '', // Will be populated from token or API call
        email: email,
        full_name: '',
        is_active: true,
        created_at: new Date().toISOString()
      });
      
      // Create session after login
      const sessionResponse = await authAPI.createSession();
      console.log('Session created:', sessionResponse);
      
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const register = async (email: string, password: string, fullName?: string) => {
    try {
      await authAPI.register(email, password, fullName);
      // Auto-login after registration
      await login(email, password);
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_email');
    // Force redirect to login page
    window.location.href = '/login';
  };

  const value = {
    user,
    token,
    login,
    register,
    logout,
    loading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
