import React, { useState, useEffect, useRef } from "react";
import { NavLink, useNavigate } from "react-router";
import {
  Car,
  Clock,
  Wrench,
  Camera,
  LogOut,
  LifeBuoy,
  Search,
  LayoutDashboard,
  ChevronsUpDown,
  ChevronDown,
  PanelLeft,
  PanelLeftOpen,
  User,
  Settings,
  Cpu,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import logo from "../../assets/png/logo.png"
import avatar1 from "../../assets/png/avatar9.png"

interface NavItem {
  title: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string | number;
}

interface NavSection {
  category: string;
  items: NavItem[];
}

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  onOpenProfile?: () => void;
}

export function Sidebar({
  isOpen,
  onClose,
  isCollapsed = false,
  onToggleCollapse,
  onOpenProfile,
}: SidebarProps) {
  const { user, role, logout } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({});

  const dropdownRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Cerrar menús al hacer clic fuera o presionar Escape
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (userMenuRef.current && !userMenuRef.current.contains(target)) {
        setIsUserMenuOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsUserMenuOpen(false);
        setShowLogoutModal(false);
      }
      // Atajo Cmd/Ctrl + B para colapsar/expandir
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "b") {
        event.preventDefault();
        onToggleCollapse?.();
      }
      // Atajo Cmd/Ctrl + K para enfocar búsqueda
      if ((event.metaKey || event.ctrlKey) && (event.key.toLowerCase() === "k" || event.key.toLowerCase() === "f")) {
        event.preventDefault();
        if (isCollapsed) {
          onToggleCollapse?.();
        }
        setTimeout(() => searchInputRef.current?.focus(), 80);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isCollapsed, onToggleCollapse]);

  const toggleCategory = (category: string) => {
    setCollapsedCategories((prev) => ({
      ...prev,
      [category]: !prev[category],
    }));
  };

  const normalizedRole = (role || "").toLowerCase();
  const isAdmin = normalizedRole === "admin";
  const isOperator = normalizedRole === "operator";

  // Módulos corporativos según rol
  const getNavSections = (): NavSection[] => {
    if (isAdmin) {
      return [
        {
          category: "Usuarios",
          items: [
            { title: "Gestionar Usuarios", path: "/dashboard/users", icon: User },
          ],
        }
      ];
    }

    if (isOperator) {
      return [
        {
          category: "Operación de Patio",
          items: [
            { title: "Ingreso / Corrección Placa", path: "/dashboard/feature-in-progress", icon: Car },
            { title: "Vehículos en Parqueadero", path: "/dashboard/feature-in-progress", icon: Clock },
            { title: "Reportar Incidencia", path: "/dashboard/feature-in-progress", icon: LifeBuoy },
          ],
        },
      ];
    }

    return [
      {
        category: "Infraestructura & Hardware",
        items: [
          { title: "Consola de Dispositivos", path: "/dashboard/feature-in-progress", icon: Camera },
          { title: "Tickets de Soporte", path: "/dashboard/feature-in-progress", icon: Wrench },
        ],
      },
    ];
  };

  const navSections = getNavSections();

  const handleLogout = async () => {
    toast("Se cerró la sesión con éxito", "success", "Sesión finalizada");
    await logout();
    navigate("/");
  };

  const getRoleDisplayName = (r: string | null) => {
    switch (r?.toLowerCase()) {
      case "admin":
        return "Administrador";
      case "operator":
        return "Operador";
      case "support":
        return "Soporte Técnico";
      default:
        return "Usuario del Sistema";
    }
  };

  return (
    <>
      {/* Backdrop móvil */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/75 backdrop-blur-sm z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed top-0 bottom-0 left-0 z-40 
          ${isCollapsed ? "w-17" : "w-62"} bg-bg-surface 
          border-r border-border-secondary flex flex-col 
          transition-all duration-300 ease-in-out 
          lg:translate-x-0 ${isOpen ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        <div className="flex flex-col h-full overflow-hidden select-none font-sans">
          {/* ========================================================= */}
          {/* MODO COLAPSADO (Rail Industrial - Iconos y Acciones Clave) */}
          {/* ========================================================= */}
          {isCollapsed ? (
            <div className="flex flex-col h-full items-center py-2 justify-between">
              {/* Cabecera Rail */}
              <div className="flex flex-col items-center gap-2.5 w-full border-b border-border-secondary">
                <button
                  type="button"
                  onClick={onToggleCollapse}
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-text-muted hover:text-text-primary hover:bg-bg-app transition-colors cursor-pointer mb-2"
                  title="Expandir barra lateral (⌘B)"
                >
                  <PanelLeftOpen className="w-4.5 h-4.5" />
                </button>
              </div>

              <button
                type="button"
                onClick={() => {
                  onToggleCollapse?.();
                  setTimeout(() => searchInputRef.current?.focus(), 150);
                }}
                className="
                  flex items-center justify-center p-2 rounded-lg text-text-muted 
                  border border-border-secondary
                  hover:text-text-primary hover:bg-bg-app transition-colors cursor-pointer
                  mt-3 mb-4
                "
                title="Búsqueda rápida (⌘K)"
              >
                <Search className="w-4 h-4" />
              </button>

              {/* Lista de Iconos de Navegación Rail */}
              <div className="flex-1 w-full overflow-y-auto py-2 space-y-1.5 flex flex-col items-center scrollbar-none">
                {/* Panel de Control Principal */}
                <NavLink
                  to="/dashboard"
                  end
                  className={({ isActive }) =>
                    `w-10 h-10 rounded-lg flex items-center justify-center transition-all cursor-pointer ${isActive
                      ? "bg-bg-accent text-text-primary border border-border-primary shadow-xs"
                      : "text-text-muted hover:text-text-primary hover:bg-bg-app"
                    }`
                  }
                  title="Panel de Control"
                >
                  <LayoutDashboard className="w-4 h-4" />
                </NavLink>

                <div className="w-6 h-px bg-border-secondary my-1" />

                {/* Iconos por Secciones */}
                {navSections.map((section, sIdx) => (
                  <React.Fragment key={section.category || sIdx}>
                    {section.items.map((item) => {
                      const Icon = item.icon;
                      return (
                        <NavLink
                          key={item.path}
                          to={item.path}
                          end={item.path === "/dashboard"}
                          className={({ isActive }) =>
                            `w-10 h-10 rounded-lg flex items-center justify-center transition-all cursor-pointer ${isActive
                              ? "bg-bg-accent text-text-primary border border-border-primary shadow-xs"
                              : "text-text-muted hover:text-text-primary hover:bg-bg-app"
                            }`
                          }
                          title={item.title}
                        >
                          <Icon className="w-4 h-4" />
                        </NavLink>
                      );
                    })}
                    {sIdx < navSections.length - 1 && (
                      <div className="w-6 h-px bg-border-secondary my-1" />
                    )}
                  </React.Fragment>
                ))}
              </div>

              {/* Utilidades y Usuario en Rail */}

              <div className="flex flex-col items-center gap-2 w-full pt-2" ref={userMenuRef}>
                <div className="w-10 h-px bg-border-secondary my-1" />

                <div className="relative p-2 bg-bg-accent/40 rounded-xl border border-border-primary">
                  <button
                    type="button"
                    onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                    className="relative w-7 h-7 rounded-full flex items-center justify-center font-mono font-bold text-xs text-text-primary hover:border-border-strong transition-colors cursor-pointer shadow-xs"
                    title={`${user?.username || "Administrador"} • ${getRoleDisplayName(role)}`}
                  >
                    <img src={avatar1} alt="avatar" className="w-full h-full rounded-full" />
                    <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-status-success ring-2 ring-bg-surface" />
                  </button>
                </div>

                {/* Popover de Usuario en modo Rail */}
                {isUserMenuOpen && (
                  <div className="absolute left-18 bottom-3 w-64 z-50 bg-bg-surface-elevated border border-border-primary rounded-xl shadow-2xl p-2 space-y-1 animate-in fade-in zoom-in-95 duration-150">
                    <div className="flex items-center gap-2.5 p-2 border-b border-border-secondary">
                      <div className="w-8 h-8 rounded-lg bg-bg-app border border-border-primary flex items-center justify-center font-mono font-bold text-xs text-text-primary shrink-0">
                        <img src={avatar1} alt="avatar" className="w-full h-full rounded-full" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-text-primary truncate leading-tight">
                          {user?.username || "Administrador"}
                        </p>
                        <p className="text-[10px] text-text-muted truncate mt-0.5 font-mono">
                          {getRoleDisplayName(role)}
                        </p>
                      </div>
                    </div>

                    <div className="py-1 space-y-0.5">
                      <button
                        type="button"
                        onClick={() => {
                          setIsUserMenuOpen(false);
                          onOpenProfile?.();
                        }}
                        className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-bg-app transition-colors cursor-pointer"
                      >
                        <Settings className="w-3.5 h-3.5 text-text-muted" />
                        <span>Configuración de cuenta</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setIsUserMenuOpen(false);
                          navigate("/dashboard/devices");
                        }}
                        className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-bg-app transition-colors cursor-pointer"
                      >
                        <Cpu className="w-3.5 h-3.5 text-text-muted" />
                        <span>Consola de Dispositivos</span>
                      </button>

                      <div className="pt-1 border-t border-border-secondary">
                        <button
                          type="button"
                          onClick={() => {
                            setIsUserMenuOpen(false);
                            setShowLogoutModal(true);
                          }}
                          className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs font-medium text-status-error hover:bg-status-error-bg transition-colors cursor-pointer"
                        >
                          <LogOut className="w-3.5 h-3.5" />
                          <span>Cerrar Sesión</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* ========================================================= */
            /* MODO EXPANDIDO (Diseño Empresarial Serio para SIGAP)      */
            /* ========================================================= */
            <div className="flex flex-col h-full overflow-hidden">
              {/* 1. Cabecera Corporativa: Identificador SIGAP + Sede + Colapsar */}
              <div className="px-1.5 py-3 pb-2 relative shrink-0 border-b border-border-secondary" ref={dropdownRef}>
                <div className="flex items-center justify-between gap-2 p-2">
                  {/* Identidad Corporativa & Selector de Sede */}
                  <div className="flex items-center gap-1 min-w-0 flex-1">
                    <img src={logo} alt="Logo" className="h-auto w-10 object-cover" />

                    <div className="min-w-0 flex-1">
                      <div className="flex flex-col items-start leading-none">
                        <span className="font-special font-bold italic text-lg tracking-wide uppercase">
                          SIGAP
                        </span>
                        <span className="text-[10.5px] text-text-muted">
                          Parqueo Inteligente
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Botón Colapsar Barra Lateral */}
                  <button
                    type="button"
                    onClick={onToggleCollapse}
                    className="rounded-lg text-text-muted hover:text-text-primary hover:bg-bg-app transition-colors cursor-pointer shrink-0"
                    title="Colapsar barra lateral (⌘B)"
                  >
                    <PanelLeft className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* 2. Barra de Búsqueda Corporativa */}
              <div className="px-3 pt-4 pb-2">
                <div className="flex items-center w-full h-8 px-2.5 rounded-lg bg-bg-app border border-border-secondary text-xs text-text-muted transition-colors focus-within:border-border-strong hover:border-border-primary">
                  <Search className="w-3.5 h-3.5 text-text-muted mr-2 shrink-0" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="Buscar módulo o registro..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-transparent border-none outline-none text-xs text-text-primary placeholder:text-text-muted/60 p-0 font-normal"
                  />
                  <kbd className="font-mono text-[9px] text-text-muted bg-bg-surface px-1.5 py-0.5 rounded border border-border-secondary shrink-0 select-none">
                    ⌘K
                  </kbd>
                </div>
              </div>

              {/* 3. Navegación Principal y Módulos de Operación */}
              <div className="flex-1 overflow-y-auto px-3 py-1 space-y-2.5 scrollbar-thin">
                {/* Dashboard Principal */}
                <div className="space-y-0.5 pt-1">
                  <NavLink
                    to="/dashboard"
                    end
                    onClick={onClose}
                    className={({ isActive }) =>
                      `group flex items-center justify-between px-3 py-2.5 rounded-lg text-xs transition-all duration-150 cursor-pointer ${isActive
                        ? "bg-bg-accent/40 shadow-xs font-medium"
                        : "text-text-secondary hover:text-text-primary hover:bg-bg-accent/40"
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <div className="flex items-center gap-2.5 min-w-0">
                        <LayoutDashboard
                          className={`
                            w-4 h-4 shrink-0 transition-colors 
                            ${isActive ? "text-text-primary" : "text-text-muted group-hover:text-text-primary"}`
                          }
                        />
                        <span className="truncate">Dashboard</span>
                      </div>
                    )}
                  </NavLink>
                </div>

                {/* Categorías Acordeón */}
                {navSections.map((section, sIdx) => {
                  const isCollapsedSection = !!collapsedCategories[section.category];
                  const filteredItems = section.items.filter((item) =>
                    item.title.toLowerCase().includes(searchQuery.toLowerCase())
                  );

                  if (searchQuery && filteredItems.length === 0) return null;

                  return (
                    <div key={section.category || sIdx} className="space-y-0.5">
                      {/* Cabecera de Categoría */}
                      <button
                        type="button"
                        onClick={() => toggleCategory(section.category)}
                        className="w-full flex items-center justify-between px-2 pt-2 pb-1 text-[10px] font-special font-semibold uppercase tracking-wider text-text-muted hover:text-text-secondary transition-colors cursor-pointer text-left group"
                      >
                        <span className="truncate">{section.category}</span>
                        <ChevronDown
                          className={`
                            w-3 h-3 text-text-muted transition-transform duration-200 shrink-0 
                            ${isCollapsedSection ? "-rotate-90" : ""}`
                          }
                        />
                      </button>

                      {/* Lista de Enlaces */}
                      {!isCollapsedSection && (
                        <nav className="space-y-0.5 animate-in fade-in duration-100">
                          {filteredItems.map((item) => {
                            const Icon = item.icon;
                            return (
                              <NavLink
                                key={item.path}
                                to={item.path}
                                end={item.path === "/dashboard"}
                                onClick={onClose}
                                className={({ isActive }) =>
                                  `group flex items-center justify-between px-3 py-2.5 rounded-lg text-xs transition-all duration-150 cursor-pointer ${isActive
                                    ? "bg-bg-accent/40 shadow-xs font-medium"
                                    : "text-text-secondary hover:text-text-primary hover:bg-bg-accent/40"
                                  }`
                                }
                              >
                                {({ isActive }) => (
                                  <>
                                    <div className="flex items-center gap-2.5 min-w-0">
                                      <Icon
                                        className={`w-4 h-4 shrink-0 transition-colors ${isActive
                                          ? "text-text-primary"
                                          : "text-text-muted group-hover:text-text-primary"
                                          }`}
                                      />
                                      <span className="truncate">{item.title}</span>
                                    </div>
                                    {item.badge !== undefined && (
                                      <span className="px-1.5 py-0.2 text-[10px] font-mono rounded bg-bg-app text-text-muted border border-border-secondary">
                                        {item.badge}
                                      </span>
                                    )}
                                  </>
                                )}
                              </NavLink>
                            );
                          })}
                        </nav>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* 4. Tarjeta Inferior de Usuario (Sobria, sin fotos, con iniciales y rol) */}
              <div className="p-3 mt-auto border-t border-border-secondary relative" ref={userMenuRef}>
                <button
                  type="button"
                  onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                  className="w-full flex items-center justify-between gap-2.5 px-2.5 py-1.5 rounded-lg bg-bg-accent/40 border border-border-strong/60 transition-colors cursor-pointer text-left group shadow-xs"
                  title="Opciones de cuenta"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="relative w-7 h-7 rounded-lg flex items-center justify-center font-mono font-bold text-xs text-text-primary shrink-0 shadow-xs">
                      <img src={avatar1} alt="avatar" className="w-full h-full rounded-md" />
                      <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-status-success ring-2 ring-bg-surface" />
                    </div>

                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-text-primary truncate leading-tight font-sans">
                        {user?.username || "Administrador"}
                      </p>
                      <p className="text-[11px] text-text-muted truncate mt-0.5">
                        {getRoleDisplayName(role)}
                      </p>
                    </div>
                  </div>

                  <ChevronsUpDown className="w-3.5 h-3.5 text-text-muted group-hover:text-text-primary transition-colors shrink-0" />
                </button>

                {/* 5. Popover del Menú de Usuario */}
                {isUserMenuOpen && (
                  <div className="absolute left-2.5 right-2.5 bottom-full mb-1.5 z-50 bg-bg-surface-elevated border border-border-primary rounded-xl shadow-2xl p-1.5 space-y-1 animate-in fade-in zoom-in-95 duration-100">
                    {/* Header del Perfil en Popover: Configuración a la izquierda del perfil */}
                    <div className="flex items-center gap-2 p-2 border-b border-border-secondary">
                      {/* Información del Perfil (Avatar + Nombre + Rol) */}
                      <div className="flex items-center gap-2 min-w-0 flex-1">
                        <div className="w-7 h-7 rounded-lg flex items-center justify-center font-mono font-bold text-xs text-text-primary shrink-0">
                          <img src={avatar1} alt="avatar" className="w-full h-full rounded-full" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-text-primary truncate leading-tight">
                            {user?.username || "Administrador"}
                          </p>
                          <p className="text-[10px] text-text-muted truncate mt-0.5 font-mono">
                            {getRoleDisplayName(role)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Opciones del Menú */}
                    <div className=" space-y-0.5">
                      <button
                        type="button"
                        onClick={() => {
                          setIsUserMenuOpen(false);
                          onOpenProfile?.();
                        }}
                        className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg mb-1.5 text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-bg-app transition-colors cursor-pointer"
                      >
                        <User className="w-3.5 h-3.5 text-text-muted" />
                        <span>Configuración de la cuenta</span>
                      </button>

                      <div className="pt-1 border-t border-border-secondary">
                        <button
                          type="button"
                          onClick={() => {
                            setIsUserMenuOpen(false);
                            setShowLogoutModal(true);
                          }}
                          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-status-error hover:text-text-primary hover:bg-bg-accent/40 transition-colors cursor-pointer"
                        >
                          <LogOut className="w-3.5 h-3.5" />
                          <span>Cerrar Sesión</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* Modal de confirmación de cierre de sesión */}
      {showLogoutModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/45 backdrop-blur-xs animate-in fade-in duration-150"
          onClick={() => setShowLogoutModal(false)}
        >
          <div
            className="bg-bg-surface-elevated border border-border-secondary rounded-2xl p-6 sm:p-7 max-w-85 sm:max-w-90 w-full shadow-2xl flex flex-col items-center animate-in zoom-in-95 duration-150 select-none"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Ícono de usuario con alerta idéntico al diseño */}
            <div className="flex justify-center mb-3.5 text-text-primary">
              <svg
                className="w-10 h-10"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                {/* Círculo exterior */}
                <circle cx="12" cy="12" r="9.5" />
                {/* Cabeza */}
                <circle cx="12" cy="8.5" r="3" />
                {/* Silueta de hombros */}
                <path d="M6.8 17.5a5.5 5.5 0 0 1 10.4 0" />
                {/* Badge de alerta en esquina inferior izquierda */}
                <circle cx="6.5" cy="16.5" r="2.8" className="fill-[#1c1c1b] stroke-currentColor stroke-[1.4]" />
                <path d="M6.5 15.2v1.4" strokeWidth="1.4" />
                <circle cx="6.5" cy="17.7" r="0.4" fill="currentColor" />
              </svg>
            </div>

            {/* Título */}
            <h3 className="text-base sm:text-lg font-bold text-text-primary text-center mb-2 font-special tracking-tight">
              ¿Deseas cerrar sesión en tu cuenta?
            </h3>

            {/* Descripción adaptada */}
            <p className="text-xs sm:text-sm text-text-muted text-center leading-relaxed px-1 mb-6">
              Debes volver a iniciar sesión para acceder a todas las funcionalidades de SIGAP.
            </p>

            {/* Botón Confirmar */}
            <button
              type="button"
              onClick={() => {
                setShowLogoutModal(false);
                handleLogout();
              }}
              className="w-full py-2 px-4 rounded-lg bg-status-error-bg hover:bg-status-error-hover font-semibold text-sm transition-all duration-150 cursor-pointer shadow-xs active:scale-[0.99] mb-2.5"
            >
              Cerrar sesión
            </button>

            {/* Botón Cancelar */}
            <button
              type="button"
              onClick={() => setShowLogoutModal(false)}
              className="w-full py-2 px-4 rounded-lg bg-[#2a2a29] hover:bg-[#343433] border border-border-primary/60 font-semibold text-sm transition-all duration-150 cursor-pointer active:scale-[0.99]"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}
    </>
  );
}
