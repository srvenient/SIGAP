import React, { useState, useEffect } from "react";
import {
  X,
  User,
  Key,
  Shield,
  Laptop,
  Smartphone,
  Copy,
  Check,
  HelpCircle,
  Eye,
  EyeOff,
  Building2,
  Lock,
  AlertTriangle,
  LogOut,
  Loader2,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { authService } from "../../services/authService";
import avatar1 from "../../assets/webp/avatar1.webp";

export interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface SessionDevice {
  id: string;
  name: string;
  type: "windows" | "mobile" | "terminal";
  isCurrent: boolean;
  lastActive: string;
  location: string;
}

export function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  const { user, role, logout } = useAuth();
  const { toast } = useToast();

  const isEnforced = Boolean(user?.mustChangePassword);

  // Estados de formularios y acciones
  const [showPasswordForm, setShowPasswordForm] = useState(isEnforced);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [isSavingPass, setIsSavingPass] = useState(false);

  // Si mustChangePassword es true, abrir automáticamente el formulario
  useEffect(() => {
    if (user?.mustChangePassword) {
      setShowPasswordForm(true);
    }
  }, [user?.mustChangePassword]);

  // Permiso de acceso para soporte técnico (informativo)
  const [supportAccessEnabled, setSupportAccessEnabled] = useState(false);

  // Lista de dispositivos conectados (informativa)
  const [devices, setDevices] = useState<SessionDevice[]>([
    {
      id: "dev-1",
      name: "Windows Device",
      type: "windows",
      isCurrent: true,
      lastActive: "Ahora",
      location: "CO-CUN, Colombia",
    },
    {
      id: "dev-2",
      name: "Windows Device (Terminal Operativa)",
      type: "windows",
      isCurrent: false,
      lastActive: "13 feb 2026, 22:08",
      location: "CO-DC, Colombia",
    },
    {
      id: "dev-3",
      name: "Dispositivo móvil / SIGAP App",
      type: "mobile",
      isCurrent: false,
      lastActive: "20 ene 2026, 19:14",
      location: "CO-DC, Colombia",
    },
  ]);

  // ID de usuario y estado copiado
  const userId = `usr_${user?.id || "8e377fc8-885a-4b90-8efb-99170b385ddb"}`;
  const [hasCopiedId, setHasCopiedId] = useState(false);

  // Cerrar con Escape solo si NO es cambio obligatorio
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isEnforced) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, isEnforced]);

  if (!isOpen) return null;

  const getRoleDisplayName = (r: string | null) => {
    switch (r?.toLowerCase()) {
      case "admin":
        return "Administrador General";
      case "operator":
        return "Operador de Patio";
      case "support":
        return "Soporte Técnico Especializado";
      default:
        return "Usuario del Sistema";
    }
  };

  const handleCopyUserId = async () => {
    try {
      await navigator.clipboard.writeText(userId);
      setHasCopiedId(true);
      toast("ID de usuario copiado al portapapeles", "info");
      setTimeout(() => setHasCopiedId(false), 2000);
    } catch {
      toast("No se pudo copiar el ID", "error");
    }
  };

  const handleToggleSupportAccess = () => {
    const next = !supportAccessEnabled;
    setSupportAccessEnabled(next);
    toast(
      next
        ? "Permiso temporal de soporte técnico habilitado"
        : "Permiso de soporte técnico revocado",
      "info"
    );
  };

  // Cambio de contraseña 100% funcional conectado al backend
  const handleSavePassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!currentPassword) {
      toast("Ingresa tu contraseña actual", "error", "Campo requerido");
      return;
    }
    if (newPassword.length < 8) {
      toast("La nueva contraseña debe tener al menos 8 caracteres", "error", "Requisito de seguridad");
      return;
    }
    if (newPassword === currentPassword) {
      toast("La nueva contraseña debe ser diferente a la actual", "error", "Contraseña idéntica");
      return;
    }
    if (newPassword !== confirmPassword) {
      toast("Las contraseñas no coinciden", "error", "Validación");
      return;
    }

    setIsSavingPass(true);
    try {
      const res = await authService.changePassword(currentPassword, newPassword);
      if (res.success) {
        toast("¡Contraseña actualizada exitosamente! Entorno operacional activo.", "success", "Seguridad");
        setCurrentPassword("");
        setNewPassword("");
        setConfirmPassword("");
        setShowPasswordForm(false);
        onClose();
      } else {
        toast(res.error || "No se pudo actualizar la contraseña", "error", "Error de servidor");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al procesar la solicitud";
      toast(msg, "error");
    } finally {
      setIsSavingPass(false);
    }
  };

  const handleTerminateSession = (deviceId: string) => {
    setDevices((prev) => prev.filter((d) => d.id !== deviceId));
    toast("Sesión del dispositivo finalizada con éxito", "success");
  };

  const handleTerminateAllOtherSessions = () => {
    setDevices((prev) => prev.filter((d) => d.isCurrent));
    toast("Se cerraron todas las demás sesiones activas", "success");
  };

  const handleLogoutFromModal = async () => {
    await logout();
    window.location.href = "/";
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/65 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={() => {
        if (!isEnforced) onClose();
      }}
    >
      <div
        className="bg-[#202020] border border-[#333333] rounded-2xl w-full max-w-2xl max-h-[90vh] shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150 text-text-primary"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Encabezado del modal */}
        <div className="flex items-center justify-between px-6 py-4.5 border-b border-[#2d2d2d] shrink-0">
          <div>
            <h2 className="text-base sm:text-lg font-bold font-special text-[#f5f5f5]">
              {isEnforced ? "Actualización de Seguridad Requerida" : "Configuración de la cuenta"}
            </h2>
            <p className="text-xs text-text-muted mt-0.5">
              {isEnforced
                ? "Debes establecer una nueva contraseña personal para continuar."
                : "Administra tus credenciales, permisos y sesiones en SIGAP."}
            </p>
          </div>

          {/* Si es cambio obligatorio, se muestra botón para cerrar sesión en lugar de cerrar el modal */}
          {isEnforced ? (
            <button
              type="button"
              onClick={handleLogoutFromModal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-status-error hover:bg-status-error-bg/20 transition-colors cursor-pointer"
              title="Salir de la sesión"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Cerrar sesión</span>
            </button>
          ) : (
            <button
              type="button"
              onClick={onClose}
              className="p-1.5 rounded-lg text-text-muted hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
              aria-label="Cerrar modal"
            >
              <X className="w-4.5 h-4.5" />
            </button>
          )}
        </div>

        {/* Banner de cambio obligatorio si aplica */}
        {isEnforced && (
          <div className="mx-6 mt-4 p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-start gap-3 text-amber-200 shrink-0">
            <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
            <div className="text-xs">
              <p className="font-semibold text-amber-300">Cambio de contraseña obligatorio</p>
              <p className="opacity-90 mt-0.5 leading-relaxed">
                Por políticas de seguridad del sistema SIGAP (primer acceso o contraseña restablecida),
                es obligatorio configurar una nueva contraseña personal para desbloquear el acceso operacional.
              </p>
            </div>
          </div>
        )}

        {/* Cuerpo desplazable */}
        <div className="overflow-y-auto p-6 space-y-7 divide-y divide-[#2d2d2d]">
          {/* 1. Datos Generales de la Cuenta */}
          <div className="flex items-center gap-4">
            <div className="relative w-14 h-14 rounded-2xl bg-bg-app border border-border-primary flex items-center justify-center shrink-0 shadow-md">
              <img
                src={avatar1}
                alt="Avatar"
                className="w-full h-full rounded-2xl object-cover"
              />
              <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-status-success ring-2 ring-[#202020]" />
            </div>

            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2">
                <h3 className="text-sm sm:text-base font-semibold text-white truncate">
                  {user?.username || "Administrador"}
                </h3>
                <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-primary-muted text-primary-DEFAULT border border-primary-DEFAULT/30">
                  {getRoleDisplayName(role)}
                </span>
              </div>
              <p className="text-xs text-text-muted mt-0.5 font-mono">
                {user ? `${user.username.toLowerCase()}@sigap.co` : "admin@sigap.co"}
              </p>
            </div>
          </div>

          {/* 2. Sección Contraseña (100% Funcional con Backend) */}
          <div className="pt-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                  <span>Contraseña</span>
                  {isEnforced && (
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40">
                      Requerido
                    </span>
                  )}
                </h4>
                <p className="text-xs text-text-muted mt-0.5">
                  Establece una contraseña segura (mínimo 8 caracteres) para tu cuenta.
                </p>
              </div>

              {!showPasswordForm && !isEnforced && (
                <button
                  type="button"
                  onClick={() => setShowPasswordForm(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-xs font-medium text-white transition-colors cursor-pointer shrink-0 border border-white/10"
                >
                  Cambiar contraseña
                </button>
              )}
            </div>

            {/* Formulario para cambiar contraseña */}
            {showPasswordForm && (
              <form
                onSubmit={handleSavePassword}
                className="mt-4 p-4 rounded-xl bg-bg-app border border-border-secondary space-y-3 animate-in fade-in duration-150"
              >
                <div>
                  <label className="block text-[11px] font-medium text-text-muted mb-1">
                    Contraseña actual {isEnforced && "(o contraseña temporal inicial)"}
                  </label>
                  <input
                    type={showPass ? "text" : "password"}
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Ingresa tu contraseña actual"
                    required
                    className="w-full px-3 py-1.5 text-xs rounded-lg bg-bg-surface border border-border-primary text-white outline-none focus:border-primary-DEFAULT"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[11px] font-medium text-text-muted mb-1">
                      Nueva contraseña (mínimo 8 caracteres)
                    </label>
                    <input
                      type={showPass ? "text" : "password"}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Mínimo 8 caracteres"
                      required
                      minLength={8}
                      className="w-full px-3 py-1.5 text-xs rounded-lg bg-bg-surface border border-border-primary text-white outline-none focus:border-primary-DEFAULT"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-medium text-text-muted mb-1">
                      Confirmar nueva contraseña
                    </label>
                    <input
                      type={showPass ? "text" : "password"}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Repetir nueva contraseña"
                      required
                      minLength={8}
                      className="w-full px-3 py-1.5 text-xs rounded-lg bg-bg-surface border border-border-primary text-white outline-none focus:border-primary-DEFAULT"
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-1">
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="flex items-center gap-1.5 text-[11px] text-text-muted hover:text-white transition-colors cursor-pointer"
                  >
                    {showPass ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    <span>{showPass ? "Ocultar" : "Mostrar"} contraseñas</span>
                  </button>

                  <div className="flex items-center gap-2">
                    {!isEnforced && (
                      <button
                        type="button"
                        onClick={() => setShowPasswordForm(false)}
                        className="px-3 py-1.5 rounded-lg text-xs font-medium text-text-muted hover:text-white transition-colors cursor-pointer"
                      >
                        Cancelar
                      </button>
                    )}
                    <button
                      type="submit"
                      disabled={isSavingPass}
                      className="flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-primary-DEFAULT hover:bg-primary-hover text-white text-xs font-medium transition-colors cursor-pointer disabled:opacity-50"
                    >
                      {isSavingPass && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                      <span>{isSavingPass ? "Guardando..." : "Actualizar contraseña"}</span>
                    </button>
                  </div>
                </div>
              </form>
            )}
          </div>

          {/* 3. Sección Soporte */}
          <div className="pt-6 space-y-4">
            <h4 className="text-sm font-semibold text-white">Soporte</h4>

            {/* Permiso de acceso para soporte técnico */}
            <div className="flex items-center justify-between gap-4">
              <div className="max-w-md">
                <p className="text-xs font-medium text-white">
                  Permiso de acceso para soporte técnico
                </p>
                <p className="text-[11px] text-text-muted mt-0.5 leading-relaxed">
                  Otorga al equipo de soporte de SIGAP acceso temporal a tu cuenta para ayudar a
                  resolver problemas o recuperar contenido. Puedes revocar el acceso en cualquier
                  momento.
                </p>
              </div>

              {/* Toggle Switch */}
              <button
                type="button"
                onClick={handleToggleSupportAccess}
                className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                  supportAccessEnabled ? "bg-primary-DEFAULT" : "bg-[#383838]"
                }`}
                aria-label="Toggle permiso soporte"
              >
                <span
                  className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                    supportAccessEnabled ? "translate-x-4" : "translate-x-0"
                  }`}
                />
              </button>
            </div>

            {/* Eliminar mi cuenta */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2">
              <div>
                <p className="text-xs font-medium text-white">Eliminar mi cuenta</p>
                <p className="text-[11px] text-text-muted mt-0.5">
                  Elimina tu cuenta de forma permanente. Ya no podrás acceder a tus registros ni a
                  los espacios de trabajo de SIGAP.
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  toast(
                    "Esta acción requiere aprobación del Administrador General del sistema.",
                    "warning",
                    "Operación restringida"
                  )
                }
                className="px-3 py-1.5 rounded-lg bg-[#3a2222] hover:bg-[#482828] border border-[#522b2b] text-[#e05244] text-xs font-medium transition-colors cursor-pointer shrink-0"
              >
                Eliminar mi cuenta
              </button>
            </div>
          </div>

          {/* 4. Sección Dispositivos */}
          <div className="pt-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <div className="flex items-center gap-1.5">
                  <h4 className="text-sm font-semibold text-white">Dispositivos</h4>
                  <HelpCircle className="w-3.5 h-3.5 text-text-muted" />
                </div>
                <p className="text-xs font-medium text-white mt-2">
                  Cerrar sesión en todos los dispositivos
                </p>
                <p className="text-[11px] text-text-muted mt-0.5">
                  Cierra las sesiones activas en todos tus dispositivos, excepto en este.
                </p>
              </div>

              {devices.length > 1 && (
                <button
                  type="button"
                  onClick={handleTerminateAllOtherSessions}
                  className="px-3 py-1.5 rounded-lg bg-[#3a2222] hover:bg-[#482828] border border-[#522b2b] text-[#e05244] text-xs font-medium transition-colors cursor-pointer shrink-0"
                >
                  Cerrar sesión en todos los dispositivos
                </button>
              )}
            </div>

            {/* Tabla de dispositivos */}
            <div className="mt-2 border border-[#2d2d2d] rounded-xl overflow-hidden bg-bg-app">
              <div className="grid grid-cols-12 px-3.5 py-2 text-[10px] font-mono uppercase tracking-wider text-text-muted border-b border-[#2d2d2d]">
                <div className="col-span-5">Nombre del dispositivo</div>
                <div className="col-span-3">Activo por última vez</div>
                <div className="col-span-2 hidden sm:block">Ubicación</div>
                <div className="col-span-4 sm:col-span-2 text-right">Acción</div>
              </div>

              <div className="divide-y divide-[#2d2d2d]">
                {devices.map((device) => (
                  <div
                    key={device.id}
                    className="grid grid-cols-12 px-3.5 py-2.5 items-center text-xs hover:bg-[#252525] transition-colors"
                  >
                    {/* Dispositivo */}
                    <div className="col-span-5 flex items-center gap-2.5 min-w-0 pr-2">
                      {device.type === "mobile" ? (
                        <Smartphone className="w-4 h-4 text-text-muted shrink-0" />
                      ) : (
                        <Laptop className="w-4 h-4 text-text-muted shrink-0" />
                      )}
                      <div className="min-w-0">
                        <p className="font-medium text-white truncate text-xs">{device.name}</p>
                        {device.isCurrent && (
                          <span className="text-[10px] font-semibold text-primary-DEFAULT">
                            Este dispositivo
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Última actividad */}
                    <div className="col-span-3 text-[11px] text-text-muted">
                      {device.lastActive}
                    </div>

                    {/* Ubicación */}
                    <div className="col-span-2 hidden sm:block text-[11px] text-text-muted truncate">
                      {device.location}
                    </div>

                    {/* Acción */}
                    <div className="col-span-4 sm:col-span-2 flex justify-end">
                      {device.isCurrent ? (
                        <span className="text-[10px] font-mono text-status-success bg-status-success-bg px-2 py-0.5 rounded-full border border-status-success-border">
                          Activo ahora
                        </span>
                      ) : (
                        <button
                          type="button"
                          onClick={() => handleTerminateSession(device.id)}
                          className="px-2.5 py-1 rounded-md bg-[#2d2d2d] hover:bg-[#383838] border border-white/10 text-white text-[11px] font-medium transition-colors cursor-pointer"
                        >
                          Cerrar sesión
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* 5. Sección ID de usuario */}
          <div className="pt-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h4 className="text-sm font-semibold text-white">ID de usuario</h4>
                <p className="text-xs text-text-muted mt-0.5">
                  Identificador alfanumérico único para soporte y auditoría del sistema.
                </p>
              </div>

              <div className="flex items-center gap-2 bg-bg-app border border-border-secondary px-3 py-1.5 rounded-lg shrink-0">
                <span className="font-mono text-xs text-text-secondary select-all">
                  {userId}
                </span>
                <button
                  type="button"
                  onClick={handleCopyUserId}
                  className="p-1 rounded text-text-muted hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
                  title="Copiar ID de usuario"
                >
                  {hasCopiedId ? (
                    <Check className="w-3.5 h-3.5 text-status-success" />
                  ) : (
                    <Copy className="w-3.5 h-3.5" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
