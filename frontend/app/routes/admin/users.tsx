import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Users,
  UserPlus,
  AlertTriangle,
  Search,
  KeyRound,
  Lock,
  Unlock,
  RefreshCw,
  Copy,
  Check,
} from "lucide-react";
import { userService } from "../../services/userService";
import { ApiError } from "../../services/api";
import type { Role, User, UserRole } from "../../types/auth";
import { Card, CardHeader } from "../../components/ui/Card";
import { Button } from "../../components/ui/Button";
import { Badge } from "../../components/ui/Badge";
import { Modal } from "../../components/ui/Modal";
import { Input, Select } from "../../components/ui/Input";
import { useToast } from "../../context/ToastContext";
import { useAuth } from "../../context/AuthContext";

const ROLE_LABELS: Record<UserRole, { label: string; variant: "purple" | "primary" | "cyan" }> = {
  admin: { label: "Administrador", variant: "purple" },
  operator: { label: "Operador de Patio", variant: "primary" },
  support: { label: "Soporte Técnico", variant: "cyan" },
};

const errorMessage = (err: unknown) =>
  err instanceof ApiError ? err.message : "No se pudo conectar con el servidor.";

const isLocked = (u: User) => !!u.lockedUntil && new Date(u.lockedUntil) > new Date();

const formatDate = (iso: string | null, withTime = false) =>
  iso
    ? new Date(iso).toLocaleString("es-CO", {
        day: "2-digit",
        month: "short",
        year: withTime ? undefined : "numeric",
        ...(withTime ? { hour: "2-digit", minute: "2-digit" } : {}),
      })
    : "Sin accesos";

