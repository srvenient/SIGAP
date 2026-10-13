import { store } from "./store";
import { apiFetch, ApiError, mapUser, type UserPublicDTO } from "./api";
import type { User, LoginCredentials, LoginResult } from "../types/auth";

/** Obtiene el usuario autenticado (incluye su rol real desde la BD). */
async function fetchMe(): Promise<User> {
  return mapUser(await apiFetch<UserPublicDTO>("/auth/me"));
}

export const authService = {
  /**
   * POST /api/v1/auth/login (OAuth2PasswordRequestForm → x-www-form-urlencoded).
   * El backend deja las cookies httpOnly; luego se consulta /me para el perfil.
   */
  login: async (credentials: LoginCredentials): Promise<LoginResult> => {
    const rememberMe = credentials.rememberMe ?? false;
    const form = new URLSearchParams({
      username: credentials.username.trim(),
      password: credentials.password,
      remember_me: String(rememberMe),
    });

    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
        credentials: "include",
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const retryAfter = response.headers.get("Retry-After");
        return {
          success: false,
          error:
            data.detail ||
            (response.status === 429
              ? "Demasiados intentos fallidos. Intente más tarde."
              : `Error del servidor (${response.status})`),
          status: response.status,
          retryAfter: retryAfter ? parseInt(retryAfter, 10) : undefined,
          backendConnected: response.status !== 502,
        };
      }

      const user = await fetchMe();
      store.setCurrentUser(user, rememberMe);
      return { success: true, user, backendConnected: true };
    } catch (err) {
      return {
        success: false,
        error:
          err instanceof ApiError
            ? err.message
            : "No se pudo conectar con el servidor. Verifique que el backend esté activo.",
        status: err instanceof ApiError ? err.status : undefined,
        backendConnected: err instanceof ApiError,
      };
    }
  },

  changePassword: async (currentPassword: string, newPassword: string): Promise<{ success: boolean; error?: string }> => {
    try {
      await apiFetch<{ detail: string }>("/auth/change-password", {
        method: "POST",
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });
      await authService.checkSession();
      return { success: true };
    } catch (err) {
      return {
        success: false,
        error: err instanceof ApiError ? err.message : "Error al actualizar la contraseña.",
      };
    }
  },

  logout: async (): Promise<void> => {
    try {
      await fetch("/api/v1/auth/logout", { method: "POST", credentials: "include" });
    } catch {
      // Si el backend no responde igual se limpia la sesión local
    }
    store.setCurrentUser(null);
  },

  /** Revalida la sesión contra el backend (renueva el access token si hace falta). */
  checkSession: async (): Promise<User | null> => {
    try {
      const user = await fetchMe();
      store.setCurrentUser(user);
      return user;
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        store.setCurrentUser(null);
        return null;
      }
      return store.getCurrentUser(); // backend caído: se conserva la caché
    }
  },

  getCurrentUser: (): User | null => store.getCurrentUser(),
};
