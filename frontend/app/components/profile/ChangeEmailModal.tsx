import React, { useState, useEffect } from "react";
import {
  X,
  Mail,
  Loader2,
  Check,
  AlertCircle,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { authService } from "../../services/authService";

export interface ChangeEmailModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function ChangeEmailModal({
  isOpen,
  onClose,
  onSuccess,
}: ChangeEmailModalProps) {
  const { user } = useAuth();
  const { toast } = useToast();

  const [newEmail, setNewEmail] = useState("");
  const [confirmEmail, setConfirmEmail] = useState("");
  const [isTouched, setIsTouched] = useState(false);
  const [isConfirmTouched, setIsConfirmTouched] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  useEffect(() => {
    if (isOpen) {
      setNewEmail("");
      setConfirmEmail("");
      setIsTouched(false);
      setIsConfirmTouched(false);
      setServerError(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const currentEmail = user?.email || "";
  const trimmedNew = newEmail.trim().toLowerCase();
  const trimmedConfirm = confirmEmail.trim().toLowerCase();

  const isValidEmail = EMAIL_RE.test(trimmedNew);
  const isDifferentFromCurrent = !currentEmail || trimmedNew !== currentEmail.toLowerCase();
  const emailsMatch = trimmedConfirm.length > 0 && trimmedNew === trimmedConfirm;
  const emailsDoNotMatch = isConfirmTouched && trimmedConfirm.length > 0 && trimmedNew !== trimmedConfirm;

  const isFormValid =
    isValidEmail &&
    isDifferentFromCurrent &&
    emailsMatch &&
    !isSubmitting;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);

    if (!isValidEmail) {
      setServerError("Ingrese un correo electrónico válido (ej: usuario@empresa.com).");
      return;
    }
    if (!isDifferentFromCurrent) {
      setServerError("El nuevo correo debe ser diferente al actual.");
      return;
    }
    if (trimmedNew !== trimmedConfirm) {
      setServerError("Los correos electrónicos ingresados no coinciden.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await authService.updateProfile({ email: trimmedNew });
      if (!res.success) {
        setServerError(res.error || "No se pudo actualizar el correo electrónico.");
        return;
      }

      toast("Correo electrónico actualizado correctamente", "success", "Perfil actualizado");
      onSuccess?.();
      onClose();
    } catch {
      setServerError("Ocurrió un error inesperado al actualizar el correo.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-60 flex items-center justify-center p-3 sm:p-4 bg-black/75 backdrop-blur-xs animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="card w-full max-w-md shadow-2xl flex flex-col overflow-hidden animate-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Cabecera */}
        <div className="card-header shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#2a2a2a] border border-[#3e3e3e] flex items-center justify-center text-text-primary shrink-0">
              <Mail className="w-4 h-4 text-primary-DEFAULT" />
            </div>
            <div>
              <h2 className="text-sm sm:text-base font-bold font-special text-white">
                Cambiar correo electrónico
              </h2>
              <p className="text-[11px] text-text-muted mt-0.5">
                Asocia un correo para iniciar sesión o recuperar acceso
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-5 h-5 rounded-full bg-[#2f2f2f] hover:bg-[#3d3d3d] text-neutral-400 hover:text-white flex items-center justify-center transition-colors cursor-pointer"
            aria-label="Cerrar modal"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Formulario */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-4 text-xs">
          {serverError && (
            <div className="p-3 rounded-lg bg-status-error-bg/30 border border-status-error/40 flex items-start gap-2 text-status-error">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <p className="leading-snug">{serverError}</p>
            </div>
          )}

          {/* Correo actual */}
          <div className="p-3 rounded-lg bg-[#242424] border border-[#333333] flex items-center justify-between">
            <span className="text-text-muted text-[11px]">Correo actual:</span>
            <span className="font-mono text-text-primary text-[12px] truncate max-w-55">
              {currentEmail || <span className="text-text-disabled italic">Sin registrar</span>}
            </span>
          </div>

          {/* Nuevo correo */}
          <div className="space-y-1.5">
            <label htmlFor="new-email-input" className="block text-[11px] font-medium text-text-secondary">
              Nuevo correo electrónico
            </label>
            <div className="relative">
              <input
                id="new-email-input"
                type="email"
                value={newEmail}
                onChange={(e) => {
                  setNewEmail(e.target.value);
                  setIsTouched(true);
                  if (serverError) setServerError(null);
                }}
                placeholder="ej: usuario@empresa.com"
                maxLength={120}
                required
                className={`w-full px-3 py-2 text-xs rounded-lg bg-[#1a1a1a] border text-white placeholder:text-text-disabled focus:outline-none transition-colors ${
                  isTouched && !isValidEmail && trimmedNew.length > 0
                    ? "border-status-error focus:border-status-error"
                    : isTouched && isValidEmail
                    ? "border-status-success/60 focus:border-status-success"
                    : "border-[#383838] focus:border-primary-DEFAULT"
                }`}
              />
              {isTouched && isValidEmail && (
                <div className="absolute right-2.5 top-1/2 -translate-y-1/2 text-status-success">
                  <Check className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
            {isTouched && trimmedNew.length > 0 && !isValidEmail && (
              <p className="text-[10px] text-status-error">Formato de correo no válido.</p>
            )}
            {isTouched && currentEmail && trimmedNew === currentEmail.toLowerCase() && (
              <p className="text-[10px] text-status-warning">El nuevo correo debe ser distinto al actual.</p>
            )}
          </div>

          {/* Confirmar nuevo correo */}
          <div className="space-y-1.5">
            <label htmlFor="confirm-email-input" className="block text-[11px] font-medium text-text-secondary">
              Confirmar nuevo correo
            </label>
            <div className="relative">
              <input
                id="confirm-email-input"
                type="email"
                value={confirmEmail}
                onChange={(e) => {
                  setConfirmEmail(e.target.value);
                  setIsConfirmTouched(true);
                  if (serverError) setServerError(null);
                }}
                placeholder="Repite el nuevo correo"
                maxLength={120}
                required
                className={`w-full px-3 py-2 text-xs rounded-lg bg-[#1a1a1a] border text-white placeholder:text-text-disabled focus:outline-none transition-colors ${
                  emailsDoNotMatch
                    ? "border-status-error focus:border-status-error"
                    : emailsMatch
                    ? "border-status-success/60 focus:border-status-success"
                    : "border-[#383838] focus:border-primary-DEFAULT"
                }`}
              />
              {emailsMatch && (
                <div className="absolute right-2.5 top-1/2 -translate-y-1/2 text-status-success">
                  <Check className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
            {emailsDoNotMatch && (
              <p className="text-[10px] text-status-error">Los correos no coinciden.</p>
            )}
          </div>

          <div className="p-2.5 rounded-lg bg-[#1e1e1e] border border-[#2e2e2e] text-[11px] text-text-muted leading-relaxed">
            Podrás iniciar sesión usando tu nombre de usuario (<span className="text-text-primary font-mono font-medium">@{user?.username}</span>) o este nuevo correo.
          </div>

          {/* Botones de acción */}
          <div className="pt-2 flex items-center justify-end gap-2 border-t border-[#2d2d2d]">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-3.5 py-1.5 rounded-lg bg-transparent hover:bg-white/5 text-text-secondary hover:text-white transition-colors cursor-pointer"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!isFormValid}
              className="btn-primary flex items-center gap-1.5 px-4 py-1.5 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Guardando...</span>
                </>
              ) : (
                <span>Guardar correo</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
