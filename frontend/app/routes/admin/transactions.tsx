import { useEffect, useState } from "react";
import { Badge } from "../../components/ui/Badge";
import { EmptyRow, ErrorNotice, Pager, TableCard } from "../../components/ui/DataStates";
import { Input, Select } from "../../components/ui/Input";
import { Modal } from "../../components/ui/Modal";
import { Plate } from "../../components/ui/Plate";
import { usePolling } from "../../hooks/usePolling";
import {
  PAYMENT_METHODS,
  PAYMENT_STATUS,
  TRANSACTION_STATUS,
  VEHICLE_LABELS,
  dateTime,
  duration,
  money,
} from "../../lib/format";
import { ApiError } from "../../services/api";
import { transactionsApi } from "../../services/operations";
import type { TransactionDetail } from "../../types/operations";

const PAGE_SIZE = 25;
const EMPTY_FILTERS = { plate: "", vehicle_type: "", status: "", date_from: "", date_to: "" };

export default function TransactionsPage() {
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [skip, setSkip] = useState(0);
  const [openId, setOpenId] = useState<string | null>(null);

  const { data, error } = usePolling(
    () => transactionsApi.search({ ...filters, skip, limit: PAGE_SIZE }),
    [filters, skip],
    0
  );

  const update = (field: keyof typeof EMPTY_FILTERS, value: string) => {
    setFilters((current) => ({ ...current, [field]: value }));
    setSkip(0);
  };

  return (
    <div className="space-y-4">
      <div className="card p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Input label="Placa" value={filters.plate} onChange={(e) => update("plate", e.target.value.toUpperCase())} maxLength={7} />
        <Select
          label="Tipo de vehículo"
          value={filters.vehicle_type}
          onChange={(e) => update("vehicle_type", e.target.value)}
          options={[
            { value: "", label: "Todos" },
            { value: "car", label: "Carro" },
            { value: "motorcycle", label: "Moto" },
          ]}
        />
        <Select
          label="Estado"
          value={filters.status}
          onChange={(e) => update("status", e.target.value)}
          options={[
            { value: "", label: "Todos" },
            ...Object.entries(TRANSACTION_STATUS).map(([value, { label }]) => ({ value, label })),
          ]}
        />
        <Input label="Desde" type="date" value={filters.date_from} onChange={(e) => update("date_from", e.target.value)} />
        <Input label="Hasta" type="date" value={filters.date_to} onChange={(e) => update("date_to", e.target.value)} />
      </div>

      {error && <ErrorNotice message={error} />}

      <TableCard>
        <table className="data-table">
          <thead>
            <tr>
              <th>Placa</th>
              <th>Tipo</th>
              <th>Ingreso</th>
              <th>Salida</th>
              <th className="text-right!">Valor</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {data?.count === 0 && <EmptyRow colSpan={6}>No hay transacciones con esos filtros.</EmptyRow>}
            {data?.data.map((transaction) => (
              <tr key={transaction.id} onClick={() => setOpenId(transaction.id)} className="cursor-pointer">
                <td>
                  <Plate value={transaction.plate} />
                  {transaction.manual_intervention && (
                    <Badge size="sm" className="ml-2">
                      Manual
                    </Badge>
                  )}
                </td>
                <td>{VEHICLE_LABELS[transaction.vehicle_type]}</td>
                <td className="whitespace-nowrap">{dateTime(transaction.entry_time)}</td>
                <td className="whitespace-nowrap">{dateTime(transaction.exit_time)}</td>
                <td className="text-right tabular-nums text-text-primary">{money(transaction.total_amount)}</td>
                <td>
                  <Badge variant={TRANSACTION_STATUS[transaction.status].variant}>
                    {TRANSACTION_STATUS[transaction.status].label}
                  </Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableCard>
      {data && <Pager skip={skip} limit={PAGE_SIZE} count={data.count} onChange={setSkip} />}

      {openId && <DetailModal transactionId={openId} onClose={() => setOpenId(null)} />}
    </div>
  );
}

function DetailModal({ transactionId, onClose }: { transactionId: string; onClose: () => void }) {
  const [detail, setDetail] = useState<TransactionDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    transactionsApi
      .detail(transactionId)
      .then(setDetail)
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el detalle"));
  }, [transactionId]);

  const rows: [string, string][] = detail
    ? [
        ["Tipo de vehículo", VEHICLE_LABELS[detail.vehicle_type]],
        ["Ingreso", dateTime(detail.entry_time)],
        ["Salida", dateTime(detail.exit_time)],
        ["Tiempo liquidado", detail.billed_minutes ? duration(detail.billed_minutes) : "-"],
        ["Valor liquidado", money(detail.total_amount)],
        ["Medio de pago", detail.payment_method ? (PAYMENT_METHODS[detail.payment_method] ?? detail.payment_method) : "-"],
        ["Fecha de pago", dateTime(detail.paid_at)],
        ["Intervención manual", detail.manual_intervention ? (detail.manual_reason ?? "Sí") : "No"],
      ]
    : [];

  return (
    <Modal isOpen onClose={onClose} title={detail ? <Plate value={detail.plate} size="md" /> : "Transacción"} maxWidth="xl">
      {error && <ErrorNotice message={error} />}
      {detail && (
        <div className="space-y-5 text-sm">
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            {rows.map(([term, value]) => (
              <div key={term}>
                <dt className="text-xs font-medium text-text-muted">{term}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>

          {detail.payment_attempts.length > 0 && (
            <section>
              <h3 className="text-xs font-medium text-text-muted mb-2">Intentos de pago</h3>
              <ul className="divide-y divide-border-secondary border-y border-border-secondary">
                {detail.payment_attempts.map((attempt) => (
                  <li key={attempt.id} className="py-2 flex flex-wrap items-center gap-x-3 gap-y-1">
                    <Badge variant={PAYMENT_STATUS[attempt.status].variant}>{PAYMENT_STATUS[attempt.status].label}</Badge>
                    <span>{PAYMENT_METHODS[attempt.method] ?? attempt.method}</span>
                    <span className="tabular-nums">{money(attempt.amount)}</span>
                    {attempt.failure_reason && <span className="text-text-secondary">{attempt.failure_reason}</span>}
                    <span className="ml-auto text-xs text-text-muted">{dateTime(attempt.created_at)}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}
    </Modal>
  );
}
