import logo from "../../assets/png/logo.png";

/** Logo y nombre. La imagen trae margen transparente, por eso los márgenes negativos. */
export function Brand({ subtitle = "Gestión de parqueaderos" }: { subtitle?: string }) {
  return (
    <div className="flex items-center gap-2.5 min-w-0">
      <img src={logo} alt="" className="w-11 h-11 -m-1.5 object-contain shrink-0" />
      <div className="min-w-0 leading-tight">
        <p className="text-base font-semibold tracking-tight">SIGAP</p>
        <p className="text-xs text-text-muted truncate">{subtitle}</p>
      </div>
    </div>
  );
}
