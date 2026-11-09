import React from "react";
import { Loader2 } from "lucide-react";

export type ButtonVariant =
  | "primary"
  | "secondary"
  | "outline"
  | "ghost"
  | "danger"
  | "success";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const BASE =
  "inline-flex items-center justify-center font-medium transition-colors duration-150 rounded-md disabled:opacity-45 disabled:cursor-not-allowed cursor-pointer select-none";

const SIZES = {
  sm: "text-xs h-7.5 px-2.5 gap-1.5",
  md: "text-sm h-9 px-3.5 gap-2",
  lg: "text-base h-11 px-5 gap-2.5",
};

const VARIANTS: Record<ButtonVariant, string> = {
  primary: "bg-primary-DEFAULT hover:bg-primary-hover active:bg-primary-active text-on-primary",
  secondary: "bg-bg-accent hover:bg-border-primary text-text-primary border border-border-primary",
  outline: "bg-transparent hover:bg-bg-accent text-text-primary border border-border-strong",
  ghost: "bg-transparent hover:bg-bg-accent text-text-secondary hover:text-text-primary",
  danger: "bg-status-error-bg hover:bg-status-error-hover text-white",
  success: "bg-status-success-bg hover:bg-status-success-hover text-white",
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  leftIcon,
  rightIcon,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={`${BASE} ${SIZES[size]} ${VARIANTS[variant]} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : (
        leftIcon && <span className="shrink-0">{leftIcon}</span>
      )}
      <span>{children}</span>
      {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
    </button>
  );
}
