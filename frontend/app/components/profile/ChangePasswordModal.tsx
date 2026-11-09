import React, { useState, useEffect } from "react";
import {
  X,
  Eye,
  EyeOff,
  Loader2,
  LogOut,
  Check,
  AlertCircle,
  RectangleEllipsis,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { authService } from "../../services/authService";

export interface ChangePasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
  isEnforced?: boolean;
  onSuccess?: () => void;
}

export function ChangePasswordModal({
  isOpen,
  onClose,
  isEnforced = false,
  onSuccess,
}: ChangePasswordModalProps) {
  const { logout } = useAuth();
  const { toast } = useToast();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  // Control de interacción para UX no intrusivo
  const [isCurrentTouched, setIsCurrentTouched] = useState(false);
  const [isNewFocused, setIsNewFocused] = useState(false);
  const [isConfirmTouched, setIsConfirmTouched] = useState(false);

  // Cerrar con Escape solo si no es cambio obligatorio
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !isEnforced) {
        e.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose, isEnforced]);

  // Limpiar campos y errores al abrir/cerrar
  useEffect(() => {
    if (isOpen) {
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setServerError(null);
      setIsCurrentTouched(false);
      setIsNewFocused(false);
      setIsConfirmTouched(false);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  // Criterios de validación en tiempo real (UI/UX)
  const hasMinLength = newPassword.length >= 8;
  const hasLetter = /[a-zA-Z]/.test(newPassword);
  const hasNumber = /[0-9]/.test(newPassword);
  const hasLettersAndNumbers = /[a-z]/.test(newPassword) && /[A-Z]/.test(newPassword) && hasNumber;
  const isDifferentFromCurrent = !currentPassword || !newPassword || newPassword !== currentPassword;
  const passwordsMatch = confirmPassword.length > 0 && newPassword === confirmPassword;
  const passwordsDoNotMatch = confirmPassword.length > 0 && newPassword !== confirmPassword;

  // Medidor de fortaleza de contraseña (0 a 3)
  const strengthScore = (() => {
    if (!newPassword) return 0;
    let score = 0;
    if (hasMinLength) score += 1;
    if (hasLettersAndNumbers) score += 1;
    if (newPassword.length >= 12 || /[^a-zA-Z0-9]/.test(newPassword)) score += 1;
    return score;
  })();

  const strengthLabel = (() => {
    if (!newPassword) return "";
    if (strengthScore <= 1) return "Débil";
    if (strengthScore === 2) return "Aceptable";
    return "Fuerte";
  })();

  const strengthColor = (() => {
    if (strengthScore <= 1) return "text-status-error";
    if (strengthScore === 2) return "text-status-warning";
    return "text-status-success";
  })();

  const isFormValid =
    currentPassword.trim().length > 0 &&
    hasMinLength &&
    hasLettersAndNumbers &&
    isDifferentFromCurrent &&
    passwordsMatch;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);

    // Marcar campos como interactuados para destacar cualquier pendiente
    setIsCurrentTouched(true);
    setIsConfirmTouched(true);

    if (!currentPassword.trim()) {
      setServerError("Ingresa tu contraseña actual");
      toast("Ingresa tu contraseña actual", "error", "Campo requerido");
      return;
    }

    if (!hasMinLength) {
      setServerError("La nueva contraseña debe tener al menos 8 caracteres");
      toast(
        "La nueva contraseña debe tener al menos 8 caracteres",
        "error",
        "Requisito de seguridad"
      );
      return;
    }

    if (!hasLettersAndNumbers) {
      setServerError("La contraseña debe incluir mayúscula, minúscula y número");
      toast(
        "La contraseña debe incluir mayúscula, minúscula y número",
        "error",
        "Requisito de seguridad"
      );
      return;
    }

    if (newPassword === currentPassword) {
      setServerError("La nueva contraseña debe ser diferente a la actual");
      toast(
        "La nueva contraseña debe ser diferente a la actual",
        "error",
        "Contraseña idéntica"
      );
      return;
    }

    if (newPassword !== confirmPassword) {
      setServerError("Las contraseñas no coinciden");
      toast("Las contraseñas no coinciden", "error", "Validación");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await authService.changePassword(currentPassword, newPassword);
      if (res.success) {
        toast(
          "¡Contraseña actualizada exitosamente! Entorno de seguridad activo.",
          "success",
          "Seguridad"
        );
        onClose();
        onSuccess?.();
      } else {
        const errorMsg = res.error || "No se pudo actualizar la contraseña";
        setServerError(errorMsg);
        toast(errorMsg, "error", "Error de autenticación");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error al procesar la solicitud";
      setServerError(msg);
      toast(msg, "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    window.location.href = "/";
  };

  return (
    <div
      className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={(e) => {
        e.stopPropagation();
        if (!isEnforced) onClose();
      }}
    >
      <div
        className="bg-bg-app border border-border-primary rounded-2xl p-6 sm:p-7 max-w-sm w-full shadow-2xl relative flex flex-col items-center animate-in zoom-in-95 duration-150 select-none sm:select-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Botón cerrar X circular estilo Notion (o salir si es obligatorio) */}
        {!isEnforced ? (
          <button
            type="button"
            onClick={onClose}
            className="absolute top-3.5 right-3.5 w-5 h-5 rounded-full bg-bg-accent hover:bg-border-primary text-text-muted hover:text-text-primary flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Cerrar"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        ) : (
          <button
            type="button"
            onClick={handleLogout}
            className="absolute top-3.5 right-3.5 px-2.5 py-1 rounded-md text-xs font-medium text-status-error hover:bg-status-error-soft/20 transition-colors cursor-pointer flex items-center gap-1"
            title="Cerrar sesión"
          >
            <LogOut className="w-3 h-3" />
            <span>Salir</span>
          </button>
        )}

        {/* Ícono de contraseña con puntos de entrada estilo Notion de la foto */}
        <div className="flex justify-center text-text-primary">
          <RectangleEllipsis className="w-10 h-10" />
        </div>

        {/* Título idéntico a la imagen de referencia */}
        <h3 className="text-base sm:text-lg font-medium text-text-primary text-center mt-2.5 mb-1.5 font-special tracking-tight">
          Establece una contraseña
        </h3>

        {/* Descripción textual exacta de la imagen */}
        <p className="text-sm text-text-secondary text-center leading-relaxed mb-4 px-1">
          Elige una contraseña con al menos 8 caracteres, con letras y números.
        </p>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="w-full space-y-3.5">
          {/* Contraseña actual (requerida para seguridad del backend) */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Contraseña actual {isEnforced && "(o temporal inicial)"}
            </label>
            <div className="relative">
              <input
                type={showCurrent ? "text" : "password"}
                value={currentPassword}
                onChange={(e) => {
                  setCurrentPassword(e.target.value);
                  setServerError(null);
                }}
                onBlur={() => setIsCurrentTouched(true)}
                placeholder="Contraseña actual"
                required
                className={`w-full px-3.5 py-2.5 text-xs sm:text-sm rounded-lg bg-bg-app text-text-primary outline-none transition-all placeholder:text-text-disabled pr-9 border ${isCurrentTouched && !currentPassword.trim()
                  ? "border-status-error focus:border-status-error focus:ring-1 focus:ring-status-error/30"
                  : "border-border-primary focus:border-border-primary focus:ring-1 focus:ring-primary-DEFAULT"
                  }`}
              />
              <button
                type="button"
                onClick={() => setShowCurrent(!showCurrent)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-1 transition-colors cursor-pointer"
                aria-label="Ver contraseña"
              >
                {showCurrent ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
            {isCurrentTouched && !currentPassword.trim() && (
              <p className="text-xs text-status-error mt-1 flex items-center gap-1 animate-in fade-in duration-150">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>Ingresa tu contraseña actual</span>
              </p>
            )}
          </div>

          {/* Ingresa una nueva contraseña */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Ingresa una nueva contraseña
            </label>
            <div className="relative">
              <input
                type={showNew ? "text" : "password"}
                value={newPassword}
                onChange={(e) => {
                  setNewPassword(e.target.value);
                  setServerError(null);
                }}
                onFocus={() => setIsNewFocused(true)}
                placeholder="Nueva contraseña"
                required
                minLength={8}
                className={`w-full px-3.5 py-2.5 text-xs sm:text-sm rounded-lg bg-bg-app text-text-primary outline-none transition-all placeholder:text-text-disabled pr-9 border ${newPassword && !isDifferentFromCurrent
                  ? "border-status-warning focus:border-status-warning focus:ring-1 focus:ring-status-warning/30"
                  : newPassword && hasMinLength && hasLettersAndNumbers
                    ? "border-status-success focus:border-status-success focus:ring-1 focus:ring-status-success/30"
                    : "border-border-primary focus:border-border-primary focus:ring-1 focus:ring-primary-DEFAULT"
                  }`}
              />
              <button
                type="button"
                onClick={() => setShowNew(!showNew)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-1 transition-colors cursor-pointer"
                aria-label="Ver contraseña"
              >
                {showNew ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>

            {/* Checklist interactiva y medidor de fortaleza de contraseña (UI/UX) */}
            {(newPassword.length > 0 || isNewFocused) && (
              <div className="mt-2 p-2.5 rounded-lg bg-bg-app border border-border-primary space-y-2 animate-in fade-in duration-150">
                {/* Barra de progreso de fortaleza */}
                {newPassword.length > 0 && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-text-muted">Fortaleza:</span>
                      <span className={`font-medium ${strengthColor}`}>{strengthLabel}</span>
                    </div>
                    <div className="grid grid-cols-3 gap-1 h-1">
                      <div
                        className={`rounded-full transition-colors duration-200 ${strengthScore >= 1
                          ? strengthScore === 1
                            ? "bg-status-error"
                            : strengthScore === 2
                              ? "bg-status-warning"
                              : "bg-status-success"
                          : "bg-bg-accent"
                          }`}
                      />
                      <div
                        className={`rounded-full transition-colors duration-200 ${strengthScore >= 2
                          ? strengthScore === 2
                            ? "bg-status-warning"
                            : "bg-status-success"
                          : "bg-bg-accent"
                          }`}
                      />
                      <div
                        className={`rounded-full transition-colors duration-200 ${strengthScore >= 3 ? "bg-status-success" : "bg-bg-accent"
                          }`}
                      />
                    </div>
                  </div>
                )}

                {/* Requisitos específicos */}
                <div className="space-y-1 text-xs pt-0.5">
                  <div
                    className={`flex items-center gap-1.5 transition-colors ${hasMinLength ? "text-status-success font-medium" : "text-text-muted"
                      }`}
                  >
                    {hasMinLength ? (
                      <Check className="w-3 h-3 text-status-success shrink-0" />
                    ) : (
                      <span className="w-1.5 h-1.5 rounded-full bg-border-strong mx-0.75 shrink-0" />
                    )}
                    <span>Al menos 8 caracteres</span>
                  </div>

                  <div
                    className={`flex items-center gap-1.5 transition-colors ${hasLettersAndNumbers ? "text-status-success font-medium" : "text-text-muted"
                      }`}
                  >
                    {hasLettersAndNumbers ? (
                      <Check className="w-3 h-3 text-status-success shrink-0" />
                    ) : (
                      <span className="w-1.5 h-1.5 rounded-full bg-border-strong mx-0.75 shrink-0" />
                    )}
                    <span>Mayúscula, minúscula y número</span>
                  </div>

                  {currentPassword.trim().length > 0 && newPassword.length > 0 && (
                    <div
                      className={`flex items-center gap-1.5 transition-colors ${isDifferentFromCurrent
                        ? "text-status-success font-medium"
                        : "text-status-warning"
                        }`}
                    >
                      {isDifferentFromCurrent ? (
                        <Check className="w-3 h-3 text-status-success shrink-0" />
                      ) : (
                        <AlertCircle className="w-3 h-3 text-status-warning shrink-0" />
                      )}
                      <span>
                        {isDifferentFromCurrent
                          ? "Diferente a la contraseña actual"
                          : "Debe ser diferente a la contraseña actual"}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Confirma la nueva contraseña */}
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Confirma la nueva contraseña
            </label>
            <div className="relative">
              <input
                type={showConfirm ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  setIsConfirmTouched(true);
                  setServerError(null);
                }}
                placeholder="Confirmar contraseña"
                required
                minLength={8}
                className={`w-full px-3.5 py-2.5 text-xs sm:text-sm rounded-lg bg-bg-app text-text-primary outline-none transition-all placeholder:text-text-disabled pr-9 border ${confirmPassword.length > 0
                  ? passwordsMatch
                    ? "border-status-success focus:border-status-success focus:ring-1 focus:ring-status-success/30"
                    : "border-status-error focus:border-status-error focus:ring-1 focus:ring-status-error/30"
                  : isConfirmTouched && !confirmPassword
                    ? "border-status-error focus:border-status-error focus:ring-1 focus:ring-status-error/30"
                    : "border-border-primary focus:border-border-primary focus:ring-1 focus:ring-primary-DEFAULT"
                  }`}
              />
              <button
                type="button"
                onClick={() => setShowConfirm(!showConfirm)}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-primary p-1 transition-colors cursor-pointer"
                aria-label="Ver contraseña"
              >
                {showConfirm ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>

            {/* Mensaje de coincidencia en tiempo real */}
            {confirmPassword.length > 0 && (
              <div className="mt-1 animate-in fade-in duration-150">
                {passwordsMatch ? (
                  <p className="text-xs text-status-success flex items-center gap-1.5 font-medium">
                    <Check className="w-3 h-3 text-status-success shrink-0" />
                    <span>Las contraseñas coinciden</span>
                  </p>
                ) : (
                  <p className="text-xs text-status-error flex items-center gap-1.5">
                    <AlertCircle className="w-3 h-3 text-status-error shrink-0" />
                    <span>Las contraseñas no coinciden</span>
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Banner de error proveniente del servidor si ocurre */}
          {serverError && (
            <div className="p-2.5 rounded-lg bg-status-error-soft border border-status-error text-status-error text-xs flex items-start gap-2 animate-in fade-in duration-150">
              <AlertCircle className="w-4 h-4 text-status-error shrink-0 mt-0.5" />
              <span className="leading-tight">{serverError}</span>
            </div>
          )}

          {/* Botón azul eléctrico con validación de estado */}
          <button
            type="submit"
            disabled={!isFormValid || isSubmitting}
            className={`w-full py-2.5 px-4 rounded-lg font-medium text-xs sm:text-sm transition-all duration-150 flex items-center justify-center gap-2 mt-4 shadow-sm ${isFormValid && !isSubmitting
              ? "bg-primary-DEFAULT hover:bg-primary-hover text-on-primary cursor-pointer active:scale-[0.99]"
              : "bg-primary-DEFAULT/40 text-on-primary/50 cursor-not-allowed"
              }`}
          >
            {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
            <span>{isSubmitting ? "Actualizando..." : "Continuar"}</span>
          </button>
        </form>
      </div>
    </div>
  );
}