export default function AdminUsers() {
  const { user: currentAdmin } = useAuth();
  const { toast } = useToast();

  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [busyId, setBusyId] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState<"todos" | UserRole>("todos");

  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRoleId, setNewRoleId] = useState("");
  const [createError, setCreateError] = useState("");
  const [isCreating, setIsCreating] = useState(false);

  const [editing, setEditing] = useState<User | null>(null);
  const [editRoleId, setEditRoleId] = useState("");
  const [editError, setEditError] = useState("");

  const [tempPassword, setTempPassword] = useState<{ username: string; value: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setLoadError("");
    try {
      const [{ users }, roles] = await Promise.all([userService.list(), userService.listRoles()]);
      setUsers(users);
      setRoles(roles);
    } catch (err) {
      setLoadError(errorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const roleOptions = useMemo(
    () => roles.map((r) => ({ value: r.id, label: ROLE_LABELS[r.name]?.label ?? r.name })),
    [roles]
  );

  const replaceUser = (updated: User) =>
    setUsers((prev) => prev.map((u) => (u.id === updated.id ? updated : u)));

  const filteredUsers = users.filter(
    (u) =>
      u.username.toLowerCase().includes(searchTerm.toLowerCase()) &&
      (roleFilter === "todos" || u.role === roleFilter)
  );

  const openCreate = () => {
    setNewUsername("");
    setNewPassword("");
    setNewRoleId(roles.find((r) => r.name === "operator")?.id ?? roles[0]?.id ?? "");
    setCreateError("");
    setIsCreateOpen(true);
  };

  const handleCreate = async (e?: React.FormEvent) => {
    e?.preventDefault();
    setCreateError("");

    const username = newUsername.trim();
    if (username.length < 3 || username.length > 20) {
      return setCreateError("El nombre de usuario debe tener entre 3 y 20 caracteres.");
    }
    if (newPassword.length < 8 || newPassword.length > 40) {
      return setCreateError("La contraseña debe tener entre 8 y 40 caracteres.");
    }
    if (!newRoleId) return setCreateError("Seleccione un rol.");

    setIsCreating(true);
    try {
      const created = await userService.create({ username, password: newPassword, roleId: newRoleId });
      setUsers((prev) => [...prev, created]);
      setIsCreateOpen(false);
      toast(
        `@${created.username} deberá cambiar la contraseña en su primer ingreso`,
        "success",
        "Cuenta creada"
      );
    } catch (err) {
      setCreateError(errorMessage(err));
    } finally {
      setIsCreating(false);
    }
  };

  const handleUpdateRole = async () => {
    if (!editing) return;
    setEditError("");
    try {
      const updated = await userService.update(editing.id, { roleId: editRoleId });
      replaceUser(updated);
      setEditing(null);
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

  const handleToggleStatus = (target: User) =>
    runAction(target, async () => {
      const updated = await userService.update(target.id, { isActive: !target.isActive });
      replaceUser(updated);
      toast(
        `Cuenta @${updated.username} ${updated.isActive ? "reactivada" : "desactivada"}`,
        updated.isActive ? "success" : "warning"
      );
    });

  const handleResetPassword = (target: User) =>
    runAction(target, async () => {
      const value = await userService.resetPassword(target.id);
      replaceUser({ ...target, mustChangePassword: true, lockedUntil: null });
      setCopied(false);
      setTempPassword({ username: target.username, value });
    });

  const handleUnlock = (target: User) =>
    runAction(target, async () => {
      await userService.unlock(target.id);
      replaceUser({ ...target, lockedUntil: null });
      toast(`Cuenta @${target.username} desbloqueada`, "success");
    });

  const copyTempPassword = async () => {
    if (!tempPassword) return;
    await navigator.clipboard.writeText(tempPassword.value);
    setCopied(true);
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border-secondary">
        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={loadData}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? "animate-spin" : ""}`} />}
          >
            Actualizar
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={openCreate}
            disabled={roles.length === 0}
            leftIcon={<UserPlus className="w-4 h-4" />}
          >
            Nueva cuenta
          </Button>
        </div>
      </div>

      <Card>
        <CardHeader
          title={
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-text-primary" />
              <span>Directorio de cuentas</span>
            </div>
          }
          subtitle={`${users.length} cuentas registradas`}
          action={
            <div className="flex flex-col sm:flex-row items-center gap-2">
              <div className="relative w-full sm:w-60">
                <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  placeholder="Buscar por usuario..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-bg-app border border-border-primary text-xs text-text-primary placeholder:text-text-disabled outline-none focus:border-border-strong font-mono"
                />
              </div>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value as "todos" | UserRole)}
                className="bg-bg-app border border-border-primary text-xs text-text-primary rounded-lg px-3 py-1.5 outline-none cursor-pointer"
              >
                <option value="todos">Todos los roles</option>
                <option value="admin">Administradores</option>
                <option value="operator">Operadores de patio</option>
                <option value="support">Soporte técnico</option>
              </select>
            </div>
          }
        />

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-text-muted uppercase tracking-wider text-[10px] border-b border-border-secondary">
              <tr>
                <th className="py-3 px-5">Usuario</th>
                <th className="py-3 px-4">Rol</th>
                <th className="py-3 px-4">Estado</th>
                <th className="py-3 px-4">Último acceso</th>
                <th className="py-3 px-4">Alta</th>
                <th className="py-3 px-5 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-secondary">
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-text-muted font-mono">
                    Cargando cuentas...
                  </td>
                </tr>
              ) : loadError ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center">
                    <div className="inline-flex items-center gap-2 text-status-error">
                      <AlertTriangle className="w-4 h-4" />
                      <span>{loadError}</span>
                    </div>
                  </td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-text-muted">
                    No hay cuentas que coincidan con los filtros.
                  </td>
                </tr>
              ) : (
                filteredUsers.map((u) => {
                  const isSelf = u.id === currentAdmin?.id;
                  const locked = isLocked(u);
                  const busy = busyId === u.id;
                  const role = u.role ? ROLE_LABELS[u.role] : null;

                  return (
                    <tr key={u.id} className="hover:bg-bg-app/50 transition-colors">
                      <td className="py-3 px-5">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-lg bg-bg-app border border-border-primary flex items-center justify-center font-mono font-bold text-text-primary text-xs shrink-0 uppercase">
                            {u.username.slice(0, 2)}
                          </div>
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span className="font-semibold text-text-primary font-mono">@{u.username}</span>
                              {isSelf && <span className="text-[10px] text-text-muted">(tú)</span>}
                            </div>
                            {u.mustChangePassword && (
                              <p className="text-[10px] text-status-warning mt-0.5">
                                Cambio de contraseña pendiente
                              </p>
                            )}
                          </div>
                        </div>
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
                        {/* El backend también rechaza estas acciones sobre la propia cuenta */}
                        {isSelf ? (
                          <p className="text-right text-[11px] text-text-muted">—</p>
                        ) : (
                          <div className="flex items-center justify-end gap-1.5">
                            {locked && (
                              <Button variant="ghost" size="sm" disabled={busy} onClick={() => handleUnlock(u)}
                                leftIcon={<Unlock className="w-3.5 h-3.5" />}>
                                Desbloquear
                              </Button>
                            )}
                            <Button
                              variant="ghost"
                              size="sm"
                              disabled={busy}
                              onClick={() => {
                                setEditing(u);
                                setEditRoleId(u.roleId ?? "");
                                setEditError("");
                              }}
                            >
                              Rol
                            </Button>
                            <Button variant="ghost" size="sm" disabled={busy} onClick={() => handleResetPassword(u)}
                              leftIcon={<KeyRound className="w-3.5 h-3.5" />}>
                              Restablecer
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              disabled={busy}
                              className={u.isActive ? "text-status-warning" : "text-status-success"}
                              onClick={() => handleToggleStatus(u)}
                            >
                              {u.isActive ? "Desactivar" : "Reactivar"}
                            </Button>
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
      </Card>

      {/* Crear cuenta */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Nueva cuenta de acceso"
        subtitle="El usuario deberá cambiar la contraseña en su primer inicio de sesión"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setIsCreateOpen(false)}>
              Cancelar
            </Button>
            <Button variant="primary" size="sm" onClick={() => handleCreate()} isLoading={isCreating}>
              Crear cuenta
            </Button>
          </>
        }
      >
        <form onSubmit={handleCreate} className="space-y-4">
          {createError && <ErrorBox message={createError} />}
          <Input
            label="Nombre de usuario"
            placeholder="ej: mario.gomez"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            helperText="Entre 3 y 20 caracteres, único en el sistema"
            required
          />
          <Select
            label="Rol"
            value={newRoleId}
            onChange={(e) => setNewRoleId(e.target.value)}
            options={roleOptions}
          />
          <Input
            label="Contraseña inicial"
            type="password"
            placeholder="Mínimo 8 caracteres"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            helperText="Entre 8 y 40 caracteres"
            required
          />
          <button type="submit" className="hidden" />
        </form>
      </Modal>

      {/* Editar rol */}
      <Modal
        isOpen={!!editing}
        onClose={() => setEditing(null)}
        title={`Cambiar rol: @${editing?.username ?? ""}`}
        subtitle="El nuevo rol aplica desde la siguiente petición del usuario"
        footer={
          <>
            <Button variant="outline" size="sm" onClick={() => setEditing(null)}>
              Cancelar
            </Button>
            <Button variant="primary" size="sm" onClick={handleUpdateRole} disabled={editRoleId === editing?.roleId}>
              Guardar
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {editError && <ErrorBox message={editError} />}
          <Select
            label="Rol asignado"
            value={editRoleId}
            onChange={(e) => setEditRoleId(e.target.value)}
            options={roleOptions}
          />
        </div>
      </Modal>

      {/* Contraseña temporal */}
      <Modal
        isOpen={!!tempPassword}
        onClose={() => setTempPassword(null)}
        title="Contraseña temporal generada"
        subtitle={`Entréguela a @${tempPassword?.username ?? ""} por un canal seguro`}
        footer={
          <Button variant="primary" size="sm" onClick={() => setTempPassword(null)}>
            Entendido
          </Button>
        }
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-3 p-3 rounded-lg bg-bg-app border border-border-primary">
            <code className="font-mono text-sm text-text-primary tracking-wider select-all">{tempPassword?.value}</code>
            <Button variant="ghost" size="sm" onClick={copyTempPassword}
              leftIcon={copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}>
              {copied ? "Copiada" : "Copiar"}
            </Button>
          </div>
          <p className="text-[11px] text-text-muted">
            No se volverá a mostrar. Las sesiones activas del usuario fueron cerradas y deberá definir una
            contraseña nueva al ingresar.
          </p>
        </div>
      </Modal>
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
