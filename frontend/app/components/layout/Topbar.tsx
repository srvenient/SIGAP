import { useEffect, useState } from "react";
import { useLocation } from "react-router";
import { ChevronRight, Menu, Settings } from "lucide-react";
import { clock } from "../../lib/format";
import { PAGES } from "../../lib/pages";

const CLOCK_REFRESH_MS = 15_000;

export interface TopbarProps {
  onToggleSidebar: () => void;
  onOpenProfile?: () => void;
}

export function Topbar({ onToggleSidebar, onOpenProfile }: TopbarProps) {
  const { pathname } = useLocation();
  const page = PAGES[pathname];
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), CLOCK_REFRESH_MS);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="sticky top-0 z-30 h-14 px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-3 bg-bg-app/85 backdrop-blur border-b border-border-primary">
      <div className="flex items-center gap-2 min-w-0 text-sm">
        <button
          onClick={onToggleSidebar}
          className="lg:hidden -ml-1 mr-1 p-1.5 text-text-secondary hover:text-text-primary cursor-pointer"
          aria-label="Abrir menú"
        >
          <Menu className="w-5 h-5" />
        </button>
        {page?.section && (
          <>
            <span className="text-text-muted hidden sm:inline">{page.section}</span>
            <ChevronRight className="w-3.5 h-3.5 text-text-disabled hidden sm:block" />
          </>
        )}
        <span className="font-medium truncate">{page?.title ?? "SIGAP"}</span>
      </div>

      <div className="flex items-center gap-3">
        <time className="hidden sm:block text-xs text-text-muted tabular-nums">{clock(now)}</time>
        <button
          onClick={onOpenProfile}
          className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-text-primary rounded-md hover:bg-bg-accent transition-colors cursor-pointer"
          aria-label="Configuración de la cuenta"
          title="Configuración de la cuenta"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
}
