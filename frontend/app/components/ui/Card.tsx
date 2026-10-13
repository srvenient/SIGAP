import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glow?: boolean;
}

export function Card({ children, className = "", glow = false }: CardProps) {
  return (
    <div
      className={`relative rounded-xl bg-bg-surface border border-border-primary transition-all duration-200 shadow-xs ${
        glow
          ? "hover:border-border-strong hover:shadow-md"
          : "hover:border-border-strong/70"
      } ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  subtitle,
  action,
  className = "",
}: {
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`px-5 py-4 border-b border-border-secondary flex items-center justify-between gap-4 ${className}`}
    >
      <div>
        <h3 className="text-sm font-semibold text-text-primary font-special tracking-tight">{title}</h3>
        {subtitle && <p className="text-xs text-text-muted mt-0.5 font-sans">{subtitle}</p>}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

export function CardContent({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`p-5 text-text-primary ${className}`}>{children}</div>;
}

