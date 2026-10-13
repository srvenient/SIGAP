import type { User, UserRole } from "../types/auth";

/** Error HTTP con el `detail` devuelto por FastAPI. */
export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

/** Forma cruda de `UserPublic` en el backend (snake_case). */
export interface UserPublicDTO {
  id: string;
  username: string;
  full_name?: string | null;
  email?: string | null;
  is_active: boolean;
  role_id: string | null;
  role: { id: string; name: string; description?: string | null } | null;
  must_change_password: boolean;
  locked_until: string | null;
  last_login: string | null;
  created_at: string;
  is_superuser?: boolean;
}

export function mapUser(dto: UserPublicDTO): User {
  return {
    id: dto.id,
    username: dto.username,
    fullName: dto.full_name ?? null,
    email: dto.email ?? null,
    role: (dto.role?.name as UserRole) ?? null,
    roleId: dto.role_id,
    isActive: dto.is_active,
    mustChangePassword: dto.must_change_password,
    lockedUntil: dto.locked_until,
    lastLogin: dto.last_login,
    createdAt: dto.created_at,
    isSuperuser: Boolean(dto.is_superuser ?? (dto.username === "admin")),
  };
}

let refreshing: Promise<boolean> | null = null;

/** Un solo /refresh en vuelo aunque fallen varias peticiones a la vez. */
function refreshSession(): Promise<boolean> {
  refreshing ??= fetch("/api/v1/auth/refresh", { method: "POST", credentials: "include" })
    .then((r) => r.ok)
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

/**
 * fetch contra /api/v1 con cookies httpOnly. Ante un 401 intenta renovar
 * la sesión una vez y reintenta la petición original.
 */
export async function apiFetch<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const res = await fetch(`/api/v1${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init.body ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });

  if (res.status === 401 && retry && (await refreshSession())) {
    return apiFetch<T>(path, init, false);
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail = Array.isArray(data.detail)
      ? data.detail.map((d: { msg: string }) => d.msg).join(", ") // errores de validación 422
      : data.detail;
    throw new ApiError(res.status, detail || `Error del servidor (${res.status})`);
  }

  return (res.status === 204 ? undefined : await res.json()) as T;
}
