import { useEffect, useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router";
import { ShieldAlert } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { Sidebar } from "../components/layout/Sidebar";
import { Topbar } from "../components/layout/Topbar";
import { ProfileModal } from "../components/profile/ProfileModal";
import { canVisit } from "../lib/access";
import { PAGES } from "../lib/pages";

function AccessDenied() {
  return (
    <div className="max-w-sm mx-auto mt-16 text-center">
      <ShieldAlert className="w-8 h-8 mx-auto text-text-muted" />
      <h1 className="mt-4 text-lg font-semibold">No tienes acceso a esta sección</h1>
      <p className="mt-1.5 text-sm text-text-secondary">Tu rol no incluye esta función. Si la necesitas, pídesela al administrador.</p>
      <Link to="/dashboard" className="btn-primary mt-5">
        Volver al panel
      </Link>
    </div>
  );
}

export default function DashboardLayout() {
  const { user, isAuthenticated, isLoading, role } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("sigap_sidebar_collapsed") === "true";
    }
    return false;
  });
  const navigate = useNavigate();
  const location = useLocation();

  const handleToggleCollapse = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      if (typeof window !== "undefined") {
        localStorage.setItem("sigap_sidebar_collapsed", String(next));
      }
      return next;
    });
  };

  // Abrir modal de configuración automáticamente si se requiere cambio de contraseña
  useEffect(() => {
    if (!isLoading && isAuthenticated && user?.mustChangePassword) {
      setIsProfileOpen(true);
    }
  }, [isLoading, isAuthenticated, user?.mustChangePassword]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-7 h-7 border-2 border-border-strong border-t-steel rounded-full animate-spin" role="status" aria-label="Cargando" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const allowed = canVisit(location.pathname, role);
  const page = PAGES[location.pathname];

  return (
    <div className="min-h-screen flex flex-col">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isCollapsed={isCollapsed}
        onToggleCollapse={handleToggleCollapse}
        onOpenProfile={() => setIsProfileOpen(true)}
      />

      <div className={`${isCollapsed ? "lg:pl-15" : "lg:pl-64"} flex flex-col min-h-screen transition-[padding] duration-200`}>
        <Topbar onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} onOpenProfile={() => setIsProfileOpen(true)} />

        <main className="flex-1 w-full px-4 sm:px-6 lg:px-8 py-6">
          <div className="max-w-360 mx-auto">
            {allowed && page && (
              <header className="mb-5">
                <h1 className="text-xl font-semibold tracking-tight">{page.title}</h1>
                <p className="mt-0.5 text-sm text-text-muted">{page.description}</p>
              </header>
            )}
            {allowed ? <Outlet /> : <AccessDenied />}
          </div>
        </main>
      </div>

      <ProfileModal isOpen={isProfileOpen} onClose={() => setIsProfileOpen(false)} />
    </div>
  );
}
