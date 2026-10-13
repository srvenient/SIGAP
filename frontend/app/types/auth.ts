export type UserRole = "admin" | "operator" | "support";

export interface Role {
  id: string;
  name: UserRole;
  description?: string | null;
}

/** Espejo de `UserPublic` del backend, en camelCase. */
export interface User {
  id: string;
  username: string;
  fullName: string | null;
  email: string | null;
  role: UserRole | null;
  roleId: string | null;
  isActive: boolean;
  mustChangePassword: boolean;
  lockedUntil: string | null;
  lastLogin: string | null;
  createdAt: string;
  isSuperuser?: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

export interface LoginResult {
  success: boolean;
  user?: User;
  error?: string;
  status?: number;
  retryAfter?: number;
  backendConnected?: boolean;
}
