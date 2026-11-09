import React from "react";

const FIELD =
  "w-full rounded-md bg-bg-field border text-text-primary placeholder:text-text-disabled text-sm h-9 transition-colors outline-none";
const FIELD_STATE = {
  normal: "border-border-primary hover:border-border-strong focus:border-steel focus:ring-3 focus:ring-primary-muted",
  error: "border-status-error focus:ring-3 focus:ring-status-error-soft",
};
const LABEL = "block text-[13px] font-medium text-text-secondary mb-1.5";

function Hint({ error, helperText }: { error?: string; helperText?: string }) {
  if (error) return <p className="mt-1.5 text-xs text-status-error font-semibold">{error}</p>;
  if (helperText) return <p className="mt-1.5 text-xs text-text-muted">{helperText}</p>;
  return null;
}

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export function Input({ label, error, helperText, leftIcon, rightIcon, className = "", id, ...props }: InputProps) {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className={LABEL}>
          {label}
        </label>
      )}
      <div className="relative">
        {leftIcon && (
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
            {leftIcon}
          </div>
        )}
        <input
          id={inputId}
          className={`${FIELD} ${leftIcon ? "pl-9" : "pl-3"} ${rightIcon ? "pr-9" : "pr-3"} ${
            error ? FIELD_STATE.error : FIELD_STATE.normal
          } ${className}`}
          {...props}
        />
        {rightIcon && <div className="absolute inset-y-0 right-0 pr-3 flex items-center text-text-muted">{rightIcon}</div>}
      </div>
      <Hint error={error} helperText={helperText} />
    </div>
  );
}

interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: { value: string; label: string }[];
}

export function Select({ label, error, helperText, options, className = "", id, ...props }: SelectProps) {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={selectId} className={LABEL}>
          {label}
        </label>
      )}
      <div className="relative">
        <select
          id={selectId}
          className={`${FIELD} px-3 pr-8 appearance-none cursor-pointer ${
            error ? FIELD_STATE.error : FIELD_STATE.normal
          } ${className}`}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-text-muted">
          <svg className="w-4 h-4 fill-current" viewBox="0 0 20 20" aria-hidden="true">
            <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
          </svg>
        </div>
      </div>
      <Hint error={error} helperText={helperText} />
    </div>
  );
}

export function Textarea({
  label,
  error,
  id,
  className = "",
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string; error?: string }) {
  const fieldId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={fieldId} className={LABEL}>
          {label}
        </label>
      )}
      <textarea
        id={fieldId}
        rows={3}
        className={`${FIELD} h-auto! py-2 px-3 ${error ? FIELD_STATE.error : FIELD_STATE.normal} ${className}`}
        {...props}
      />
      <Hint error={error} />
    </div>
  );
}
