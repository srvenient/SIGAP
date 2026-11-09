import React, { useEffect, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router";
import {
  Banknote,
  Car,
  ChevronsUpDown,
  Cpu,
  LayoutDashboard,
  LogOut,
  PanelLeft,
  PanelLeftOpen,
  ReceiptText,
  ScrollText,
  Search,
  Settings,
  Tags,
  TriangleAlert,
  User,
  Wrench,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { Brand } from "../ui/Brand";
import { Button } from "../ui/Button";
import { Modal } from "../ui/Modal";
import logo from "../../assets/png/logo.png";

interface NavItem {
  title: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavSection {
  category: string;
  items: NavItem[];
}

const PANEL: NavItem = { title: "Panel", path: "/dashboard", icon: LayoutDashboard };

const NAVIGATION: Record<string, NavSection[]> = {
  admin: [
    {
      category: "Operación",
      items: [
        { title: "Vehículos dentro", path: "/dashboard/vehicles", icon: Car },
        { title: "Alertas", path: "/dashboard/alerts", icon: TriangleAlert },
        { title: "Transacciones", path: "/dashboard/transactions", icon: ReceiptText },
        { title: "Recaudo", path: "/dashboard/revenue", icon: Banknote },
        { title: "Dispositivos", path: "/dashboard/devices", icon: Cpu },
      ],
    },
    {
      category: "Administración",
      items: [
        { title: "Tarifas", path: "/dashboard/tariffs", icon: Tags },
        { title: "Usuarios", path: "/dashboard/users", icon: User },
        { title: "Parqueadero", path: "/dashboard/settings", icon: Settings },
        { title: "Auditoría", path: "/dashboard/audit", icon: ScrollText },
      ],
    },
  ],
  operator: [
    {
      category: "Operación",
      items: [
        { title: "Alertas", path: "/dashboard/alerts", icon: TriangleAlert },
        { title: "Vehículos dentro", path: "/dashboard/vehicles", icon: Car },
        { title: "Tickets técnicos", path: "/dashboard/tickets", icon: Wrench },
      ],
    },
  ],
  support: [
    {
      category: "Soporte",
      items: [
        { title: "Dispositivos", path: "/dashboard/devices", icon: Cpu },
        { title: "Tickets técnicos", path: "/dashboard/tickets", icon: Wrench },
      ],
    },
  ],
};

const ROLE_NAMES: Record<string, string> = {
  admin: "Administrador",
  operator: "Operador",
  support: "Soporte Técnico",
};

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
  onOpenProfile?: () => void;
}

function NavRow({ item, compact, onNavigate }: { item: NavItem; compact: boolean; onNavigate?: () => void }) {
  const Icon = item.icon;

  return (
    <NavLink
      to={item.path}
      end={item.path === PANEL.path}
      onClick={onNavigate}
      title={compact ? item.title : undefined}
      className={({ isActive }) =>
        `flex items-center gap-2.5 rounded-md text-sm transition-colors ${
          compact ? "w-9 h-9 justify-center" : "h-8.5 px-2.5"
        } ${
          isActive
            ? "bg-bg-accent text-text-primary font-medium"
            : "text-text-secondary hover:text-text-primary hover:bg-bg-accent/60"
        }`
      }
    >
      <Icon className="w-4 h-4 shrink-0" />
      {!compact && <span className="truncate">{item.title}</span>}
    </NavLink>
  );
}

export function Sidebar({ isOpen, onClose, isCollapsed = false, onToggleCollapse, onOpenProfile }: SidebarProps) {
  const { user, role, logout } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [showLogoutModal, setShowLogoutModal] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const userMenuRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // El panel desplegado en móvil siempre se muestra completo
  const compact = isCollapsed && !isOpen;

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsUserMenuOpen(false);

      const key = event.key.toLowerCase();
      if ((event.metaKey || event.ctrlKey) && key === "b") {
        event.preventDefault();
        onToggleCollapse?.();
      }
      if ((event.metaKey || event.ctrlKey) && (key === "k" || key === "f")) {
        event.preventDefault();
        if (isCollapsed) onToggleCollapse?.();
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

  const query = searchQuery.trim().toLowerCase();
  const matches = (item: NavItem) => item.title.toLowerCase().includes(query);
  const sections = (NAVIGATION[role ?? ""] ?? [])
    .map((section) => ({ ...section, items: section.items.filter(matches) }))
    .filter((section) => section.items.length > 0);
  const nothingFound = query !== "" && sections.length === 0 && !matches(PANEL);

  const roleName = ROLE_NAMES[role ?? ""] ?? "Usuario del sistema";
  const displayName = user?.fullName || user?.username || roleName;
  const initials = displayName.slice(0, 2).toUpperCase();

  const handleLogout = async () => {
    setShowLogoutModal(false);
    toast("Se cerró la sesión con éxito", "success", "Sesión finalizada");
    await logout();
    navigate("/");
  };

  const expandAndSearch = () => {
    onToggleCollapse?.();
    setTimeout(() => searchInputRef.current?.focus(), 150);
  };

  return (
    <>
      {isOpen && <div className="fixed inset-0 bg-black/60 z-40 lg:hidden" onClick={onClose} />}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 ${compact ? "w-15" : "w-64"} bg-bg-sidebar border-r border-border-primary flex flex-col transition-[width,translate] duration-200 lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className={`h-14 shrink-0 flex items-center border-b border-border-primary ${compact ? "justify-center" : "justify-between gap-2 pl-4 pr-3"}`}>
          {compact ? (
            <button
              type="button"
              onClick={onToggleCollapse}
              className="group relative w-9 h-9 flex items-center justify-center rounded-md hover:bg-bg-accent text-text-secondary cursor-pointer"
              title="Expandir barra lateral (Ctrl+B)"
              aria-label="Expandir barra lateral"
            >
              <img src={logo} alt="" className="w-11 h-11 max-w-none object-contain group-hover:hidden" />
              <PanelLeftOpen className="w-4 h-4 hidden group-hover:block" />
            </button>
          ) : (
            <>
              <Brand />
              <button
                type="button"
                onClick={onToggleCollapse}
                className="hidden lg:flex w-7 h-7 items-center justify-center rounded-md text-text-muted hover:text-text-primary hover:bg-bg-accent cursor-pointer shrink-0"
                title="Colapsar barra lateral (Ctrl+B)"
                aria-label="Colapsar barra lateral"
              >
                <PanelLeft className="w-4 h-4" />
              </button>
            </>
          )}
        </div>

        <div className={`shrink-0 pt-3 pb-1 ${compact ? "flex justify-center" : "px-3"}`}>
          {compact ? (
            <button
              type="button"
              onClick={expandAndSearch}
              className="w-9 h-9 flex items-center justify-center rounded-md text-text-muted hover:text-text-primary hover:bg-bg-accent cursor-pointer"
              title="Buscar sección (Ctrl+K)"
              aria-label="Buscar sección"
            >
              <Search className="w-4 h-4" />
            </button>
          ) : (
            <div className="flex items-center h-8 px-2.5 rounded-md bg-bg-field border border-border-primary focus-within:border-border-strong transition-colors">
              <Search className="w-3.5 h-3.5 text-text-muted mr-2 shrink-0" />
              <input
                ref={searchInputRef}
                type="text"
                aria-label="Buscar sección"
                placeholder="Buscar sección"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-transparent outline-none text-sm text-text-primary placeholder:text-text-muted"
              />
              <kbd className="ml-1 text-[11px] text-text-muted whitespace-nowrap font-sans">Ctrl K</kbd>
            </div>
          )}
        </div>

        <nav className={`flex-1 overflow-y-auto py-2 ${compact ? "flex flex-col items-center gap-0.5" : "px-3"}`} aria-label="Principal">
          {matches(PANEL) && <NavRow item={PANEL} compact={compact} onNavigate={onClose} />}

          {sections.map((section) =>
            compact ? (
              <React.Fragment key={section.category}>
                <div className="w-5 h-px bg-border-primary my-2" />
                {section.items.map((item) => (
                  <NavRow key={item.path} item={item} compact onNavigate={onClose} />
                ))}
              </React.Fragment>
            ) : (
              <div key={section.category} className="mt-5">
                <p className="px-2.5 mb-1 text-xs text-text-muted">{section.category}</p>
                <div className="space-y-0.5">
                  {section.items.map((item) => (
                    <NavRow key={item.path} item={item} compact={false} onNavigate={onClose} />
                  ))}
                </div>
              </div>
            )
          )}

          {nothingFound && <p className="px-2.5 py-3 text-xs text-text-muted">Sin resultados</p>}
        </nav>

        <div ref={userMenuRef} className={`relative shrink-0 border-t border-border-primary p-2 ${compact ? "flex justify-center" : ""}`}>
          <button
            type="button"
            onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
            className={`flex items-center gap-2.5 rounded-md hover:bg-bg-accent/60 transition-colors cursor-pointer text-left ${
              compact ? "p-1.5" : "w-full px-2 py-1.5"
            }`}
            title={compact ? `${displayName} · ${roleName}` : "Opciones de cuenta"}
            aria-haspopup="menu"
            aria-expanded={isUserMenuOpen}
          >
            <span className="w-7 h-7 rounded-full bg-bg-accent border border-border-strong flex items-center justify-center text-xs font-medium shrink-0">
              {initials}
            </span>
            {!compact && (
              <>
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium truncate leading-tight">{displayName}</span>
                  <span className="block text-xs text-text-muted truncate leading-tight mt-0.5">{roleName}</span>
                </span>
                <ChevronsUpDown className="w-3.5 h-3.5 text-text-muted shrink-0" />
              </>
            )}
          </button>

          {isUserMenuOpen && (
            <div
              role="menu"
              className={`absolute z-50 bg-bg-surface-elevated border border-border-primary rounded-lg shadow-xl shadow-black/40 p-1 ${
                compact ? "left-14 bottom-2 w-56" : "left-2 right-2 bottom-full mb-1"
              }`}
            >
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setIsUserMenuOpen(false);
                  onOpenProfile?.();
                }}
                className="w-full flex items-center gap-2 px-2.5 h-8 rounded text-sm text-text-secondary hover:text-text-primary hover:bg-bg-accent cursor-pointer"
              >
                <User className="w-3.5 h-3.5" />
                Configuración de la cuenta
              </button>
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setIsUserMenuOpen(false);
                  setShowLogoutModal(true);
                }}
                className="w-full flex items-center gap-2 px-2.5 h-8 rounded text-sm text-status-error hover:bg-status-error-soft cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                Cerrar sesión
              </button>
            </div>
          )}
        </div>
      </aside>

      <Modal
        isOpen={showLogoutModal}
        onClose={() => setShowLogoutModal(false)}
        title="Cerrar sesión"
        maxWidth="sm"
        footer={
          <>
            <Button variant="ghost" onClick={() => setShowLogoutModal(false)}>
              Cancelar
            </Button>
            <Button variant="danger" onClick={handleLogout}>
              Cerrar sesión
            </Button>
          </>
        }
      >
        <p className="text-sm text-text-secondary">Tendrás que volver a iniciar sesión para usar SIGAP.</p>
      </Modal>
    </>
  );
}
