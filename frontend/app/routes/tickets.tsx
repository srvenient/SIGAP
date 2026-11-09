import { useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { EmptyRow, ErrorNotice, Pager, TableCard } from "../components/ui/DataStates";
import { Input, Select, Textarea } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { usePolling } from "../hooks/usePolling";
import { TICKET_STATUS, dateTime } from "../lib/format";
import { ApiError } from "../services/api";
import { ticketsApi, transactionsApi } from "../services/operations";
import type { TicketDetail, Transaction } from "../types/operations";

const PAGE_SIZE = 20;
const STATUS_OPTIONS = [
  { value: "", label: "Todos los estados" },
  ...Object.entries(TICKET_STATUS).map(([value, { label }]) => ({ value, label })),
];

export default function TicketsPage() {
  const { role } = useAuth();
  const [status, setStatus] = useState("");
  const [skip, setSkip] = useState(0);
  const [creating, setCreating] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);

  const { data, error, reload } = usePolling(
    () => ticketsApi.search({ status, skip, limit: PAGE_SIZE }),
    [status, skip]
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="w-56">
          <Select
            label="Estado"
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setSkip(0);
            }}
            options={STATUS_OPTIONS}
          />
        </div>
        {role === "operator" && (
          <Button leftIcon={<Plus className="w-4 h-4" />} onClick={() => setCreating(true)}>
            Crear ticket
          </Button>
        )}
      </div>

      {error && <ErrorNotice message={error} />}

      <TableCard>
        <table className="data-table">
          <thead>
            <tr>
              <th>Creado</th>
              <th>Componente</th>
              <th>Descripción</th>
              <th>Origen</th>
              <th>Responsable</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {data?.count === 0 && <EmptyRow colSpan={6}>No hay tickets.</EmptyRow>}
            {data?.data.map((ticket) => (
              <tr key={ticket.id} onClick={() => setOpenId(ticket.id)} className="cursor-pointer">
                <td className="whitespace-nowrap">{dateTime(ticket.created_at)}</td>
                <td className="font-medium text-text-primary">{ticket.component}</td>
                <td className="max-w-xs truncate">{ticket.description}</td>
                <td>{ticket.origin === "automatic" ? "Automático" : ticket.created_by_username}</td>
                <td>{ticket.assignee_username ?? "-"}</td>
                <td>
                  <Badge variant={TICKET_STATUS[ticket.status].variant}>{TICKET_STATUS[ticket.status].label}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableCard>
      {data && <Pager skip={skip} limit={PAGE_SIZE} count={data.count} onChange={setSkip} />}

      {creating && (
        <CreateTicketModal
          onClose={() => setCreating(false)}
          onCreated={() => {
            setCreating(false);
            void reload();
          }}
        />
      )}
      {openId && (
        <TicketModal
          ticketId={openId}
          canManage={role === "support"}
          onClose={() => setOpenId(null)}
          onChanged={() => void reload()}
        />
      )}
    </div>
  );
}

function CreateTicketModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const { toast } = useToast();
  const [component, setComponent] = useState("");
  const [description, setDescription] = useState("");
  const [transactionId, setTransactionId] = useState("");
  const [vehicles, setVehicles] = useState<Transaction[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    transactionsApi.inside().then(setVehicles).catch(() => setVehicles([]));
  }, []);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await ticketsApi.create({ component, description, transaction_id: transactionId || undefined });
      toast("Ticket creado y asignado a Soporte técnico", "success");
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo crear el ticket");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Crear ticket técnico"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={save} isLoading={saving} disabled={component.trim().length < 2 || description.trim().length < 5}>
            Crear
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <Input label="Componente o proceso afectado" value={component} onChange={(e) => setComponent(e.target.value)} maxLength={80} autoFocus />
        <Textarea label="Descripción del problema" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={1000} />
        <Select
          label="Transacción relacionada (opcional)"
          value={transactionId}
          onChange={(e) => setTransactionId(e.target.value)}
          options={[{ value: "", label: "Ninguna" }, ...vehicles.map((v) => ({ value: v.id, label: v.plate }))]}
        />
        {error && <ErrorNotice message={error} />}
      </div>
    </Modal>
  );
}

