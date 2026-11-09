import { useState } from "react";
import { ErrorNotice } from "../../components/ui/DataStates";
import { Input } from "../../components/ui/Input";
import { StatCard, StatGrid } from "../../components/ui/StatCard";
import { usePolling } from "../../hooks/usePolling";
import { PAYMENT_METHODS, VEHICLE_LABELS, money, todayLocal } from "../../lib/format";
import { reportsApi } from "../../services/operations";
import type { RevenueLine } from "../../types/operations";

export default function RevenuePage() {
  const [dateFrom, setDateFrom] = useState(todayLocal);
  const [dateTo, setDateTo] = useState(todayLocal);

  const { data, error } = usePolling(
    () => reportsApi.revenue({ date_from: dateFrom, date_to: dateTo }),
    [dateFrom, dateTo]
  );

  return (
    <div className="space-y-5">
      <div className="card p-4 flex flex-wrap gap-3">
        <div className="w-44">
          <Input label="Desde" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        </div>
        <div className="w-44">
          <Input label="Hasta" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        </div>
      </div>

      {error && <ErrorNotice message={error} />}

      {data && (
        <>
          <StatGrid columns={2}>
            <StatCard title="Recaudo del periodo" value={money(data.total)} />
            <StatCard title="Pagos registrados" value={data.count} />
          </StatGrid>

          <div className="grid gap-4 lg:grid-cols-2">
            <Breakdown title="Por tipo de vehículo" lines={data.by_vehicle_type} labels={VEHICLE_LABELS} />
            <Breakdown title="Por medio de pago" lines={data.by_payment_method} labels={PAYMENT_METHODS} />
          </div>
        </>
      )}
    </div>
  );
}

/** Una sola serie: barras de un mismo tono ordenadas por valor, con la cifra siempre visible. */
function Breakdown({
  title,
  lines,
  labels,
}: {
  title: string;
  lines: RevenueLine[];
  labels: Record<string, string>;
}) {
  const sorted = [...lines].sort((a, b) => b.total - a.total);
  const max = Math.max(...sorted.map((line) => line.total), 1);

  return (
    <section className="card p-5">
      <h2 className="text-sm font-semibold mb-4">{title}</h2>
      {sorted.length === 0 ? (
        <p className="text-sm text-text-muted">Sin pagos en este periodo.</p>
      ) : (
        <ul className="space-y-4">
          {sorted.map((line) => {
            const label = labels[line.key] ?? line.key;
            return (
              <li key={line.key} title={`${label}: ${money(line.total)} en ${line.count} pagos`}>
                <div className="flex items-baseline justify-between gap-3 text-sm">
                  <span className="font-medium">{label}</span>
                  <span className="tabular-nums">
                    {money(line.total)}{" "}
                    <span className="text-xs text-text-muted">
                      · {line.count} {line.count === 1 ? "pago" : "pagos"}
                    </span>
                  </span>
                </div>
                <div className="mt-2 h-2 rounded-sm bg-bg-accent">
                  <div
                    className="h-full bg-data rounded-sm min-w-1"
                    style={{ width: `${(line.total / max) * 100}%` }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
