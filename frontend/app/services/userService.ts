import { apiFetch, mapUser, type UserPublicDTO } from "./api";
import type { Role, User } from "../types/auth";

/**
 * Gestión de usuarios contra /api/v1/users.
 * Todas las rutas exigen rol admin en el backend (403 en caso contrario).
 */
export const userService = {
  async list(skip = 0, limit = 100): Promise<{ users: User[]; count: number }> {
    const res = await apiFetch<{ data: UserPublicDTO[]; count: number }>(
      `/users?skip=${skip}&limit=${limit}`
    );
    return { users: res.data.map(mapUser), count: res.count };
  },

  async listRoles(): Promise<Role[]> {
    const res = await apiFetch<{ roles: Role[]; count: number }>("/users/roles");
    return res.roles;
  },

  async create(data: { username: string; password: string; roleId: string; isActive?: boolean }): Promise<User> {
    const dto = await apiFetch<UserPublicDTO>("/users", {
      method: "POST",
      body: JSON.stringify({
        username: data.username,
        password: data.password,
        role_id: data.roleId,
        is_active: data.isActive ?? true,
      }),
    });
    return mapUser(dto);
  },

  async update(id: string, changes: { roleId?: string; isActive?: boolean }): Promise<User> {
    const dto = await apiFetch<UserPublicDTO>(`/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ role_id: changes.roleId, is_active: changes.isActive }),
    });
    return mapUser(dto);
  },

  /** Devuelve la contraseña temporal; el backend no la vuelve a mostrar. */
  async resetPassword(id: string): Promise<string> {
    const res = await apiFetch<{ temporary_password: string }>(`/users/${id}/reset-password`, {
      method: "POST",
    });
    return res.temporary_password;
  },

  async unlock(id: string): Promise<void> {
    await apiFetch<void>(`/users/${id}/unlock`, { method: "POST" });
  },
};
