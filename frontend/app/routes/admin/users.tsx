import React, { useEffect, useMemo, useRef, useState } from "react";
import { useRevalidator } from "react-router";
import type { Route } from "./+types/users";
import {
  UserPlus,
  AlertTriangle,
  Search,
  KeyRound,
  Lock,
  Unlock,
  RefreshCw,
  Copy,
  Check,
  Eye,
  EyeOff,
  X,
  UserCog,
  Power,
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Car,
  Headset,
  ArrowRight,
  SlidersHorizontal,
  type LucideIcon,
} from "lucide-react";
import { userService } from "../../services/userService";
import { ApiError } from "../../services/api";
import type { Role, User, UserRole } from "../../types/auth";
import { Card } from "../../components/ui/Card";
import { Badge } from "../../components/ui/Badge";
import { useToast } from "../../context/ToastContext";
import { useAuth } from "../../context/AuthContext";

const ROLE_LABELS: Record<UserRole, { label: string; variant: "purple" | "primary" | "cyan" }> = {
  admin: { label: "Administrador", variant: "purple" },
  operator: { label: "Operador de Patio", variant: "primary" },
  support: { label: "Soporte Técnico", variant: "cyan" },
};

const ROLE_META: Record<UserRole, { icon: LucideIcon; description: string }> = {
  admin: {
    icon: ShieldCheck,
    description: "Control total: cuentas, tarifas, transacciones y auditoría.",
  },
  operator: {
    icon: Car,
    description: "Opera el patio: ingreso manual, vehículos y tiquetes.",
  },
  support: {
    icon: Headset,
    description: "Atiende dispositivos y tiquetes del sistema.",
  },
};

type ConfirmKind = "toggle" | "reset" | "unlock" | "role";
type ConfirmState = { kind: ConfirmKind; target: User } | null;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

const ROLE_ORDER: Record<string, number> = { admin: 0, operator: 1, support: 2 };
const NO_ROLE_RANK = 99;
const roleRank = (name: string | null | undefined) =>
  name ? ROLE_ORDER[name] ?? NO_ROLE_RANK : NO_ROLE_RANK;

type SortKey = "fullName" | "username" | "email" | "role" | "lastLogin" | "createdAt";
type SortDir = "asc" | "desc";

const ROLE_FILTER_OPTIONS: { value: "todos" | UserRole; label: string }[] = [
  { value: "todos", label: "Todos los roles" },
  { value: "admin", label: "Administradores" },
  { value: "operator", label: "Operadores de patio" },
  { value: "support", label: "Soporte técnico" },
];

const PAGE_SIZES = [5, 10, 20, 50];

const inputCls =
  "w-full rounded-lg bg-bg-app border border-border-primary px-3 py-2 text-sm text-text-primary placeholder:text-text-disabled outline-none transition-all hover:border-border-strong focus:border-primary-DEFAULT focus:ring-3 focus:ring-primary-muted";

const errorMessage = (err: unknown) =>
  err instanceof ApiError ? err.message : "No se pudo conectar con el servidor.";

const isLocked = (u: User) => !!u.lockedUntil && new Date(u.lockedUntil) > new Date();

const timestamp = (iso: string | null) => (iso ? new Date(iso).getTime() : 0);

const formatDate = (iso: string | null, withTime = false) =>
  iso
    ? new Date(iso).toLocaleString("es-CO", {
      day: "2-digit",
      month: "short",
      year: withTime ? undefined : "numeric",
      ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
    })
    : "Sin accesos";

/** Genera una contraseña aleatoria criptográficamente segura (letras, números y símbolos). */
const generatePassword = (length = 14) => {
  const upper = "ABCDEFGHJKLMNPQRSTUVWXYZ";
  const lower = "abcdefghijkmnopqrstuvwxyz";
  const digits = "23456789";
  const symbols = "!@#$%*?-_";
  const all = upper + lower + digits + symbols;

  const rand = (max: number) => {
    const buf = new Uint32Array(1);
    crypto.getRandomValues(buf);
    return buf[0] % max;
  };

  // Garantiza al menos un carácter de cada grupo
  const chars = [upper, lower, digits, symbols].map((set) => set[rand(set.length)]);
  while (chars.length < length) chars.push(all[rand(all.length)]);

  // Fisher-Yates
  for (let i = chars.length - 1; i > 0; i--) {
    const j = rand(i + 1);
    [chars[i], chars[j]] = [chars[j], chars[i]];
  }
  return chars.join("");
};

/** Lista de páginas con elipsis: 1 … 4 5 6 … 12 */
const pageList = (current: number, total: number): (number | "…")[] => {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const keep = [...new Set([1, total, current - 1, current, current + 1])]
    .filter((n) => n >= 1 && n <= total)
    .sort((a, b) => a - b);
  const out: (number | "…")[] = [];
  keep.forEach((n, i) => {
    if (i > 0 && n - keep[i - 1] > 1) out.push("…");
    out.push(n);
  });
  return out;
};

export async function clientLoader() {
  const [{ users }, roles] = await Promise.all([
    userService.list(),
    userService.listRoles(),
  ]);
  return { users, roles };
}

