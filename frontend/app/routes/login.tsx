import React, { useState, useEffect } from "react";
import type { Route } from "./+types/login";
import { useNavigate } from "react-router";
import {
  Lock,
  User,
  ArrowRight,
  AlertCircle,
  AlertTriangle,
  ShieldAlert,
  Shield,
  Eye,
  EyeOff,
  Loader2,
  Check,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import logo from "../assets/png/logo.png"

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  type AuthErrorType = "credentials" | "inactive" | "locked" | "server";

  const [authError, setAuthError] = useState<{
    type: AuthErrorType;
    message: string;
    retryAfter?: number;
  } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<{ username?: string; password?: string }>({});

  // Validación para habilitar el botón de acceso
  const isFormValid = username.trim().length > 0 && password.trim().length > 0;
  const isCredentialsError = authError?.type === "credentials";
  const isAccountLocked = authError?.type === "locked";

  // Redirigir al dashboard si ya está autenticado
  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleUsernameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setUsername(e.target.value);
    if (fieldErrors.username) {
      setFieldErrors((prev) => ({ ...prev, username: undefined }));
    }
    if (authError) {
      setAuthError(null);
    }
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPassword(e.target.value);
    if (fieldErrors.password) {
      setFieldErrors((prev) => ({ ...prev, password: undefined }));
    }
    if (authError) {
      setAuthError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);

    const newFieldErrors: { username?: string; password?: string } = {};

    if (!username.trim()) {
      newFieldErrors.username = "Por favor ingrese su usuario o correo";
    }

    if (!password.trim()) {
      newFieldErrors.password = "Por favor ingrese su contraseña";
    }

    if (Object.keys(newFieldErrors).length > 0) {
      setFieldErrors(newFieldErrors);
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await login({ username: username.trim(), password, rememberMe });
      if (res.success) {
        toast("Autenticación exitosa. Cargando entorno operacional...", "success", "Bienvenido");
        navigate("/dashboard", { replace: true });
      } else {
        const status = res.status;
        setFieldErrors({});

        if (status === 401) {
          // Error 401: Credenciales inválidas (InvalidCredentials)
          setAuthError({
            type: "credentials",
            message: res.error || "Usuario o correo y contraseña incorrectos",
          });
        } else if (status === 403) {
          // Error 403: Usuario inactivo (InactiveUser)
          setAuthError({
            type: "inactive",
            message: "Esta cuenta institucional se encuentra inactiva. Comuníquese con el administrador del sistema.",
          });
        } else if (status === 429) {
          // Error 429: Exceso de intentos / Cuenta bloqueada (AccountLocked / RateLimitExceeded)
          const waitMinutes = res.retryAfter ? Math.ceil(res.retryAfter / 60) : 15;
          setAuthError({
            type: "locked",
            message: `Demasiados intentos fallidos. Su cuenta ha sido bloqueada temporalmente por seguridad. Intente de nuevo en ${waitMinutes} minutos.`,
            retryAfter: res.retryAfter,
          });
        } else {
          // Error 500, 502, 503 o fallo de conexión
          setAuthError({
            type: "server",
            message: "El servidor de autenticación no se encuentra disponible. Por favor intente más tarde.",
          });
          toast(
            "No se pudo establecer conexión con el servidor de autenticación (500). Intente más tarde.",
            "error",
            "Error del Servidor"
          );
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex flex-col justify-between items-center px-4 py-4 sm:py-6">
      {/* Contenedor central perfectamente centrado */}
      <div className="flex-1 flex items-center justify-center w-full">
        <div className="card w-full max-w-110 py-8 space-y-6">
          {/* Encabezado */}
          <div className="text-center space-y-2">
            <div className="flex flex-col items-center justify-center -mt-2">
              <img src={logo} className="h-24 w-auto mx-auto mb-2" alt="Logo" />
              <h1 className="text-3xl font-bold font-special -mt-4">
                ¡Bienvenido!
              </h1>
            </div>
            <p className="text-text-muted text-sm -mt-1">
              Ingrese sus credenciales asignadas para acceder al sistema.
            </p>
          </div>

          {/* Tarjeta de Autenticación */}
          <div className="px-7 sm:px-8 space-y-6 relative">

            {authError && (
              <div
                className={`p-3.5 rounded-lg border flex items-start gap-2.5 text-xs animate-in fade-in duration-200 ${authError.type === "inactive"
                  ? "bg-amber-500/10 border-amber-500/25 text-amber-300"
                  : authError.type === "locked"
                    ? "bg-orange-500/10 border-orange-500/25 text-orange-300"
                    : "bg-rose-500/10 border-rose-500/25 text-rose-300"
                  }`}
              >
                {authError.type === "inactive" ? (
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                ) : authError.type === "locked" ? (
                  <ShieldAlert className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
                )}
                <div className="flex-1 font-medium">{authError.message}</div>
              </div>
            )}

            <form noValidate onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-1.5">
                <label
                  htmlFor="username"
                  className={`label transition-colors ${fieldErrors.username || isCredentialsError ? "text-rose-400" : ""}`}
                >
                  Usuario o correo
                </label>
                <div className="relative">
                  <span
                    className={`absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors ${fieldErrors.username || isCredentialsError ? "text-rose-400" : "text-text-muted"
                      }`}
                  >
                    <User className="w-4 h-4" />
                  </span>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    autoComplete="username"
                    value={username}
                    onChange={handleUsernameChange}
                    placeholder="Usuario o correo electrónico"
                    className={`input pl-10 text-sm ${fieldErrors.username || isCredentialsError ? "input-error" : ""}`}
                  />
                </div>
                {fieldErrors.username && (
                  <p className="flex items-center gap-1.5 text-xs text-rose-400 font-medium animate-in fade-in slide-in-from-top-1 duration-150">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>{fieldErrors.username}</span>
                  </p>
                )}
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="password"
                  className={`label transition-colors ${fieldErrors.password || isCredentialsError ? "text-rose-400" : ""}`}
                >
                  Contraseña
                </label>
                <div className="relative">
                  <span
                    className={`absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none transition-colors ${fieldErrors.password || isCredentialsError ? "text-rose-400" : "text-text-muted"
                      }`}
                  >
                    <Lock className="w-4 h-4" />
                  </span>
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={handlePasswordChange}
                    placeholder="Escribe tu contraseña"
                    className={`input pl-10 pr-10 text-sm ${fieldErrors.password || isCredentialsError ? "input-error" : ""}`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                    className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-text-muted hover:text-slate-300 cursor-pointer transition-colors"
                    title={showPassword ? "Ocultar contraseña" : "Ver contraseña"}
                  >
                    {showPassword ? (
                      <EyeOff className="w-4 h-4" />
                    ) : (
                      <Eye className="w-4 h-4" />
                    )}
                  </button>
                </div>
                {fieldErrors.password && (
                  <p className="flex items-center gap-1.5 text-xs text-rose-400 font-medium animate-in fade-in slide-in-from-top-1 duration-150">
                    <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                    <span>{fieldErrors.password}</span>
                  </p>
                )}
              </div>

              <div className="flex items-center pt-1 text-xs">
                <label className="inline-flex items-center gap-2.5 cursor-pointer text-slate-400 hover:text-slate-200 select-none group">
                  <input
                    type="checkbox"
                    id="rememberMe"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div
                    className={`w-4 h-4 rounded-md flex items-center justify-center border transition-all duration-200 peer-focus-visible:ring-2 peer-focus-visible:ring-blue-500/50 peer-focus-visible:ring-offset-2 peer-focus-visible:ring-offset-slate-950 ${rememberMe
                      ? "bg-blue-600 border-blue-500 shadow-sm shadow-blue-500/30 text-white"
                      : "bg-slate-900/90 border-slate-700 group-hover:border-slate-500 group-hover:bg-slate-800/80 text-transparent"
                      }`}
                    aria-hidden="true"
                  >
                    <Check
                      className={`w-3 h-3 stroke-3 transform transition-all duration-150 ${rememberMe ? "scale-100 opacity-100" : "scale-50 opacity-0"
                        }`}
                    />
                  </div>
                  <span className="font-medium text-slate-400 group-hover:text-slate-200 transition-colors select-none">
                    Recordar sesión
                  </span>
                </label>
              </div>

              <button
                type="submit"
                disabled={!isFormValid || isSubmitting || isLoading || isAccountLocked}
                className={`btn-primary w-full mt-2 transition-all duration-200 ${!isFormValid || isAccountLocked ? "opacity-40 cursor-not-allowed shadow-none" : ""
                  }`}
                title={
                  isAccountLocked
                    ? "Acceso bloqueado temporalmente por seguridad"
                    : !isFormValid
                      ? "Ingrese su usuario o correo y contraseña para habilitar el acceso"
                      : "Acceder al Sistema"
                }
              >
                {isSubmitting || isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Validando credenciales...</span>
                  </>
                ) : isAccountLocked ? (
                  <>
                    <ShieldAlert className="w-4 h-4 mr-1 text-orange-400" />
                    <span>Acceso Bloqueado Temporalmente</span>
                  </>
                ) : (
                  <>
                    <span>Acceder al Sistema</span>
                    <ArrowRight className="w-4 h-4 ml-1" />
                  </>
                )}
              </button>
            </form>

            <div className="flex items-center justify-center w-full ">
              <p className="text-[11px] text-text-secondary/50">
                Todas las acciones son registradas con fines de auditoría y trazabilidad.
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full text-center space-y-1">
        <p className="text-[11px] text-text-secondary/60">
          SIGAP &copy; 2026 &bull; Sistema Integral de Gestión y Automatización de Parqueaderos
        </p>
      </div>
    </div>
  );
}
