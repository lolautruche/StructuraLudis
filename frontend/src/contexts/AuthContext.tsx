'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  ReactNode,
} from 'react';
import {
  authApi,
  User,
  LoginRequest,
  RegisterRequest,
  getAccessToken,
  setAccessToken,
} from '@/lib/api';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (data: LoginRequest) => Promise<{ success: boolean; error?: string }>;
  register: (
    data: RegisterRequest
  ) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    const response = await authApi.getCurrentUser();
    if (response.data) {
      setUser(response.data);
    } else {
      // Token invalid, clear it
      setAccessToken(null);
      setUser(null);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = useCallback(
    async (data: LoginRequest) => {
      const response = await authApi.login(data);
      if (response.error) {
        return { success: false, error: response.error.message };
      }
      await refreshUser();
      return { success: true };
    },
    [refreshUser]
  );

  const register = useCallback(async (data: RegisterRequest) => {
    const response = await authApi.register(data);
    if (response.error) {
      return { success: false, error: response.error.message };
    }
    return { success: true };
  }, []);

  const logout = useCallback(() => {
    authApi.logout();
    setUser(null);
  }, []);

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}