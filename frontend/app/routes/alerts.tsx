import { useState } from "react";
import { DoorOpen, PenLine } from "lucide-react";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { ErrorNotice } from "../components/ui/DataStates";
import { Input, Select } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { Plate } from "../components/ui/Plate";
import { useToast } from "../context/ToastContext";
import { usePolling } from "../hooks/usePolling";
import { ALERT_LABELS, COMMAND_STATUS, GATE_LABELS, dateTime } from "../lib/format";
import { ApiError } from "../services/api";
import { interventionsApi } from "../services/operations";
import type { Gate, OperationAlert } from "../types/operations";

type Dialog =
  | { kind: "resolve"; alert: OperationAlert }
  | { kind: "dismiss"; alert: OperationAlert }
  | { kind: "manual-entry" }
  | { kind: "open-gate" }
  | null;

export default function AlertsPage() {
  const [dialog, setDialog] = useState<Dialog>(null);

  const { data, error, reload } = usePolling(async () => {
    const [alerts, commands] = await Promise.all([interventionsApi.alerts(), interventionsApi.commands()]);
    return { alerts, commands };
  });

  const close = () => setDialog(null);
  const done = () => {
    setDialog(null);
    void reload();
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2 justify-end">
        <Button variant="outline" leftIcon={<PenLine className="w-4 h-4" />} onClick={() => setDialog({ kind: "manual-entry" })}>
          Registrar ingreso manual
        </Button>
        <Button variant="outline" leftIcon={<DoorOpen className="w-4 h-4" />} onClick={() => setDialog({ kind: "open-gate" })}>
          Abrir talanquera
        </Button>
      </div>

      {error && <ErrorNotice message={error} />}

      {data?.alerts.length === 0 && <p className="card py-16 text-center text-sm text-text-muted">No hay alertas por atender.</p>}

      <div className="grid gap-4 lg:grid-cols-2">
        {data?.alerts.map((alert) => (
          <article key={alert.id} className="card overflow-hidden flex flex-col sm:flex-row">
            {alert.has_snapshot && (
              <img
                src={interventionsApi.snapshotUrl(alert.id)}
                alt="Captura de la cámara"
                className="sm:w-48 h-40 sm:h-auto object-cover bg-bg-accent"
              />
            )}
            <div className="p-4 flex-1 flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <Badge variant="warning">{GATE_LABELS[alert.gate]}</Badge>
                <span className="text-xs text-text-muted">{dateTime(alert.created_at)}</span>
              </div>
              <h2 className="font-semibold">{ALERT_LABELS[alert.alert_type]}</h2>
              <p className="text-sm text-text-secondary">{alert.message}</p>
              {alert.plate_read && (
                <div>
                  <Plate value={alert.plate_read} />
                </div>
              )}
              <div className="mt-auto pt-2 flex gap-2">
                <Button size="sm" onClick={() => setDialog({ kind: "resolve", alert })}>
                  Registrar placa
                </Button>
                <Button size="sm" variant="ghost" onClick={() => setDialog({ kind: "dismiss", alert })}>
                  Descartar
                </Button>
              </div>
            </div>
          </article>
        ))}
      </div>

      {data && data.commands.length > 0 && (
        <section className="space-y-2">
          <h2 className="text-sm font-semibold">Órdenes de apertura recientes</h2>
          <ul className="card divide-y divide-border-secondary">
            {data.commands.map((command) => (
              <li key={command.id} className="flex flex-wrap items-center gap-3 px-4 py-2.5 text-sm">
                <Badge variant={COMMAND_STATUS[command.status].variant}>{COMMAND_STATUS[command.status].label}</Badge>
                <span className="font-medium">{GATE_LABELS[command.gate]}</span>
                <span className="text-text-secondary truncate">{command.reason}</span>
                <span className="ml-auto text-xs text-text-muted">
                  {command.requested_by_username} · {dateTime(command.created_at)}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {dialog?.kind === "resolve" && (
        <PlateReasonDialog
          title="Registrar placa"
          subtitle={`${GATE_LABELS[dialog.alert.gate]}: continúa el flujo normal y abre la talanquera`}
          initialPlate={dialog.alert.plate_read ?? ""}
          confirm="Registrar y abrir"
          success="Orden enviada a la talanquera"
          onSubmit={(plate, reason) => interventionsApi.resolve(dialog.alert.id, plate, reason)}
          onClose={close}
          onDone={done}
        />
      )}
      {dialog?.kind === "manual-entry" && (
        <PlateReasonDialog
          title="Registrar ingreso manual"
          confirm="Registrar y abrir"
          success="Ingreso registrado"
          onSubmit={(plate, reason) => interventionsApi.manualEntry(plate, reason)}
          onClose={close}
          onDone={done}
        />
      )}
      {dialog?.kind === "dismiss" && <DismissDialog alert={dialog.alert} onClose={close} onDone={done} />}
      {dialog?.kind === "open-gate" && <OpenGateDialog onClose={close} onDone={done} />}
    </div>
  );
}

function useSubmit(onDone: () => void, success: string) {
  const { toast } = useToast();
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const submit = async (action: () => Promise<unknown>) => {
    setSaving(true);
    setError(null);
    try {
      await action();
      toast(success, "success");
      onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo completar la acción");
    } finally {
      setSaving(false);
    }
  };

  return { error, saving, submit };
}

function PlateReasonDialog({
  title,
  subtitle,
  initialPlate = "",
  confirm,
  success,
  onSubmit,
  onClose,
  onDone,
}: {
  title: string;
  subtitle?: string;
  initialPlate?: string;
  confirm: string;
  success: string;
  onSubmit: (plate: string, reason: string) => Promise<unknown>;
  onClose: () => void;
  onDone: () => void;
}) {
  const [plate, setPlate] = useState(initialPlate);
  const [reason, setReason] = useState("");
  const { error, saving, submit } = useSubmit(onDone, success);

  return (
    <Modal
      isOpen
      onClose={onClose}
      title={title}
      subtitle={subtitle}
      maxWidth="sm"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            isLoading={saving}
            disabled={plate.length < 5 || reason.trim().length < 3}
            onClick={() => submit(() => onSubmit(plate, reason))}
          >
            {confirm}
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <Input
          label="Placa"
          value={plate}
          onChange={(e) => setPlate(e.target.value.toUpperCase())}
          className="font-mono"
          maxLength={7}
          autoFocus
        />
        <Input label="Motivo" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={300} />
        {error && <ErrorNotice message={error} />}
      </div>
    </Modal>
  );
}

function DismissDialog({ alert, onClose, onDone }: { alert: OperationAlert; onClose: () => void; onDone: () => void }) {
  const [reason, setReason] = useState("");
  const { error, saving, submit } = useSubmit(onDone, "Alerta descartada");

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Descartar alerta"
      maxWidth="sm"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            isLoading={saving}
            disabled={reason.trim().length < 3}
            onClick={() => submit(() => interventionsApi.dismiss(alert.id, reason))}
          >
            Descartar
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <Input label="Motivo" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={300} autoFocus />
        {error && <ErrorNotice message={error} />}
      </div>
    </Modal>
  );
}

function OpenGateDialog({ onClose, onDone }: { onClose: () => void; onDone: () => void }) {
  const [gate, setGate] = useState<Gate>("entry");
  const [reason, setReason] = useState("");
  const { error, saving, submit } = useSubmit(onDone, "Orden enviada a la talanquera");

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Abrir talanquera"
      subtitle="Solo para contingencias. No cambia el estado de ninguna transacción y queda en la auditoría."
      maxWidth="sm"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancelar
          </Button>
          <Button
            variant="danger"
            isLoading={saving}
            disabled={reason.trim().length < 3}
            onClick={() => submit(() => interventionsApi.openGate(gate, reason))}
          >
            Abrir
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <Select
          label="Talanquera"
          value={gate}
          onChange={(e) => setGate(e.target.value as Gate)}
          options={[
            { value: "entry", label: "Ingreso" },
            { value: "exit", label: "Salida" },
          ]}
        />
        <Input label="Motivo" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={300} />
        {error && <ErrorNotice message={error} />}
      </div>
    </Modal>
  );
}