export default function AdminUsers({ loaderData }: Route.ComponentProps) {
  const { user: currentAdmin } = useAuth();
  const { toast } = useToast();
  const revalidator = useRevalidator();

  const [users, setUsers] = useState<User[]>(loaderData.users);
  const roles = loaderData.roles;
  const [busyId, setBusyId] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState<"todos" | UserRole>("todos");
  const [sortKey, setSortKey] = useState<SortKey>("role");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newFullName, setNewFullName] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(true);
  const [copiedNew, setCopiedNew] = useState(false);
  const [newRoleId, setNewRoleId] = useState("");
  const [createError, setCreateError] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const [editing, setEditing] = useState<User | null>(null);
  const [editRoleId, setEditRoleId] = useState("");
  const [editError, setEditError] = useState("");

  const [showCancelCreateConfirm, setShowCancelCreateConfirm] = useState(false);
  const [showCreateConfirm, setShowCreateConfirm] = useState(false);

  const [confirm, setConfirm] = useState<ConfirmState>(null);

  const [tempPassword, setTempPassword] = useState<{ username: string; value: string } | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setUsers(loaderData.users);
  }, [loaderData.users]);

  // Cualquier cambio de filtros o tamaño de página vuelve a la primera página
  useEffect(() => {
    setPage(1);
  }, [searchTerm, roleFilter, pageSize]);

  const sortedRoles = useMemo(
    () => [...roles].sort((a, b) => roleRank(a.name) - roleRank(b.name)),
    [roles]
  );

  const replaceUser = (updated: User) =>
    setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));

  const processedUsers = useMemo(() => {
    const term = searchTerm.toLowerCase();
    const filtered = users.filter(
      (u) =>
        (u.username.toLowerCase().includes(term) ||
          (u.fullName ?? "").toLowerCase().includes(term) ||
          (u.email ?? "").toLowerCase().includes(term)) &&
        (roleFilter === "todos" || u.role === roleFilter)
    );

    return filtered.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "role":
          cmp = roleRank(a.role) - roleRank(b.role) || a.username.localeCompare(b.username);
          break;
        case "fullName":
          cmp = (a.fullName || "").localeCompare(b.fullName || "") || a.username.localeCompare(b.username);
          break;
        case "username":
          cmp = a.username.localeCompare(b.username);
          break;
        case "email":
          cmp = (a.email || "").localeCompare(b.email || "");
          break;
        case "lastLogin":
          cmp = timestamp(a.lastLogin) - timestamp(b.lastLogin);
          break;
        case "createdAt":
          cmp = timestamp(a.createdAt) - timestamp(b.createdAt);
          break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [users, searchTerm, roleFilter, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(processedUsers.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const startIndex = (currentPage - 1) * pageSize;
  const pagedUsers = processedUsers.slice(startIndex, startIndex + pageSize);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const openCreate = () => {
    setNewUsername("");
    setNewFullName("");
    setNewEmail("");
    setNewPassword(generatePassword());
    setShowNewPassword(true);
    setCopiedNew(false);
    setNewRoleId(
      sortedRoles.find((r) => r.name === "operator")?.id ?? sortedRoles[0]?.id ?? ""
    );
    setCreateError("");
    setShowCancelCreateConfirm(false);
    setShowCreateConfirm(false);
    setIsCreateOpen(true);
  };

  const handleRequestCloseCreate = () => {
    setShowCancelCreateConfirm(true);
  };

  const confirmDiscardCreate = () => {
    setShowCancelCreateConfirm(false);
    setIsCreateOpen(false);
    setNewFullName("");
    setNewEmail("");
    setNewUsername("");
    setCreateError("");
  };

  const regeneratePassword = () => {
    setNewPassword(generatePassword());
    setCopiedNew(false);
  };

  const copyNewPassword = async () => {
    try {
      await navigator.clipboard.writeText(newPassword);
      setCopiedNew(true);
      toast("Contraseña copiada al portapapeles", "info");
      setTimeout(() => setCopiedNew(false), 2000);
    } catch {
      toast("No se pudo copiar la contraseña", "error");
    }
  };

  const handleCreate = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setCreateError("");

    const username = newUsername.trim();
    const fullName = newFullName.trim().replace(/\s+/g, " ");
    const email = newEmail.trim().toLowerCase();
    if (fullName.length < 2) {
      return setCreateError("Ingrese el nombre completo de la persona.");
    }
    if (!EMAIL_RE.test(email)) {
      return setCreateError("Ingrese un correo electrónico válido.");
    }
    if (username.length < 3 || username.length > 20) {
      return setCreateError("El nombre de usuario debe tener entre 3 y 20 caracteres.");
    }
    if (/[\s@]/.test(username)) {
      return setCreateError("El nombre de usuario no puede contener espacios ni '@'.");
    }
    if (newPassword.length < 8 || newPassword.length > 40) {
      return setCreateError("La contraseña debe tener entre 8 y 40 caracteres.");
    }
    if (!newRoleId) return setCreateError("Seleccione un rol.");

    setShowCreateConfirm(true);
  };

  const executeCreateAccount = async () => {
    const username = newUsername.trim();
    const fullName = newFullName.trim().replace(/\s+/g, " ");
    const email = newEmail.trim().toLowerCase();

    setIsCreating(true);
    try {
      const created = await userService.create({
        username,
        fullName,
        email,
        password: newPassword,
        roleId: newRoleId,
      });
      setUsers((prev) => [...prev, created]);
      setShowCreateConfirm(false);
      setIsCreateOpen(false);
      revalidator.revalidate();
      toast(
        `@${created.username} deberá cambiar la contraseña en su primer ingreso`,
        "success",
        "Cuenta creada"
      );
    } catch (err) {
      setShowCreateConfirm(false);
      setCreateError(errorMessage(err));
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateRole = async () => {
    if (!editing) return;
    if (editing.isSuperuser || editing.username === "admin") {
      toast("La cuenta superusuario está protegida y no puede ser modificada", "error", "Operación denegada");
      setEditing(null);
      return;
    }
    setEditError("");
    try {
      const updated = await userService.update(editing.id, { roleId: editRoleId });
      replaceUser(updated);
      setEditing(null);
      revalidator.revalidate();
      toast(`Rol de @${updated.username} actualizado`, "success");
    } catch (err) {
      setEditError(errorMessage(err));
    }
  };

  const runAction = async (target: User, action: () => Promise<void>) => {
    setBusyId(target.id);
    try {
      await action();
    } catch (err) {
      toast(errorMessage(err), "error", "Operación denegada");
    } finally {
      setBusyId(null);
    }
  };

  const handleToggleStatus = (target: User) => {
    if (target.isSuperuser || target.username === "admin") {
      toast("La cuenta superusuario está protegida y no puede ser modificada", "error", "Operación denegada");
      return;
    }
    return runAction(target, async () => {
      const updated = await userService.update(target.id, { isActive: !target.isActive });
      replaceUser(updated);
      revalidator.revalidate();
      toast(
        `Cuenta @${updated.username} ${updated.isActive ? "reactivada" : "desactivada"}`,
        updated.isActive ? "success" : "warning"
      );
    });
  };

  const handleResetPassword = (target: User) => {
    if (target.isSuperuser || target.username === "admin") {
      toast("La cuenta superusuario está protegida y no puede ser modificada", "error", "Operación denegada");
      return;
    }
    return runAction(target, async () => {
      const value = await userService.resetPassword(target.id);
      replaceUser({ ...target, mustChangePassword: true, lockedUntil: null });
      setCopied(false);
      setTempPassword({ username: target.username, value });
      revalidator.revalidate();
    });
  };

  const handleUnlock = (target: User) => {
    if (target.isSuperuser || target.username === "admin") {
      toast("La cuenta superusuario está protegida y no puede ser modificada", "error", "Operación denegada");
      return;
    }
    return runAction(target, async () => {
      await userService.unlock(target.id);
      replaceUser({ ...target, lockedUntil: null });
      revalidator.revalidate();
      toast(`Cuenta @${target.username} desbloqueada`, "success");
    });
  };

  const executeConfirm = async () => {
    if (!confirm) return;
    const { kind, target } = confirm;
    setConfirm(null);
    if (target.isSuperuser || target.username === "admin") {
      toast("La cuenta superusuario está protegida y no puede ser modificada", "error", "Operación denegada");
      return;
    }
    if (kind === "toggle") await handleToggleStatus(target);
    else if (kind === "reset") await handleResetPassword(target);
    else if (kind === "unlock") await handleUnlock(target);
    else await handleUpdateRole();
  };

  const copyTempPassword = async () => {
    if (!tempPassword) return;
    await navigator.clipboard.writeText(tempPassword.value);
    setCopied(true);
  };

  const rangeFrom = processedUsers.length === 0 ? 0 : startIndex + 1;
  const rangeTo = Math.min(startIndex + pageSize, processedUsers.length);

  return (
    <div className="space-y-5 animate-in fade-in duration-200">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
        <div className="flex flex-col sm:flex-row items-center gap-2.5 w-full lg:w-auto">
          <div className="relative w-full sm:w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted pointer-events-none" />
            <input
              type="text"
              placeholder="Buscar cuentas..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-8 py-2 rounded-lg bg-bg-app border border-border-primary text-xs text-text-primary placeholder:text-text-disabled outline-none transition-all hover:border-border-strong focus:border-primary-DEFAULT focus:ring-3 focus:ring-primary-muted font-sans"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm("")}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-0.5 rounded transition-colors cursor-pointer"
                aria-label="Limpiar búsqueda"
              >
                <X className="w-3 h-3" />
              </button>
            )}
          </div>

          <CustomSelect<"todos" | UserRole>
            ariaLabel="Filtrar por rol"
            value={roleFilter}
            onChange={setRoleFilter}
            className="w-full sm:w-48"
            leftIcon={<SlidersHorizontal className="w-3.5 h-3.5 text-text-muted shrink-0" />}
            options={ROLE_FILTER_OPTIONS}
          />
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-2.5 w-full lg:w-auto justify-end">
          <button
            type="button"
            onClick={openCreate}
            disabled={roles.length === 0}
            className="flex justify-center items-center gap-2 px-3 py-2 bg-primary-DEFAULT rounded-lg w-full sm:w-auto shrink-0 cursor-pointer"
          >
            <UserPlus className="w-4 h-4" />
            <span className="font-special font-bold text-[13px]">Nueva cuenta</span>
          </button>
        </div>
      </div>

      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-bg-app/50 border-b border-border-secondary">
              <tr className="text-text-muted uppercase tracking-wider text-[10px] font-special">
                <SortTh label="Nombre" k="fullName" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} className="px-5" />
                <SortTh label="Usuario" k="username" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
                <SortTh label="Correo" k="email" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
                <SortTh label="Rol" k="role" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
                <th className="py-3 px-4 font-bold">Estado</th>
                <SortTh label="Último acceso" k="lastLogin" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
                <SortTh label="Alta" k="createdAt" sortKey={sortKey} sortDir={sortDir} onSort={toggleSort} />
                <th className="py-3 px-5 text-right font-bold">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-secondary">
              {pagedUsers.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-text-muted">
                    No hay cuentas que coincidan con los filtros.
                  </td>
                </tr>
              ) : (
                pagedUsers.map((u) => {
                  const isSelf = u.id === currentAdmin?.id;
                  const isSuperuser = Boolean(u.isSuperuser || u.username === "admin");
                  const locked = isLocked(u);
                  const busy = busyId === u.id;
                  const role = u.role ? ROLE_LABELS[u.role] : null;

                  return (
                    <tr key={u.id} className="hover:bg-bg-accent/20 transition-colors">
                      <td className="py-3 px-5">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-bg-accent border border-border-strong/50 flex items-center justify-center font-mono font-bold text-text-primary text-[11px] shrink-0 uppercase">
                            {(u.fullName || u.username).slice(0, 2)}
                          </div>
                          <span className="font-semibold text-text-primary truncate">
                            {u.fullName || <span className="text-text-disabled font-normal italic">Sin registrar</span>}
                          </span>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5 font-mono">
                          <span className="font-medium text-text-primary">@{u.username}</span>
                          {isSelf && <span className="text-[10px] text-text-muted">(tú)</span>}
                          {isSuperuser && (
                            <span
                              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20"
                              title="Superusuario definido en variables de entorno (.env)"
                            >
                              <ShieldCheck className="w-3 h-3" />
                              Superuser
                            </span>
                          )}
                        </div>
                        {u.mustChangePassword && (
                          <p className="text-[10px] text-status-warning mt-0.5">
                            Cambio pendiente
                          </p>
                        )}
                      </td>
                      <td className="py-3 px-4 text-text-secondary font-mono truncate max-w-55" title={u.email ?? undefined}>
                        {u.email || <span className="text-text-disabled">—</span>}
                      </td>
                      <td className="py-3 px-4">
                        {role ? (
                          <Badge variant={role.variant} size="sm">
                            {role.label}
                          </Badge>
                        ) : (
                          <Badge variant="neutral" size="sm">Sin rol</Badge>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1.5">
                          <Badge variant={u.isActive ? "success" : "danger"} size="sm" dot>
                            {u.isActive ? "Activo" : "Desactivado"}
                          </Badge>
                          {locked && (
                            <Badge variant="warning" size="sm">
                              <Lock className="w-3 h-3" />
                              Bloqueado
                            </Badge>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-text-secondary font-mono">{formatDate(u.lastLogin, true)}</td>
                      <td className="py-3 px-4 text-text-muted font-mono">{formatDate(u.createdAt)}</td>
                      <td className="py-3 px-5">
                        {/* El backend también rechaza estas acciones sobre superuser y sobre la propia cuenta */}
                        {isSuperuser ? (
                          <div
                            className="flex items-center justify-end gap-1.5 text-text-muted text-[11px]"
                            title="Cuenta superusuario protegida por .env"
                          >
                            <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                            <span className="font-mono">Protegido</span>
                          </div>
                        ) : isSelf ? (
                          <p className="text-right text-[11px] text-text-muted">—</p>
                        ) : (
                          <div className="flex items-center justify-end gap-1">
                            {locked && (
                              <ActionBtn title="Desbloquear cuenta" disabled={busy} onClick={() => setConfirm({ kind: "unlock", target: u })} tone="success">
                                <Unlock className="w-3.5 h-3.5" />
                              </ActionBtn>
                            )}
                            <ActionBtn
                              title="Cambiar rol"
                              disabled={busy}
                              onClick={() => {
                                setEditing(u);
                                setEditRoleId(u.roleId ?? "");
                                setEditError("");
                              }}
                            >
                              <UserCog className="w-3.5 h-3.5" />
                            </ActionBtn>
                            <ActionBtn title="Restablecer contraseña" disabled={busy} onClick={() => setConfirm({ kind: "reset", target: u })}>
                              <KeyRound className="w-3.5 h-3.5" />
                            </ActionBtn>
                            <ActionBtn
                              title={u.isActive ? "Desactivar cuenta" : "Reactivar cuenta"}
                              disabled={busy}
                              onClick={() => setConfirm({ kind: "toggle", target: u })}
                              tone={u.isActive ? "warning" : "success"}
                            >
                              <Power className="w-3.5 h-3.5" />
                            </ActionBtn>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Paginación */}
        {processedUsers.length > 0 && (
          <div className="px-5 py-3 border-t border-border-secondary flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-text-muted">
            <div className="flex items-center gap-3">
              <span>
                Mostrando <span className="text-text-primary font-medium">{rangeFrom}–{rangeTo}</span> de{" "}
                <span className="text-text-primary font-medium">{processedUsers.length}</span>
              </span>
              <div className="flex items-center gap-2">
                <span>Filas por página</span>
                <CustomSelect<number>
                  ariaLabel="Filas por página"
                  value={pageSize}
                  onChange={setPageSize}
                  dropUp
                  compact
                  className="w-18"
                  options={PAGE_SIZES.map((s) => ({ value: s, label: String(s) }))}
                />
              </div>
            </div>

            <nav className="flex items-center gap-1" aria-label="Paginación">
              <PageBtn
                aria-label="Página anterior"
                disabled={currentPage === 1}
                onClick={() => setPage(currentPage - 1)}
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </PageBtn>
              {pageList(currentPage, totalPages).map((p, i) =>
                p === "…" ? (
                  <span key={`gap-${i}`} className="px-1.5 text-text-disabled">…</span>
                ) : (
                  <PageBtn key={p} active={p === currentPage} onClick={() => setPage(p)}>
                    {p}
                  </PageBtn>
                )
              )}
              <PageBtn
                aria-label="Página siguiente"
                disabled={currentPage === totalPages}
                onClick={() => setPage(currentPage + 1)}
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </PageBtn>
            </nav>
          </div>
        )}
      </Card>

      {/* Crear cuenta */}
      <Dialog
        isOpen={isCreateOpen}
        onClose={handleRequestCloseCreate}
        closeOnEsc={!showCancelCreateConfirm && !showCreateConfirm}
        title="Nueva cuenta de acceso"
        subtitle="El usuario deberá cambiar la contraseña en su primer inicio de sesión"
        footer={
          <>
            <button
              type="button"
              className="btn-secondary"
              onClick={handleRequestCloseCreate}
              disabled={isCreating}
            >
              Cancelar
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={() => handleCreate()}
              disabled={isCreating}
            >
              {isCreating ? "Creando..." : "Crear cuenta"}
            </button>
          </>
        }
      >
        <form onSubmit={handleCreate} className="space-y-5">
          {createError && <ErrorBox message={createError} />}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="new-fullname" className="label">Nombre completo</label>
              <input
                id="new-fullname"
                className={inputCls}
                placeholder="ej: Mario Gómez"
                value={newFullName}
                onChange={(e) => setNewFullName(e.target.value)}
                autoComplete="off"
                maxLength={80}
                required
              />
            </div>
            <div>
              <label htmlFor="new-email" className="label">Correo electrónico</label>
              <input
                id="new-email"
                type="email"
                className={inputCls}
                placeholder="mario@empresa.com"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                autoComplete="off"
                maxLength={120}
                required
              />
            </div>
          </div>

          <div>
            <label htmlFor="new-username" className="label">Nombre de usuario</label>
            <input
              id="new-username"
              className={inputCls}
              placeholder="ej: mario.gomez"
              value={newUsername}
              onChange={(e) => setNewUsername(e.target.value)}
              autoComplete="off"
              required
            />
            <p className="mt-1.5 text-[11px] text-text-muted">
              Entre 3 y 20 caracteres, sin espacios ni «@». Podrá iniciar sesión con el usuario o el correo.
            </p>
          </div>

          <div>
            <span className="label">Rol</span>
            <RoleSelector roles={sortedRoles} value={newRoleId} onChange={setNewRoleId} />
          </div>

          <div>
            <label htmlFor="new-password" className="label">Contraseña inicial</label>
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <input
                  id="new-password"
                  readOnly
                  type={showNewPassword ? "text" : "password"}
                  value={newPassword}
                  className={`${inputCls} font-mono tracking-wider pr-10`}
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword((v) => !v)}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-1 transition-colors cursor-pointer"
                  aria-label={showNewPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
                >
                  {showNewPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                </button>
              </div>
              <IconSquare title="Generar otra contraseña" onClick={regeneratePassword}>
                <RefreshCw className="w-4 h-4" />
              </IconSquare>
              <IconSquare title="Copiar contraseña" onClick={copyNewPassword} active={copiedNew}>
                {copiedNew ? <Check className="w-4 h-4 text-status-success" /> : <Copy className="w-4 h-4" />}
              </IconSquare>
            </div>
            <p className="mt-1.5 text-[11px] text-text-muted">
              Generada automáticamente. Cópiala y entrégala por un canal seguro antes de crear la cuenta.
            </p>
          </div>
          <button type="submit" className="hidden" />
        </form>
      </Dialog>

      {/* Editar rol */}
      <Dialog
        isOpen={!!editing}
        onClose={() => setEditing(null)}
        closeOnEsc={!confirm}
        title="Cambiar rol"
        subtitle="El nuevo rol aplica desde la siguiente petición del usuario"
        maxWidth="max-w-md"
        footer={
          <>
            <button type="button" className="btn-secondary" onClick={() => setEditing(null)}>
              Cancelar
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={() => editing && setConfirm({ kind: "role", target: editing })}
              disabled={!editRoleId || editRoleId === editing?.roleId}
            >
              Guardar cambio
            </button>
          </>
        }
      >
        {editing && (
          <div className="space-y-5">
            {editError && <ErrorBox message={editError} />}

            <div className="flex items-center gap-3 p-3 rounded-xl bg-bg-app border border-border-primary">
              <div className="w-10 h-10 rounded-full bg-bg-accent border border-border-strong/50 flex items-center justify-center font-mono font-bold text-text-primary text-xs shrink-0 uppercase">
                {(editing.fullName || editing.username).slice(0, 2)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-text-primary truncate">
                  {editing.fullName || `@${editing.username}`}
                </p>
                <p className="text-[11px] text-text-muted font-mono truncate">
                  {editing.fullName ? `@${editing.username}` : "Sin nombre registrado"}
                  {editing.email ? ` · ${editing.email}` : ""}
                </p>
              </div>
              {editing.role ? (
                <Badge variant={ROLE_LABELS[editing.role].variant} size="sm">
                  {ROLE_LABELS[editing.role].label}
                </Badge>
              ) : (
                <Badge variant="neutral" size="sm">Sin rol</Badge>
              )}
            </div>

            <div>
              <span className="label">Selecciona el nuevo rol</span>
              <RoleSelector
                roles={sortedRoles}
                value={editRoleId}
                onChange={setEditRoleId}
                currentId={editing.roleId}
              />
            </div>
          </div>
        )}
      </Dialog>

      {/* Contraseña temporal */}
      <Dialog
        isOpen={!!tempPassword}
        onClose={() => setTempPassword(null)}
        title="Contraseña temporal generada"
        subtitle={`Entréguela a @${tempPassword?.username ?? ""} por un canal seguro`}
        maxWidth="max-w-md"
        footer={
          <button type="button" className="btn-primary" onClick={() => setTempPassword(null)}>
            Entendido
          </button>
        }
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3 p-3 rounded-lg bg-bg-app border border-border-primary">
            <code className="font-mono text-sm text-text-primary tracking-wider select-all break-all">
              {tempPassword?.value}
            </code>
            <IconSquare title="Copiar contraseña" onClick={copyTempPassword} active={copied}>
              {copied ? <Check className="w-4 h-4 text-status-success" /> : <Copy className="w-4 h-4" />}
            </IconSquare>
          </div>
          <p className="text-[11px] text-text-muted">
            No se volverá a mostrar. Las sesiones activas del usuario fueron cerradas y deberá definir una
            contraseña nueva al ingresar.
          </p>
        </div>
      </Dialog>

      {/* Confirmación para cancelar / descartar creación de cuenta */}
      {showCancelCreateConfirm && (
        <ConfirmDialog
          icon={AlertTriangle}
          tone="warning"
          title="¿Descartar nueva cuenta?"
          description={
            newFullName.trim() || newEmail.trim() || newUsername.trim()
              ? "Hay información ingresada en el formulario que no se ha guardado. Si sales ahora, se perderán los datos."
              : "¿Estás seguro de que deseas salir del registro de la nueva cuenta?"
          }
          confirmLabel="Sí, descartar"
          cancelLabel="Continuar editando"
          onCancel={() => setShowCancelCreateConfirm(false)}
          onConfirm={confirmDiscardCreate}
        />
      )}

      {/* Confirmación antes de crear la cuenta definitivamente */}
      {showCreateConfirm && (
        <ConfirmDialog
          icon={UserPlus}
          tone="primary"
          title="¿Crear nueva cuenta de acceso?"
          description="Verifica los datos de la cuenta antes de registrarla en el sistema:"
          confirmLabel="Confirmar y crear"
          cancelLabel="Revisar datos"
          maxWidth="max-w-md"
          isLoading={isCreating}
          onCancel={() => !isCreating && setShowCreateConfirm(false)}
          onConfirm={executeCreateAccount}
        >
          <div className="space-y-3 text-left">
            <div className="flex items-center gap-3 p-3.5 rounded-xl bg-bg-app border border-border-primary">
              <div className="w-10 h-10 rounded-full bg-bg-accent border border-border-strong/50 flex items-center justify-center font-mono font-bold text-text-primary text-xs shrink-0 uppercase">
                {(newFullName || newUsername).slice(0, 2)}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-text-primary truncate">
                  {newFullName.trim()}
                </p>
                <p className="text-xs text-text-muted font-mono truncate">
                  @{newUsername.trim()} · {newEmail.trim()}
                </p>
              </div>
              {(() => {
                const r = sortedRoles.find((role) => role.id === newRoleId);
                const roleMeta = r?.name ? ROLE_LABELS[r.name] : null;
                return roleMeta ? (
                  <Badge variant={roleMeta.variant} size="sm">
                    {roleMeta.label}
                  </Badge>
                ) : (
                  <Badge variant="neutral" size="sm">Sin rol</Badge>
                );
              })()}
            </div>

            <div className="rounded-lg bg-bg-accent/40 border border-border-secondary px-3 py-2 text-[11px] text-text-secondary flex items-start gap-2">
              <KeyRound className="w-3.5 h-3.5 mt-0.5 text-text-muted shrink-0" />
              <span>
                Se asignará la contraseña generada y el usuario deberá actualizarla de forma obligatoria en su primer inicio de sesión.
              </span>
            </div>
          </div>
        </ConfirmDialog>
      )}

      {/* Confirmación de acciones */}
      {confirm && (
        <ConfirmDialog
          {...confirmView(confirm, sortedRoles, editRoleId)}
          onCancel={() => setConfirm(null)}
          onConfirm={executeConfirm}
        />
      )}
    </div>
  );
}

function SortTh({
  label,
  k,
  sortKey,
  sortDir,
  onSort,
  className = "px-4",
}: {
  label: string;
  k: SortKey;
  sortKey: SortKey;
  sortDir: SortDir;
  onSort: (k: SortKey) => void;
  className?: string;
}) {
  const active = sortKey === k;
  const Icon = !active ? ChevronsUpDown : sortDir === "asc" ? ChevronUp : ChevronDown;
  return (
    <th
      className={`py-3 ${className} font-bold`}
      aria-sort={active ? (sortDir === "asc" ? "ascending" : "descending") : "none"}
    >
      <button
        type="button"
        onClick={() => onSort(k)}
        className={`inline-flex items-center gap-1 uppercase tracking-wider cursor-pointer transition-colors hover:text-text-primary ${active ? "text-text-primary" : ""
          }`}
        title={k === "role" ? "Orden personalizado: Admin → Operador → Soporte" : `Ordenar por ${label.toLowerCase()}`}
      >
        {label}
        <Icon className={`w-3 h-3 ${active ? "text-primary-DEFAULT" : "opacity-60"}`} />
      </button>
    </th>
  );
}

function ActionBtn({
  children,
  title,
  onClick,
  disabled,
  tone = "default",
}: {
  children: React.ReactNode;
  title: string;
  onClick: () => void;
  disabled?: boolean;
  tone?: "default" | "success" | "warning";
}) {
  const tones = {
    default: "text-text-secondary hover:text-text-primary hover:bg-bg-accent/60",
    success: "text-status-success hover:bg-status-success-bg",
    warning: "text-status-warning hover:bg-status-warning-bg",
  };
  return (
    <button
      type="button"
      title={title}
      aria-label={title}
      disabled={disabled}
      onClick={onClick}
      className={`w-7 h-7 rounded-lg flex items-center justify-center transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${tones[tone]}`}
    >
      {children}
    </button>
  );
}

function PageBtn({
  children,
  active,
  disabled,
  onClick,
  ...rest
}: {
  children: React.ReactNode;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
} & React.AriaAttributes) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-current={active ? "page" : undefined}
      {...rest}
      className={`min-w-7 h-7 px-2 rounded-md text-xs font-medium flex items-center justify-center transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed ${active
        ? "bg-primary-DEFAULT text-white"
        : "text-text-secondary hover:bg-bg-accent/60 hover:text-text-primary"
        }`}
    >
      {children}
    </button>
  );
}

function IconSquare({
  children,
  title,
  onClick,
  active,
}: {
  children: React.ReactNode;
  title: string;
  onClick: () => void;
  active?: boolean;
}) {
  return (
    <button
      type="button"
      title={title}
      aria-label={title}
      onClick={onClick}
      className={`w-9.5 h-9.5 shrink-0 rounded-lg border flex items-center justify-center transition-colors cursor-pointer ${active
        ? "border-status-success-border bg-status-success-bg"
        : "border-border-primary bg-bg-app text-text-secondary hover:text-text-primary hover:border-border-strong"
        }`}
    >
      {children}
    </button>
  );
}

function RoleSelector({
  roles,
  value,
  onChange,
  currentId,
}: {
  roles: Role[];
  value: string;
  onChange: (id: string) => void;
  /** Rol vigente del usuario (se marca con la etiqueta «Actual»). */
  currentId?: string | null;
}) {
  return (
    <div className="flex flex-col gap-2" role="radiogroup">
      {roles.map((r) => {
        const active = value === r.id;
        const meta = ROLE_META[r.name];
        const Icon = meta?.icon ?? UserCog;
        return (
          <button
            key={r.id}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(r.id)}
            className={`group flex items-center gap-3 p-3 rounded-xl border text-left transition-all cursor-pointer outline-none focus-visible:ring-3 focus-visible:ring-primary-muted ${active
              ? "border-primary-DEFAULT bg-primary-muted"
              : "border-border-primary bg-bg-app hover:border-border-strong hover:bg-bg-accent/30"
              }`}
          >
            <span
              className={`w-9 h-9 rounded-lg border flex items-center justify-center shrink-0 transition-colors ${active
                ? "border-primary-DEFAULT/40 bg-bg-app text-primary-DEFAULT"
                : "border-border-primary bg-bg-card text-text-secondary group-hover:text-text-primary"
                }`}
            >
              <Icon className="w-4 h-4" />
            </span>
            <span className="min-w-0 flex-1">
              <span className="flex items-center gap-2">
                <span className="text-[13px] font-semibold text-text-primary">
                  {ROLE_LABELS[r.name]?.label ?? r.name}
                </span>
                {currentId === r.id && (
                  <span className="text-[10px] px-1.5 py-px rounded-full border border-border-strong text-text-muted">
                    Actual
                  </span>
                )}
              </span>
              {meta && (
                <span className="block text-[11px] leading-snug text-text-muted mt-0.5">
                  {meta.description}
                </span>
              )}
            </span>
            <span
              className={`w-4.5 h-4.5 rounded-full border flex items-center justify-center shrink-0 transition-colors ${active ? "border-primary-DEFAULT bg-primary-DEFAULT text-white" : "border-border-strong"
                }`}
              aria-hidden
            >
              {active && <Check className="w-3 h-3" />}
            </span>
          </button>
        );
      })}
    </div>
  );
}

function CustomSelect<T extends string | number>({
  value,
  options,
  onChange,
  ariaLabel,
  className = "",
  dropUp = false,
  compact = false,
  leftIcon,
  labelPrefix,
  align = "left",
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (value: T) => void;
  ariaLabel: string;
  className?: string;
  dropUp?: boolean;
  compact?: boolean;
  leftIcon?: React.ReactNode;
  labelPrefix?: string;
  align?: "left" | "right";
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const selected = options.find((o) => o.value === value);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!ref.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={ref} className={`relative ${className}`}>
      <button
        type="button"
        aria-label={ariaLabel}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        className={
          `w-full flex items-center justify-between gap-2 rounded-lg 
          bg-bg-app border text-text-secondary outline-none transition-all cursor-pointer 
          hover:border-border-strong focus-visible:ring-3 focus-visible:ring-primary-muted 
          ${compact ? "px-2.5 py-1 text-xs" : "px-3 py-2 text-xs"} 
          ${open ? "border-primary-DEFAULT ring-3 ring-primary-muted" : "border-border-primary"}`
        }
      >
        <div className="flex items-center gap-2 truncate">
          {leftIcon}
          <span className="truncate">
            {labelPrefix ? `${labelPrefix}${selected?.label ?? ""}` : selected?.label}
          </span>
        </div>
        <ChevronDown
          className={`w-3.5 h-3.5 shrink-0 text-text-muted transition-transform ${open ? "rotate-180" : ""}`}
        />
      </button>

      {open && (
        <ul
          role="listbox"
          aria-label={ariaLabel}
          className={`absolute z-40 ${align === "right" ? "right-0" : "left-0"
            } min-w-full max-h-64 overflow-y-auto p-1.5 rounded-xl bg-bg-surface-elevated border border-border-primary shadow-2xl shadow-black/50 animate-in fade-in zoom-in-95 duration-100 ${dropUp ? "bottom-full mb-1.5 origin-bottom" : "top-full mt-1.5 origin-top"
            }`}
        >
          {options.map((o) => {
            const active = o.value === value;
            return (
              <li key={String(o.value)} role="option" aria-selected={active}>
                <button
                  type="button"
                  onClick={() => {
                    onChange(o.value);
                    setOpen(false);
                  }}
                  className={`w-full flex items-center justify-between gap-3 px-2.5 py-1.5 rounded-lg text-xs text-left whitespace-nowrap transition-colors cursor-pointer ${active
                    ? "bg-primary-muted text-text-primary font-medium"
                    : "text-text-secondary hover:bg-bg-accent/60 hover:text-text-primary"
                    }`}
                >
                  <span>{o.label}</span>
                  {active && <Check className="w-3.5 h-3.5 text-primary-DEFAULT shrink-0" />}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

/** Contenido del diálogo de confirmación según la acción pendiente. */
function confirmView(
  state: NonNullable<ConfirmState>,
  roles: Role[],
  newRoleId: string
): Omit<React.ComponentProps<typeof ConfirmDialog>, "onConfirm" | "onCancel"> {
  const t = state.target;
  const who = <strong className="text-text-primary">@{t.username}</strong>;

  switch (state.kind) {
    case "toggle":
      return t.isActive
        ? {
          icon: Power,
          tone: "warning",
          title: "¿Desactivar cuenta?",
          confirmLabel: "Desactivar",
          description: <>La cuenta {who} no podrá iniciar sesión y sus sesiones activas dejarán de funcionar. Podrás reactivarla cuando quieras.</>,
        }
        : {
          icon: Power,
          tone: "primary",
          title: "¿Reactivar cuenta?",
          confirmLabel: "Reactivar",
          description: <>La cuenta {who} volverá a tener acceso al sistema con su contraseña actual.</>,
        };
    case "reset":
      return {
        icon: KeyRound,
        tone: "warning",
        title: "¿Generar nueva contraseña?",
        confirmLabel: "Generar contraseña",
        description: <>Se creará una contraseña temporal para {who}. Se cerrarán sus sesiones activas y deberá cambiarla en su próximo ingreso. Se mostrará una sola vez.</>,
      };
    case "unlock":
      return {
        icon: Unlock,
        tone: "primary",
        title: "¿Desbloquear cuenta?",
        confirmLabel: "Desbloquear",
        description: <>{who} podrá volver a intentar iniciar sesión de inmediato.</>,
      };
    case "role": {
      const next = roles.find((r) => r.id === newRoleId);
      const from = t.role ? ROLE_LABELS[t.role].label : "Sin rol";
      const to = next ? ROLE_LABELS[next.name]?.label ?? next.name : "—";
      return {
        icon: UserCog,
        tone: "primary",
        title: "¿Confirmar cambio de rol?",
        confirmLabel: "Cambiar rol",
        description: <>Se modificarán los permisos de {who}. El cambio aplica desde su siguiente petición.</>,
        children: (
          <div className="flex items-center justify-center gap-3 p-3 rounded-lg bg-bg-app border border-border-primary text-xs">
            <span className="text-text-muted">{from}</span>
            <ArrowRight className="w-3.5 h-3.5 text-text-muted" />
            <span className="font-semibold text-text-primary">{to}</span>
          </div>
        ),
      };
    }
  }
}

function ConfirmDialog({
  icon: Icon,
  tone,
  title,
  description,
  confirmLabel,
  cancelLabel = "Cancelar",
  maxWidth = "max-w-sm",
  isLoading = false,
  disabled = false,
  children,
  onConfirm,
  onCancel,
}: {
  icon: LucideIcon;
  tone: "primary" | "warning" | "danger";
  title: string;
  description: React.ReactNode;
  confirmLabel: string;
  cancelLabel?: string;
  maxWidth?: string;
  isLoading?: boolean;
  disabled?: boolean;
  children?: React.ReactNode;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isLoading) onCancel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onCancel, isLoading]);

  const tones = {
    primary: "bg-primary-muted text-primary-DEFAULT border-primary-DEFAULT/30",
    warning: "bg-status-warning-bg text-status-warning border-status-warning-border",
    danger: "bg-status-error-bg text-status-error border-status-error-border",
  };

  return (
    <div
      className="fixed inset-0 z-60 flex items-center justify-center p-3 sm:p-6 bg-black/70 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={() => {
        if (!isLoading) onCancel();
      }}
    >
      <div
        className={`card w-full ${maxWidth} overflow-hidden animate-in zoom-in-95 duration-150`}
        onClick={(e) => e.stopPropagation()}
        role="alertdialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="px-6 pt-6 pb-5 text-center space-y-3">
          <div className={`mx-auto w-11 h-11 rounded-full border flex items-center justify-center ${tones[tone]}`}>
            <Icon className="w-5 h-5" />
          </div>
          <h2 className="text-base font-bold font-special text-text-primary">{title}</h2>
          <p className="text-[13px] leading-relaxed text-text-muted">{description}</p>
          {children}
        </div>
        <div className="px-6 py-4 border-t border-border-secondary flex items-center justify-end gap-2">
          <button type="button" className="btn-secondary" onClick={onCancel} disabled={isLoading}>
            {cancelLabel}
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={onConfirm}
            disabled={disabled || isLoading}
            autoFocus
          >
            {isLoading ? (
              <span className="flex items-center gap-1.5">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Procesando...
              </span>
            ) : (
              confirmLabel
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function Dialog({
  isOpen,
  onClose,
  title,
  subtitle,
  children,
  footer,
  maxWidth = "max-w-lg",
  closeOnEsc = true,
}: {
  isOpen: boolean;
  onClose: () => void;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
  footer?: React.ReactNode;
  maxWidth?: string;
  /** Se desactiva mientras otro diálogo (p. ej. una confirmación) está encima. */
  closeOnEsc?: boolean;
}) {
  useEffect(() => {
    if (!isOpen || !closeOnEsc) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [isOpen, closeOnEsc, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/65 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className={`card w-full ${maxWidth} max-h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-150`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="card-header items-start shrink-0 border-b border-border-secondary">
          <div>
            <h2 className="text-base sm:text-lg font-bold font-special text-text-primary">{title}</h2>
            {subtitle && <p className="text-xs sm:text-[13px] text-text-muted mt-0.5">{subtitle}</p>}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-5 h-5 mt-0.5 rounded-full bg-[#2f2f2f] hover:bg-[#3d3d3d] text-neutral-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer shrink-0"
            aria-label="Cerrar modal"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-y-auto px-6 py-5">{children}</div>

        {footer && (
          <div className="px-6 py-4 border-t border-border-secondary flex items-center justify-end gap-2 shrink-0">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

function ErrorBox({ message }: { message: string }) {
  return (
    <div className="p-3 rounded-lg bg-status-error-bg border border-status-error-border text-status-error text-xs flex items-center gap-2">
      <AlertTriangle className="w-4 h-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
