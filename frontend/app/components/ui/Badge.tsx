import React from "react";

export type BadgeVariant =
  | "primary"
  | "success"
  | "warning"
  | "danger"
  | "purple"
  | "neutral"
  | "cyan";

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: "sm" | "md";
  dot?: boolean;
  className?: string;
}

const VARIANTS: Record<BadgeVariant, string> = {
  primary: "bg-steel/12 text-steel border-steel/30",
  success: "bg-status-success-soft text-status-success border-status-success-border",
  warning: "bg-status-warning-soft text-status-warning border-status-warning-border",
  danger: "bg-status-error-soft text-status-error border-status-error-border",
  purple: "bg-text-primary/10 text-text-primary border-text-primary/20",
  cyan: "bg-text-secondary/8 text-text-secondary border-border-strong",
  neutral: "bg-bg-accent text-text-secondary border-border-primary",
};

const DOTS: Record<BadgeVariant, string> = {
  primary: "bg-steel",
  success: "bg-status-success",
  warning: "bg-status-warning",
  danger: "bg-status-error",
  purple: "bg-text-primary",
  cyan: "bg-text-secondary",
  neutral: "bg-text-muted",
};

const SIZES = {
  sm: "text-xs px-1.5 py-px",
  md: "text-xs px-2 py-0.5",
};

export function Badge({ children, variant = "neutral", size = "md", dot = false, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded font-medium border whitespace-nowrap ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full ${DOTS[variant]}`} />}
      {children}
    </span>
  );
}
