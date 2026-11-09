import {
  isRouteErrorResponse,
  Links,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
} from "react-router";

import type { Route } from "./+types/root";
import "./app.css";
import { AuthProvider } from "./context/AuthContext";
import { ToastProvider } from "./context/ToastContext";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="color-scheme" content="dark" />
        <meta name="theme-color" content="#0b0d10" />
        <title>SIGAP - Sistema Integral de Gestión y Automatización de Parqueaderos</title>
        <Meta />
        <Links />
      </head>
      <body className="antialiased">
        {children}
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <Outlet />
      </ToastProvider>
    </AuthProvider>
  );
}

export function ErrorBoundary({ error }: Route.ErrorBoundaryProps) {
  let message = "Algo salió mal";
  let details = "Ocurrió un error inesperado en la aplicación.";
  let stack: string | undefined;

  if (isRouteErrorResponse(error)) {
    message = error.status === 404 ? "Página no encontrada" : "Error";
    details = error.status === 404 ? "La pantalla solicitada no existe." : error.statusText || details;
  } else if (import.meta.env.DEV && error && error instanceof Error) {
    details = error.message;
    stack = error.stack;
  }

  return (
    <main className="min-h-screen flex items-center justify-center p-6">
      <div className="max-w-md w-full card p-8 text-center space-y-4">
        <h1 className="text-xl font-semibold">{message}</h1>
        <p className="text-sm text-text-secondary">{details}</p>
        {stack && (
          <pre className="w-full p-4 overflow-x-auto text-left text-xs bg-bg-app rounded text-status-error font-mono">
            <code>{stack}</code>
          </pre>
        )}
        <a href="/" className="btn-primary">
          Volver al inicio
        </a>
      </div>
    </main>
  );
}
