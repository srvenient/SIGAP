import { useLocation, useNavigate } from "react-router";
import { Menu, Home, Bell, Settings, Search } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

export interface TopbarProps {
  onToggleSidebar: () => void;
  onOpenProfile?: () => void;
}

export function Topbar({ onToggleSidebar, onOpenProfile }: TopbarProps) {
  const { role } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  // Breadcrumbs contextuales según la URL actual
  const getViewTitle = (pathname: string): { category: string; title: string } => {
    if (pathname === "/dashboard") {
      if (role === "admin") return { category: "General", title: "Dashboard" };
      if (role === "operator") return { category: "Operación", title: "Dashboard" };
      return { category: "Infraestructura", title: "Dashboard" };
    }
    if (pathname === "/dashboard/users") return { category: "Usuarios", title: "Gestión de Usuarios" };
    if (pathname.includes("feature-in-progress")) return { category: "Roadmap", title: "Módulo en Desarrollo" };
    return { category: "SIGAP", title: "Dashboard" };
  };

  const viewInfo = getViewTitle(location.pathname);

  return (
    <header className="sticky top-0 z-30 h-20 px-4 sm:px-8 flex items-center justify-between bg-bg-app transition-colors">

      {/* Grupo Izquierdo: Botón Menú (Móvil) + Breadcrumbs y Título */}
      <div className="flex items-center gap-3 sm:gap-4 lg:gap-8 min-w-0">
        {/* Bloque de texto (Breadcrumbs + Título) */}
        <div className="flex flex-col min-w-0 gap-0.5">
          <div className="flex items-center gap-1 text-xs sm:text-sm text-text-muted font-medium">
            <button
              onClick={() => navigate('/dashboard')}
              className="text-text-muted hover:text-text-primary rounded-xl hover:bg-bg-surface-elevated cursor-pointer shrink-0 transition-colors"
              aria-label="Ir al inicio"
            >
              <Home className="w-3.5 h-3.5" />
            </button>
            <span>/</span>
            <span>{viewInfo.category}</span>
            <span>/</span>
            <span className="text-text-primary">{viewInfo.title}</span>
          </div>
          <h1 className="text-base sm:text-[19px] font-bold font-special truncate">
            {viewInfo.title}
          </h1>
        </div>

        {/* Botón Hamburger: solo visible cuando el sidebar desaparece (< lg) */}
        <button
          onClick={onToggleSidebar}
          className="lg:hidden p-2 text-text-muted hover:text-text-primary rounded-xl hover:bg-bg-surface-elevated cursor-pointer shrink-0 transition-colors"
          aria-label="Abrir menú"
        >
          <Menu className="w-5 h-5" />
        </button>
      </div>

      {/* Grupo Derecho: Buscador y Campana de Notificaciones */}
      <div className="flex items-center gap-1 shrink-0">
        {/* Buscador (oculto en pantallas muy pequeñas por diseño) */}
        <div className="relative hidden sm:block">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="w-4 h-4 text-text-muted" />
          </div>
          <input
            type="text"
            placeholder="Buscar en el sistema..."
            className="w-48 lg:w-64 bg-bg-surface border border-border-primary text-text-primary rounded-full pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-primary-DEFAULT focus:ring-1 focus:ring-primary-DEFAULT transition-all placeholder:text-text-muted"
          />
        </div>
        
        <button
          onClick={onOpenProfile}
          className="p-2 text-text-muted hover:text-text-primary rounded-full hover:bg-bg-surface-elevated transition-colors cursor-pointer"
          aria-label="Configuración de la cuenta"
          title="Configuración de la cuenta"
        >
          <Settings className="w-5 h-5" />
        </button>

        <button
          className="p-2 text-text-muted hover:text-text-primary rounded-full hover:bg-bg-surface-elevated transition-colors cursor-pointer"
          aria-label="Notificaciones"
        >
          <Bell className="w-5 h-5" />
        </button>
      </div>

    </header>
  );
}