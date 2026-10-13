import { useState, useEffect } from "react";
import {
  X,
  Laptop,
  Smartphone,
  Copy,
  Check,
  HelpCircle,
  AlertTriangle,
  LogOut,
  ShieldCheck,
  Lock,
  Save,
  Loader2,
  Mail,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { authService } from "../../services/authService";
import { ChangePasswordModal } from "./ChangePasswordModal";
import { ChangeEmailModal } from "./ChangeEmailModal";
import avatar1 from "../../assets/png/avatar9.png";

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

  const isSuperuser = Boolean(user?.isSuperuser || user?.username === "admin");
  const isEnforced = !isSuperuser && Boolean(user?.mustChangePassword);

  // Estado del modal de cambio de contraseña
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(isEnforced);

  // Estado del modal de cambio de correo
  const [isEmailModalOpen, setIsEmailModalOpen] = useState(false);

  // Estado de edición de nombre
  const [editFullName, setEditFullName] = useState(user?.fullName || "");
  const [isSavingName, setIsSavingName] = useState(false);
  const [isNameDirty, setIsNameDirty] = useState(false);

  useEffect(() => {
    setEditFullName(user?.fullName || "");
    setIsNameDirty(false);
  }, [user?.fullName]);

  // Si mustChangePassword es true, abrir automáticamente el modal de contraseña (salvo superuser)
  useEffect(() => {
    if (!isSuperuser && user?.mustChangePassword) {
      setIsPasswordModalOpen(true);
    }
  }, [isSuperuser, user?.mustChangePassword]);

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
  const userId = user?.id || "8e377fc8-885a-4b90-8efb-99170b385ddb";
  const [hasCopiedId, setHasCopiedId] = useState(false);

  const handleSaveName = async () => {
    if (isSuperuser) {
      toast("La cuenta superusuario está protegida y no puede ser modificada", "error");
      return;
    }
    const trimmed = editFullName.trim().replace(/\s+/g, " ");
    if (trimmed.length < 2) {
      toast("El nombre debe tener al menos 2 caracteres", "warning");
      return;
    }
    setIsSavingName(true);
    try {
      const res = await authService.updateProfile({ fullName: trimmed });
      if (!res.success) {
        toast(res.error || "No se pudo actualizar el nombre", "error");
        return;
      }
      setIsNameDirty(false);
      toast("Nombre actualizado correctamente", "success", "Perfil");
    } catch {
      toast("Error al guardar el nombre", "error");
    } finally {
      setIsSavingName(false);
    }
  };

  const isAnySubModalOpen = isPasswordModalOpen || isEmailModalOpen;

  // Cerrar con Escape solo si NO es cambio obligatorio y NO está abierto ningún submodal
  useEffect(() => {
    if (!isOpen || isAnySubModalOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isEnforced) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, isEnforced, isAnySubModalOpen]);

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

  const handleLogoutFromModal = async () => {
    await logout();
    window.location.href = "/";
  };

  return (
    <>
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/65 backdrop-blur-xs animate-in fade-in duration-150"
        onClick={() => {
          if (!isEnforced && !isAnySubModalOpen) onClose();
        }}
      >
        <div
          className="card bg-bg-accent/60 w-full max-w-2xl max-h-[90vh] shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Encabezado del modal */}
          <div className="card-header shrink-0">
            <div>
              <h2 className="text-base sm:text-xl font-bold font-special">
                {isEnforced ? "Actualización de Seguridad Requerida" : "Cuenta"}
              </h2>
              <p className="text-xs sm:text-sm mt-0.5">
                {isEnforced
                  ? "Debes establecer una nueva contraseña personal para continuar."
                  : "Gestiona tu perfil, tus datos de inicio de sesión y tus dispositivos."}
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
                className="w-5 h-5 rounded-full bg-[#2f2f2f] hover:bg-[#3d3d3d] text-neutral-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
                aria-label="Cerrar modal"
              >
                <X className="w-3.5 h-3.5" />
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
          <div className="overflow-y-auto px-6 py-4 space-y-4">
            {/* 1. Datos Generales de la Cuenta */}
            <div className="flex flex-col justify-center gap-4 divide-y divide-[#2d2d2d]">
              <div className="flex items-center gap-2 pb-3">
                <h4 className="font-special font-semibold text-white">Perfil</h4>
              </div>

              <div className="flex items-start gap-4">
                <div className="relative w-15 h-15 rounded-full flex items-center justify-center shrink-0 shadow-md mt-1">
                  <img
                    src={avatar1}
                    alt="Avatar"
                    className="w-full h-full rounded-full object-cover"
                  />
                  <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 rounded-full bg-status-success ring-2 ring-[#202020]" />
                </div>

                <div className="min-w-0 flex-1 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-semibold text-text-primary">
                      @{user?.username || "admin"}
                    </span>
                    <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-primary-muted text-primary-DEFAULT border border-primary-DEFAULT/30">
                      {getRoleDisplayName(role)}
                    </span>
                    {isSuperuser && (
                      <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3" />
                        Superuser
                      </span>
                    )}
                  </div>

                  <div>
                    <label htmlFor="profile-fullname-input" className="block text-[13px] font-medium">
                      Nombre
                    </label>
                    {isSuperuser ? (
                      <div className="mt-1 flex items-center gap-2">
                        <input
                          id="profile-fullname-input"
                          type="text"
                          readOnly
                          value={user?.fullName || "Administrador del Sistema"}
                          className="w-full px-3 py-1.5 text-xs rounded-lg bg-[#1a1a1a] border border-[#303030] text-text-muted cursor-not-allowed font-sans select-none"
                          title="Protegido por configuración .env"
                        />
                        <div
                          className="px-2.5 py-1.5 rounded-lg bg-neutral-800/80 border border-neutral-700/60 text-[11px] text-text-muted flex items-center gap-1 shrink-0"
                          title="No modificable para el superusuario"
                        >
                          <Lock className="w-3 h-3 text-amber-400" />
                          <span className="font-mono">Protegido</span>
                        </div>
                      </div>
                    ) : (
                      <div className="mt-1 flex items-center gap-2">
                        <div className="relative flex-1">
                          <input
                            id="profile-fullname-input"
                            type="text"
                            value={editFullName}
                            onChange={(e) => {
                              setEditFullName(e.target.value);
                              setIsNameDirty(e.target.value.trim() !== (user?.fullName || ""));
                            }}
                            onKeyDown={(e) => {
                              if (e.key === "Enter" && isNameDirty && editFullName.trim().length >= 2) {
                                e.preventDefault();
                                handleSaveName();
                              }
                            }}
                            placeholder="ej: Mario Gómez"
                            maxLength={80}
                            className="w-full px-3 py-1.5 text-xs rounded-lg bg-[#1a1a1a] border border-[#383838] focus:border-primary-DEFAULT text-white placeholder:text-text-disabled focus:outline-none transition-colors"
                          />
                        </div>
                        <button
                          type="button"
                          onClick={handleSaveName}
                          disabled={!isNameDirty || isSavingName || editFullName.trim().length < 2}
                          className="btn-primary text-xs px-3 py-1.5 shrink-0 flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
                          title="Guardar nombre"
                        >
                          {isSavingName ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                          ) : (
                            <Save className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    )}
                    <p className="text-[10px] text-text-muted mt-1">
                      Nombre con el que te identificas dentro del sistema SIGAP.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* 2. Sección Seguridad de la cuenta */}
            <div className="pt-6 space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-border-primary">
                <h4 className="font-special font-semibold text-white">Seguridad de la cuenta</h4>
              </div>

              {/* Correo electrónico */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 ">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-[13px] font-medium text-white">Correo electrónico</p>
                    {isSuperuser ? (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40">
                        Protegido
                      </span>
                    ) : (
                      user?.email && (
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-status-success/20 text-status-success border border-status-success/30">
                          Asociado
                        </span>
                      )
                    )}
                  </div>
                  <p className="text-[12px] text-text-muted mt-0.5 font-mono">
                    {user?.email || <span className="text-text-disabled italic font-sans">Sin correo registrado</span>}
                  </p>
                </div>

                {isSuperuser ? (
                  <div
                    className="px-3 py-1.5 rounded-lg bg-neutral-800/80 border border-neutral-700/60 text-xs text-text-muted flex items-center gap-1.5 shrink-0"
                    title="Esta cuenta solo puede gestionarse mediante el archivo .env"
                  >
                    <Lock className="w-3.5 h-3.5 text-amber-400" />
                    <span className="font-mono">Protegido</span>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setIsEmailModalOpen(true)}
                    className="px-3.5 py-1.5 rounded-lg bg-[#2a2a2a] hover:bg-[#333333] border border-[#3e3e3e] text-xs font-medium text-white transition-colors cursor-pointer shrink-0"
                  >
                    {user?.email ? "Cambiar correo" : "Asociar correo"}
                  </button>
                )}
              </div>

              {/* Contraseña */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-[13px] font-medium text-white">Contraseña</p>
                    {isSuperuser ? (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40">
                        Definida en .env
                      </span>
                    ) : isEnforced && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40">
                        Requerido
                      </span>
                    )}
                  </div>
                  <p className="text-[12px] text-text-muted mt-0.5">
                    {isSuperuser
                      ? "La cuenta superusuario está protegida y sus credenciales se administran desde el archivo .env."
                      : "Establece una contraseña para tu cuenta"}
                  </p>
                </div>

                {isSuperuser ? (
                  <div
                    className="px-3 py-1.5 rounded-lg bg-neutral-800/80 border border-neutral-700/60 text-xs text-text-muted flex items-center gap-1.5 shrink-0"
                    title="Esta cuenta solo puede gestionarse mediante el archivo .env"
                  >
                    <Lock className="w-3.5 h-3.5 text-amber-400" />
                    <span className="font-mono">Protegida</span>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={() => setIsPasswordModalOpen(true)}
                    className="px-3.5 py-1.5 rounded-lg bg-[#2a2a2a] hover:bg-[#333333] border border-[#3e3e3e] text-xs font-medium text-white transition-colors cursor-pointer shrink-0"
                  >
                    Cambiar contraseña
                  </button>
                )}
              </div>
            </div>

            {/* 5. Sección ID de usuario */}
            <div className="pt-6 divide-y divide-[#2d2d2d]">
              <div className="flex items-center gap-2 pb-3">
                <h4 className="font-special font-semibold text-white">ID de usuario</h4>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 py-2">
                <h4 className="text-[13px] text-text-secondary">ID de usuario</h4>

                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg shrink-0">
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

      {/* Modal de cambio de contraseña independiente a nivel hermano para evitar propagación de eventos */}
      <ChangePasswordModal
        isOpen={isPasswordModalOpen}
        onClose={() => setIsPasswordModalOpen(false)}
        isEnforced={isEnforced}
        onSuccess={() => {
          setIsPasswordModalOpen(false);
          if (isEnforced) {
            onClose();
          }
        }}
      />

      {/* Modal de cambio de correo electrónico independiente a nivel hermano */}
      <ChangeEmailModal
        isOpen={isEmailModalOpen}
        onClose={() => setIsEmailModalOpen(false)}
        onSuccess={() => {
          setIsEmailModalOpen(false);
        }}
      />
    </>
  );
}
