import { createContext, useEffect, useMemo, useState } from 'react';

import { ApiError, apiClient } from '../api/http';
import type { UserDto } from '../types/api';

export interface AuthContextValue {
  user: UserDto | null;
  loading: boolean;
  refreshCurrentUser: () => Promise<void>;
  login: (identifier: string, password: string) => Promise<UserDto>;
  logout: () => Promise<void>;
  clearSession: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserDto | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  async function refreshCurrentUser(): Promise<void> {
    try {
      const nextUser = await apiClient.getCurrentUser();
      setUser(nextUser);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setUser(null);
        return;
      }
      throw error;
    }
  }

  async function login(identifier: string, password: string): Promise<UserDto> {
    const payload = await apiClient.login(identifier, password);
    setUser(payload.user);
    return payload.user;
  }

  async function logout(): Promise<void> {
    await apiClient.logout();
    setUser(null);
  }

  function clearSession(): void {
    setUser(null);
  }

  useEffect(() => {
    refreshCurrentUser().finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, refreshCurrentUser, login, logout, clearSession }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
