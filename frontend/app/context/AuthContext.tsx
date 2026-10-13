import React, { createContext, useContext, useEffect, useState } from "react";
import type { User, UserRole, LoginCredentials, LoginResult } from "../types/auth";
import { authService } from "../services/authService";
import { store } from "../services/store";

interface AuthContextType {
  user: User | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<LoginResult>;
  logout: () => Promise<void>;
  isAdmin: boolean;
  canAccess: (allowedRoles: UserRole[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => store.getCurrentUser());
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    // Suscribirse a cambios del store central
    const unsubscribe = store.subscribe(() => {
      setUser(store.getCurrentUser());
    });
    // Revalidar la sesión cacheada contra el backend (rol/estado actualizados)
    if (store.getCurrentUser()) {
      authService.checkSession();
    }
    return unsubscribe;
  }, []);

  const login = async (credentials: LoginCredentials): Promise<LoginResult> => {
    setIsLoading(true);
    try {
      const res = await authService.login(credentials);
      if (res.success && res.user) {
        setUser(res.user);
        return { success: true, user: res.user, backendConnected: res.backendConnected };
      }
      return {
        success: false,
        error: res.error || "Error de autenticación",
        status: res.status,
        retryAfter: res.retryAfter,
        backendConnected: res.backendConnected,
      };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  const canAccess = (allowedRoles: UserRole[]) => {
    if (!user || !user.role) return false;
    return allowedRoles.includes(user.role);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role ?? null,
        isAuthenticated: !!user && user.isActive,
        isLoading,
        login,
        logout,
        isAdmin: user?.role === "admin",
        canAccess,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
