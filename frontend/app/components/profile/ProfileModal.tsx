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
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { ChangePasswordModal } from "./ChangePasswordModal";
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

  const isEnforced = Boolean(user?.mustChangePassword);

  // Estado del modal de cambio de contraseña
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(isEnforced);

  // Si mustChangePassword es true, abrir automáticamente el modal de contraseña
  useEffect(() => {
    if (user?.mustChangePassword) {
      setIsPasswordModalOpen(true);
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
  const userId = user?.id || "8e377fc8-885a-4b90-8efb-99170b385ddb";
  const [hasCopiedId, setHasCopiedId] = useState(false);

  // Cerrar con Escape solo si NO es cambio obligatorio y NO está abierto el modal de contraseña
  useEffect(() => {
    if (!isOpen || isPasswordModalOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isEnforced) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, isEnforced, isPasswordModalOpen]);

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
          if (!isEnforced && !isPasswordModalOpen) onClose();
        }}
      >
        <div
          className="card w-full max-w-2xl max-h-[90vh] shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
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

              <div className="flex items-center gap-4">
                <div className="relative w-15 h-15 rounded-full flex items-center justify-center shrink-0 shadow-md">
                  <img
                    src={avatar1}
                    alt="Avatar"
                    className="w-full h-full rounded-full object-cover"
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
            </div>

            {/* 2. Sección Seguridad de la cuenta */}
            <div className="pt-6 space-y-4 divide-y divide-[#2d2d2d]">
              <div className="flex items-center gap-2 pb-3">
                <h4 className="font-special font-semibold text-white">Seguridad de la cuenta</h4>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-[13px] font-medium text-white">Contraseña</p>
                    {isEnforced && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 border border-amber-500/40">
                        Requerido
                      </span>
                    )}
                  </div>
                  <p className="text-[12px] text-text-muted mt-0.5">
                    Establece una contraseña para tu cuenta
                  </p>
                </div>

                <button
                  type="button"
                  onClick={() => setIsPasswordModalOpen(true)}
                  className="px-3.5 py-1.5 rounded-lg bg-[#2a2a2a] hover:bg-[#333333] border border-[#3e3e3e] text-xs font-medium text-white transition-colors cursor-pointer shrink-0"
                >
                  Cambiar contraseña
                </button>
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
    </>
  );
}
