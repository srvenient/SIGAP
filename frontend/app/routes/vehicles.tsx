import { useState } from "react";
import { Search } from "lucide-react";
import { OccupancyCard } from "../components/operations/OccupancyCard";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardHeader } from "../components/ui/Card";
import { EmptyRow, ErrorNotice } from "../components/ui/DataStates";
import { Input } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { Plate } from "../components/ui/Plate";
import { StatGrid } from "../components/ui/StatCard";
import { useToast } from "../context/ToastContext";
import { usePolling } from "../hooks/usePolling";
import { TRANSACTION_STATUS, VEHICLE_LABELS, dateTime, duration, minutesSince } from "../lib/format";
import { ApiError } from "../services/api";
import { interventionsApi, parkingApi, transactionsApi } from "../services/operations";
import type { Transaction } from "../types/operations";

export default function VehiclesPage() {
  const [plate, setPlate] = useState("");
  const [editing, setEditing] = useState<Transaction | null>(null);

  const { data, error, reload } = usePolling(async () => {
    const [occupancy, vehicles] = await Promise.all([parkingApi.occupancy(), transactionsApi.inside(plate)]);
    return { occupancy, vehicles };
  }, [plate]);

  return (
    <div className="space-y-5">
      {error && <ErrorNotice message={error} />}

      {data && (
        <StatGrid columns={1}>
          <OccupancyCard occupancy={data.occupancy} />
        </StatGrid>
      )}

      <Card className="overflow-hidden">
        <CardHeader
          title="Registros activos"
          subtitle={data ? `${data.vehicles.length} vehículos` : undefined}
          action={
            <div className="w-40 sm:w-56">
              <Input
                aria-label="Buscar por placa"
                placeholder="Buscar por placa"
                value={plate}
                onChange={(e) => setPlate(e.target.value.toUpperCase())}
                leftIcon={<Search className="w-4 h-4" />}
                maxLength={7}
              />
            </div>
          }
        />
        <div className="overflow-x-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th>Placa</th>
              <th>Tipo</th>
              <th>Ingreso</th>
              <th>Permanencia</th>
              <th>Estado</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {data?.vehicles.length === 0 && (
              <EmptyRow colSpan={6}>{plate ? "Ningún vehículo coincide." : "El parqueadero está vacío."}</EmptyRow>
            )}
            {data?.vehicles.map((vehicle) => (
              <tr key={vehicle.id}>
                <td>
                  <Plate value={vehicle.plate} />
                </td>
                <td>{VEHICLE_LABELS[vehicle.vehicle_type]}</td>
                <td>{dateTime(vehicle.entry_time)}</td>
                <td className="tabular-nums">{duration(minutesSince(vehicle.entry_time))}</td>
                <td>
                  <Badge variant={TRANSACTION_STATUS[vehicle.status].variant}>
                    {TRANSACTION_STATUS[vehicle.status].label}
                  </Badge>
                </td>
                <td className="text-right">
                  <Button variant="outline" size="sm" onClick={() => setEditing(vehicle)}>
                    Corregir placa
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </Card>

      {editing && (
        <CorrectPlateModal
          transaction={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            void reload();
          }}
        />
      )}
    </div>
  );
}

function CorrectPlateModal({
  transaction,
  onClose,
  onSaved,
}: {
  transaction: Transaction;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { toast } = useToast();
  const [plate, setPlate] = useState(transaction.plate);
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await interventionsApi.correctPlate(transaction.id, plate, reason);
      toast("Placa corregida", "success");
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      isOpen
      onClose={onClose}
      title="Corregir placa"
      maxWidth="sm"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cancelar
          </Button>
          <Button onClick={save} isLoading={saving} disabled={reason.trim().length < 3}>
            Guardar
          </Button>
        </>
      }
    >
      <div className="space-y-3">
        <Input
          label="Placa correcta"
          value={plate}
          onChange={(e) => setPlate(e.target.value.toUpperCase())}
          className="font-mono"
          maxLength={7}
        />
        <Input label="Motivo" value={reason} onChange={(e) => setReason(e.target.value)} maxLength={300} />
        {error && <ErrorNotice message={error} />}
      </div>
    </Modal>
  );
}
