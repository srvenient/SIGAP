import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router";
import { AlertCircle, Eye, EyeOff, Loader2 } from "lucide-react";
import { Brand } from "../components/ui/Brand";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

type AuthErrorType = "credentials" | "inactive" | "locked" | "server";

export default function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [authError, setAuthError] = useState<{ type: AuthErrorType; message: string } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const canSubmit = username.trim().length > 0 && password.length > 0 && !isSubmitting && !isLoading;

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setAuthError(null);
    setIsSubmitting(true);
    try {
      const res = await login({ username: username.trim(), password, rememberMe });
      if (res.success) {
        navigate("/dashboard", { replace: true });
        return;
      }

      if (res.status === 401) {
        setAuthError({ type: "credentials", message: "Usuario o contraseña incorrectos." });
      } else if (res.status === 403) {
        setAuthError({ type: "inactive", message: "Esta cuenta no está habilitada. Comunícate con el administrador." });
      } else if (res.status === 429) {
        const minutes = res.retryAfter ? Math.ceil(res.retryAfter / 60) : 15;
        setAuthError({
          type: "locked",
          message: `Demasiados intentos fallidos. Vuelve a intentarlo en ${minutes} min.`,
        });
      } else {
        setAuthError({ type: "server", message: "No pudimos conectar con el servidor. Inténtalo más tarde." });
        toast("El servidor de autenticación no responde.", "error");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const fieldState = authError?.type === "credentials" ? "input-error" : "";

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4 py-10 bg-[radial-gradient(60%_45%_at_50%_0%,rgb(255_255_255/0.045),transparent)]">
      <main className="w-full max-w-sm">
        <div className="flex justify-center mb-7">
          <Brand />
        </div>

        <div className="card p-6 sm:p-7">
          <h1 className="text-lg font-semibold tracking-tight">Inicia sesión</h1>
          <p className="mt-0.5 mb-5 text-sm text-text-muted">Accede al panel de operación del parqueadero.</p>

          {authError && (
            <div
              role="alert"
              className="mb-4 flex items-start gap-2 rounded-md border border-status-error-border bg-status-error-soft px-3 py-2 text-sm text-status-error"
            >
              <AlertCircle className="w-4 h-4 mt-px shrink-0" />
              <p>{authError.message}</p>
            </div>
          )}

          <form noValidate onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="username" className="label">
                Usuario o correo
              </label>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setAuthError(null);
                }}
                className={`input ${fieldState}`}
              />
            </div>

            <div>
              <label htmlFor="password" className="label">
                Contraseña
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setAuthError(null);
                  }}
                  className={`input pr-10 ${fieldState}`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted hover:text-text-primary cursor-pointer"
                  aria-label={showPassword ? "Ocultar contraseña" : "Ver contraseña"}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer select-none">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="w-3.5 h-3.5 accent-steel"
              />
              Recordar sesión
            </label>

            <button type="submit" disabled={!canSubmit} className="btn-primary w-full h-10!">
              {isSubmitting || isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Entrar"}
            </button>
          </form>
        </div>

        <p className="mt-5 text-center text-sm text-text-muted">
          ¿Vas a pagar tu parqueo?{" "}
          <Link to="/pago" className="font-medium text-text-primary hover:underline underline-offset-2">
            Ir al módulo de pago
          </Link>
        </p>
      </main>
    </div>
  );
}
