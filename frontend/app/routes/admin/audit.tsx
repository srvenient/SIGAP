import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { Badge } from "../../components/ui/Badge";
import { EmptyRow, ErrorNotice, Pager, TableCard } from "../../components/ui/DataStates";
import { Input, Select } from "../../components/ui/Input";
import { usePolling } from "../../hooks/usePolling";
import { AUDIT_ACTIONS, dateTime } from "../../lib/format";
import { auditApi } from "../../services/operations";

const PAGE_SIZE = 25;
const EMPTY_FILTERS = { action: "", username: "", date_from: "", date_to: "", order: "desc" };
const ACTION_OPTIONS = [
  { value: "", label: "Todas las acciones" },
  ...Object.entries(AUDIT_ACTIONS).map(([value, label]) => ({ value, label })),
];

export default function AuditPage() {
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [skip, setSkip] = useState(0);
  const [expanded, setExpanded] = useState<string | null>(null);

  const { data, error } = usePolling(() => auditApi.search({ ...filters, skip, limit: PAGE_SIZE }), [filters, skip], 0);

  const update = (field: keyof typeof EMPTY_FILTERS, value: string) => {
    setFilters((current) => ({ ...current, [field]: value }));
    setSkip(0);
  };

  return (
    <div className="space-y-4">
      <div className="card p-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <Select label="Acción" value={filters.action} onChange={(e) => update("action", e.target.value)} options={ACTION_OPTIONS} />
        <Input label="Usuario" value={filters.username} onChange={(e) => update("username", e.target.value)} maxLength={80} />
        <Input label="Desde" type="date" value={filters.date_from} onChange={(e) => update("date_from", e.target.value)} />
        <Input label="Hasta" type="date" value={filters.date_to} onChange={(e) => update("date_to", e.target.value)} />
        <Select
          label="Orden"
          value={filters.order}
          onChange={(e) => update("order", e.target.value)}
          options={[
            { value: "desc", label: "Más recientes primero" },
            { value: "asc", label: "Más antiguos primero" },
          ]}
        />
      </div>

      {error && <ErrorNotice message={error} />}

      <TableCard>
        <table className="data-table">
          <thead>
            <tr>
              <th className="w-8" />
              <th>Fecha y hora</th>
              <th>Usuario</th>
              <th>Acción</th>
              <th>Elemento</th>
              <th>Resultado</th>
            </tr>
          </thead>
          <tbody>
            {data?.count === 0 && <EmptyRow colSpan={6}>No hay registros con esos filtros.</EmptyRow>}
            {data?.data.map((entry) => {
              const isOpen = expanded === entry.id;
              const hasDetail = Object.keys(entry.detail).length > 0;
              return (
                <Fragment key={entry.id}>
                  <tr
                    onClick={() => hasDetail && setExpanded(isOpen ? null : entry.id)}
                    className={hasDetail ? "cursor-pointer" : ""}
                  >
                    <td>
                      {hasDetail &&
                        (isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />)}
                    </td>
                    <td className="whitespace-nowrap text-xs">{dateTime(entry.created_at)}</td>
                    <td className="font-medium text-text-primary">{entry.actor_label}</td>
                    <td>{AUDIT_ACTIONS[entry.action] ?? entry.action}</td>
                    <td>{entry.entity_label ?? entry.entity_type}</td>
                    <td>
                      <Badge variant={entry.result === "success" ? "success" : "danger"}>
                        {entry.result === "success" ? "Exitoso" : "Fallido"}
                      </Badge>
                    </td>
                  </tr>
                  {isOpen && (
                    <tr>
                      <td />
                      <td colSpan={5}>
                        <pre className="text-xs font-mono whitespace-pre-wrap break-all">
                          {JSON.stringify(entry.detail, null, 2)}
                        </pre>
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </TableCard>
      {data && <Pager skip={skip} limit={PAGE_SIZE} count={data.count} onChange={setSkip} />}
    </div>
  );
}
