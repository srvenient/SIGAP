import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from "lucide-react";

export type ToastType = "success" | "error" | "warning" | "info";

export interface ToastMessage {
  id: string;
  type: ToastType;
  title?: string;
  message: string;
}

interface ToastContextType {
  toast: (message: string, type?: ToastType, title?: string) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

const STYLES: Record<ToastType, { icon: typeof Info; border: string; color: string }> = {
  success: { icon: CheckCircle2, border: "border-l-status-success", color: "text-status-success" },
  error: { icon: XCircle, border: "border-l-status-error", color: "text-status-error" },
  warning: { icon: AlertTriangle, border: "border-l-status-warning", color: "text-status-warning" },
  info: { icon: Info, border: "border-l-steel", color: "text-steel" },
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, type: ToastType = "info", title?: string) => {
      const id = `toast-${Date.now()}-${Math.random()}`;
      setToasts((prev) => [...prev, { id, type, title, message }]);
      setTimeout(() => {
        removeToast(id);
      }, 4500);
    },
    [removeToast]
  );

  return (
    <ToastContext.Provider value={{ toast, removeToast }}>
      {children}
      <div className="fixed top-5 right-5 z-[60] flex flex-col gap-2 pointer-events-none max-w-md w-full px-4" aria-live="polite">
        {toasts.map((item) => {
          const style = STYLES[item.type];
          const Icon = style.icon;
          return (
            <div
              key={item.id}
              className={`pointer-events-auto flex items-start gap-3 p-3.5 rounded-md border border-border-primary border-l-2 bg-bg-surface-elevated text-text-primary shadow-xl shadow-black/40 ${style.border}`}
            >
              <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${style.color}`} />
              <div className="flex-1 text-sm">
                {item.title && <p className="font-medium mb-0.5">{item.title}</p>}
                <p className="text-text-secondary">{item.message}</p>
              </div>
              <button
                onClick={() => removeToast(item.id)}
                className="shrink-0 text-text-muted hover:text-text-primary transition-colors cursor-pointer"
                aria-label="Cerrar notificación"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextType {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
