import type { UserRole } from "../types/auth";

/** Solo decide qué se muestra: los permisos reales los valida el backend. */
export const ROUTE_ACCESS: Record<string, UserRole[]> = {
  "/dashboard/users": ["admin"],
  "/dashboard/transactions": ["admin"],
  "/dashboard/revenue": ["admin"],
  "/dashboard/tariffs": ["admin"],
  "/dashboard/audit": ["admin"],
  "/dashboard/settings": ["admin"],
  "/dashboard/vehicles": ["admin", "operator"],
  "/dashboard/alerts": ["admin", "operator"],
  "/dashboard/devices": ["admin", "support"],
  "/dashboard/tickets": ["operator", "support"],
};

export function canVisit(path: string, role: UserRole | null): boolean {
  const allowed = ROUTE_ACCESS[path];
  return !allowed || (role !== null && allowed.includes(role));
}
