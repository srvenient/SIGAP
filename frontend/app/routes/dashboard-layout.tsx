import React, { useState, useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router";
import { useAuth } from "../context/AuthContext";
import { Sidebar } from "../components/layout/Sidebar";
import { Topbar } from "../components/layout/Topbar";
import { ProfileModal } from "../components/profile/ProfileModal";

const ADMIN_EXCLUSIVE_ROUTES = [
  "/dashboard/tariffs",
  "/dashboard/users",
  "/dashboard/transactions",
  "/dashboard/audit",
];

export default function DashboardLayout() {
  const { isAuthenticated, isLoading, role } = useAuth();
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

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  useEffect(() => {
    if (isLoading || !isAuthenticated || !role) return;

    const path = location.pathname;

    if (role === "operator" && (ADMIN_EXCLUSIVE_ROUTES.includes(path) || path.includes("/support-tickets"))) {
      navigate("/unauthorized", { replace: true });
    }

    if (role === "support" && (ADMIN_EXCLUSIVE_ROUTES.includes(path) || path.includes("/manual-entry"))) {
      navigate("/unauthorized", { replace: true });
    }
  }, [role, location.pathname, isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg-app">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-primary-DEFAULT/30 border-t-primary-DEFAULT rounded-full animate-spin" />
          <p className="text-xs font-mono text-text-muted font-medium tracking-wide">
            CARGANDO ENTORNO SIGAP...
          </p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col font-sans bg-bg-app selection:bg-primary-muted selection:text-text-primary">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        isCollapsed={isCollapsed}
        onToggleCollapse={handleToggleCollapse}
        onOpenProfile={() => setIsProfileOpen(true)}
      />

      <div className={`
        ${isCollapsed ? "lg:pl-17" : "lg:pl-64"} 
        flex flex-col min-h-screen relative z-10 
        transition-all duration-300 ease-in-out`
      }>
        <Topbar
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onOpenProfile={() => setIsProfileOpen(true)}
        />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 w-full -mt-5.5">
          <Outlet />
        </main>
      </div>

      <ProfileModal
        isOpen={isProfileOpen}
        onClose={() => setIsProfileOpen(false)}
      />
    </div>
  );
}
