import type { User } from "../types/auth";

/**
 * Caché local del usuario de la sesión actual.
 * La fuente de verdad es el backend (cookies httpOnly + /auth/me); esto solo
 * evita un parpadeo de "no autenticado" al recargar la página.
 */
const STORAGE_KEYS = {
  CURRENT_USER: "sigap_current_user_v2",
  REMEMBER_ME: "sigap_remember_me_v1",
};

type Listener = () => void;

class AuthStore {
  private listeners: Set<Listener> = new Set();
  private currentUser: User | null = null;

  constructor() {
    if (typeof window === "undefined") return;
    try {
      const raw =
        sessionStorage.getItem(STORAGE_KEYS.CURRENT_USER) ??
        localStorage.getItem(STORAGE_KEYS.CURRENT_USER);
      this.currentUser = raw ? JSON.parse(raw) : null;
    } catch {
      this.currentUser = null;
    }
  }

  public subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.listeners.forEach((fn) => fn());
  }

  public isRemembered(): boolean {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(STORAGE_KEYS.REMEMBER_ME) === "true";
  }

  public getCurrentUser(): User | null {
    return this.currentUser;
  }

  public setCurrentUser(user: User | null, rememberMe?: boolean): void {
    this.currentUser = user;
    if (typeof window !== "undefined") {
      localStorage.removeItem(STORAGE_KEYS.CURRENT_USER);
      sessionStorage.removeItem(STORAGE_KEYS.CURRENT_USER);

      if (!user) {
        localStorage.removeItem(STORAGE_KEYS.REMEMBER_ME);
      } else {
        const persist = rememberMe ?? this.isRemembered();
        const storage = persist ? localStorage : sessionStorage;
        storage.setItem(STORAGE_KEYS.CURRENT_USER, JSON.stringify(user));
        if (persist) localStorage.setItem(STORAGE_KEYS.REMEMBER_ME, "true");
        else localStorage.removeItem(STORAGE_KEYS.REMEMBER_ME);
      }
    }
    this.notify();
  }
}

export const store = new AuthStore();
