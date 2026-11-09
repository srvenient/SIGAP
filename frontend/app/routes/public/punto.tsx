import { CheckCircle2, CircleAlert, Loader2, OctagonX, ScanLine } from "lucide-react";
import { Navigate, useParams } from "react-router";
import { Brand } from "../../components/ui/Brand";
import { Plate } from "../../components/ui/Plate";
import { usePolling } from "../../hooks/usePolling";
import { publicApi } from "../../services/operations";
import type { Gate } from "../../types/operations";

const POLL_MS = 2000;

const GATES: Record<string, { gate: Gate; title: string; idle: string }> = {
  ingreso: { gate: "entry", title: "Ingreso", idle: "Acérquese despacio a la cámara" },
  salida: { gate: "exit", title: "Salida", idle: "Acérquese despacio a la cámara" },
};

const STATES = {
  idle: { icon: ScanLine, panel: "", tone: "text-text-muted" },
  validating: { icon: Loader2, panel: "", tone: "text-steel" },
  granted: { icon: CheckCircle2, panel: "bg-kiosk-granted", tone: "text-status-success" },
  denied: { icon: OctagonX, panel: "bg-kiosk-denied", tone: "text-status-error" },
  error: { icon: CircleAlert, panel: "bg-kiosk-alert", tone: "text-status-warning" },
};

export default function GatePoint() {
  const { gate: slug = "" } = useParams();
  const config = GATES[slug];

  if (!config) return <Navigate to="/punto/ingreso" replace />;
  return <GateScreen {...config} />;
}

function GateScreen({ gate, title, idle }: { gate: Gate; title: string; idle: string }) {
  const { data, error } = usePolling(() => publicApi.gateDisplay(gate), [gate], POLL_MS);

  const state = error ? "error" : (data?.display.state ?? "idle");
  const visual = STATES[state];
  const Icon = visual.icon;
  const message = error ? "Sistema sin conexión" : state === "idle" ? idle : data?.display.message;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="h-16 shrink-0 px-6 flex items-center justify-between border-b border-border-primary">
        <div className="flex items-center gap-5">
          <Brand subtitle={`Punto de ${title.toLowerCase()}`} />
        </div>
        {data && gate === "entry" && (
          <p className="text-lg font-medium tabular-nums">
            {data.occupancy.available === 0 ? "Sin cupos" : `${data.occupancy.available} cupos disponibles`}
          </p>
        )}
      </header>

      <main
        className={`flex-1 flex flex-col items-center justify-center gap-8 p-6 text-center transition-colors duration-200 ${visual.panel}`}
        aria-live="assertive"
      >
        <Icon
          className={`w-20 h-20 sm:w-24 sm:h-24 ${visual.tone} ${state === "validating" ? "animate-spin" : ""}`}
          strokeWidth={1.5}
        />
        {data?.display.plate && !error && <Plate value={data.display.plate} size="xl" />}
        <p className="text-4xl sm:text-6xl font-semibold tracking-tight max-w-4xl leading-tight">{message}</p>
      </main>
    </div>
  );
}
