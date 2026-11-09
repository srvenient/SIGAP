import type { Occupancy } from "../../types/operations";

const NEARLY_FULL = 85;

function capacityState(occupancy: Occupancy) {
  if (occupancy.available === 0) return { bar: "bg-status-error", text: "text-status-error", label: "Sin cupos disponibles" };
  const label = `${occupancy.available} cupos disponibles`;
  if (occupancy.percentage >= NEARLY_FULL) return { bar: "bg-status-warning", text: "text-status-warning", label };
  return { bar: "bg-data", text: "text-text-muted", label };
}

export function OccupancyCard({ occupancy }: { occupancy: Occupancy }) {
  const state = capacityState(occupancy);

  return (
    <div className="bg-bg-surface p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-text-secondary">Ocupación</p>
        <p className="text-sm tabular-nums text-text-secondary">{occupancy.percentage}%</p>
      </div>
      <p className="mt-2.5 text-3xl leading-none font-semibold tabular-nums tracking-tight">
        {occupancy.occupied}
        <span className="text-base font-normal text-text-muted"> / {occupancy.capacity}</span>
      </p>
      <div
        className="mt-3.5 h-1 rounded-full bg-bg-accent overflow-hidden"
        role="meter"
        aria-valuenow={occupancy.occupied}
        aria-valuemin={0}
        aria-valuemax={occupancy.capacity}
        aria-label="Cupos ocupados"
      >
        <div
          className={`h-full rounded-full transition-[width] duration-500 ${state.bar}`}
          style={{ width: `${Math.min(100, occupancy.percentage)}%` }}
        />
      </div>
      <p className={`mt-2 text-xs ${state.text}`}>{state.label}</p>
    </div>
  );
}
