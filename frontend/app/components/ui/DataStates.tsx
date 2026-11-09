import React from "react";
import { ChevronLeft, ChevronRight, CircleAlert } from "lucide-react";
import { Button } from "./Button";

export function ErrorNotice({ message }: { message: string }) {
  return (
    <p
      role="alert"
      className="flex items-start gap-2 rounded-md border border-status-error-border bg-status-error-soft px-3 py-2 text-sm text-status-error"
    >
      <CircleAlert className="w-4 h-4 mt-px shrink-0" />
      <span>{message}</span>
    </p>
  );
}

export function PageLoading() {
  return (
    <div className="space-y-5" role="status" aria-label="Cargando">
      <div className="h-29 rounded-lg bg-bg-surface border border-border-primary animate-pulse" />
      <div className="h-56 rounded-lg bg-bg-surface border border-border-primary animate-pulse" />
    </div>
  );
}

export function EmptyRow({ colSpan, children }: { colSpan: number; children: React.ReactNode }) {
  return (
    <tr>
      <td colSpan={colSpan} className="text-center py-12! text-text-muted">
        {children}
      </td>
    </tr>
  );
}

export function EmptyPanel({ children }: { children: React.ReactNode }) {
  return <p className="px-5 py-12 text-center text-sm text-text-muted">{children}</p>;
}

export function TableCard({ children }: { children: React.ReactNode }) {
  return <div className="card overflow-x-auto">{children}</div>;
}

export function Pager({
  skip,
  limit,
  count,
  onChange,
}: {
  skip: number;
  limit: number;
  count: number;
  onChange: (skip: number) => void;
}) {
  if (count <= limit) return null;
  const last = Math.min(skip + limit, count);

  return (
    <div className="flex items-center justify-end gap-2 text-xs text-text-muted">
      <span className="tabular-nums mr-1">
        {skip + 1}-{last} de {count}
      </span>
      <Button variant="outline" size="sm" disabled={skip === 0} onClick={() => onChange(Math.max(0, skip - limit))} aria-label="Anterior">
        <ChevronLeft className="w-4 h-4" />
      </Button>
      <Button variant="outline" size="sm" disabled={last >= count} onClick={() => onChange(skip + limit)} aria-label="Siguiente">
        <ChevronRight className="w-4 h-4" />
      </Button>
    </div>
  );
}