function TicketModal({
  ticketId,
  canManage,
  onClose,
  onChanged,
}: {
  ticketId: string;
  canManage: boolean;
  onClose: () => void;
  onChanged: () => void;
}) {
  const { toast } = useToast();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [diagnosis, setDiagnosis] = useState("");
  const [actions, setActions] = useState("");
  const [result, setResult] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const load = async () => {
    const detail = await ticketsApi.detail(ticketId);
    setTicket(detail);
    setDiagnosis(detail.diagnosis ?? "");
    setActions(detail.actions_taken ?? "");
    setResult(detail.result ?? "");
  };

  useEffect(() => {
    load().catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar el ticket"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ticketId]);

  const act = async (action: () => Promise<unknown>, success: string) => {
    setSaving(true);
    setError(null);
    try {
      await action();
      await load();
      onChanged();
      toast(success, "success");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo completar la acción");
    } finally {
      setSaving(false);
    }
  };

  const close = (status: "solved" | "not_solved", label: string) =>
    act(() => ticketsApi.close(ticketId, { status, diagnosis, actions_taken: actions, result }), label);

  const canClose = diagnosis.trim().length >= 3 && actions.trim().length >= 3 && result.trim().length >= 3;
  const inReview = ticket?.status === "in_review";
  const takeable = ticket?.status === "pending" || ticket?.status === "not_solved";

  return (
    <Modal isOpen onClose={onClose} title={ticket?.component ?? "Ticket"} maxWidth="xl">
      {ticket && (
        <div className="space-y-5 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={TICKET_STATUS[ticket.status].variant}>{TICKET_STATUS[ticket.status].label}</Badge>
            {ticket.error_code && <span className="font-mono text-xs text-text-muted">{ticket.error_code}</span>}
          </div>
          <p className="text-text-secondary">{ticket.description}</p>

          {canManage && inReview ? (
            <div className="space-y-3">
              <Textarea label="Diagnóstico" value={diagnosis} onChange={(e) => setDiagnosis(e.target.value)} />
              <Textarea label="Acciones realizadas" value={actions} onChange={(e) => setActions(e.target.value)} />
              <Textarea label="Resultado" value={result} onChange={(e) => setResult(e.target.value)} />
            </div>
          ) : (
            (ticket.diagnosis || ticket.actions_taken || ticket.result) && (
              <dl className="space-y-2">
                {[
                  ["Diagnóstico", ticket.diagnosis],
                  ["Acciones realizadas", ticket.actions_taken],
                  ["Resultado", ticket.result],
                ].map(([term, value]) => (
                  <div key={term}>
                    <dt className="text-xs font-medium text-text-muted">{term}</dt>
                    <dd>{value || "-"}</dd>
                  </div>
                ))}
              </dl>
            )
          )}

          {error && <ErrorNotice message={error} />}

          {canManage && (takeable || inReview) && (
            <div className="flex flex-wrap gap-2">
              {takeable && (
                <Button isLoading={saving} onClick={() => act(() => ticketsApi.take(ticketId), "Ticket en revisión")}>
                  Tomar ticket
                </Button>
              )}
              {inReview && (
                <>
                  <Button
                    variant="outline"
                    disabled={saving}
                    onClick={() =>
                      act(
                        () => ticketsApi.saveNotes(ticketId, { diagnosis, actions_taken: actions, result }),
                        "Avance guardado"
                      )
                    }
                  >
                    Guardar avance
                  </Button>
                  <Button variant="success" disabled={saving || !canClose} onClick={() => close("solved", "Ticket solucionado")}>
                    Solucionado
                  </Button>
                  <Button variant="danger" disabled={saving || !canClose} onClick={() => close("not_solved", "Ticket no solucionado")}>
                    No solucionado
                  </Button>
                </>
              )}
            </div>
          )}

          <section>
            <h3 className="text-xs font-medium text-text-muted mb-2">Historial</h3>
            <ol className="space-y-1.5">
              {ticket.history.map((entry, index) => (
                <li key={index} className="flex flex-wrap gap-x-2 text-xs text-text-secondary">
                  <span className="text-text-muted tabular-nums">{dateTime(entry.created_at)}</span>
                  <span className="font-medium text-text-primary">{TICKET_STATUS[entry.to_status].label}</span>
                  <span>{entry.username}</span>
                  {entry.note && <span>· {entry.note}</span>}
                </li>
              ))}
            </ol>
          </section>
        </div>
      )}
      {!ticket && error && <ErrorNotice message={error} />}
    </Modal>
  );
}
