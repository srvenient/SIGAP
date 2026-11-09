import { useEffect, useState } from "react";
import { Bike, Car } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { EmptyRow, ErrorNotice, Pager, TableCard } from "../../components/ui/DataStates";
import { Input, Select } from "../../components/ui/Input";
import { useToast } from "../../context/ToastContext";
import { usePolling } from "../../hooks/usePolling";
import { VEHICLE_LABELS, dateTime, duration, money } from "../../lib/format";
import { ApiError } from "../../services/api";
import { tariffsApi } from "../../services/operations";
import type { Tariff, TariffConfig } from "../../types/operations";

const PAGE_SIZE = 15;

const FIELDS: { key: keyof TariffConfig; label: string; helper?: string }[] = [
  { key: "hourly_rate", label: "Valor por hora (COP)" },
  { key: "fraction_rate", label: "Valor por fracción (COP)" },
  { key: "fraction_minutes", label: "Duración de la fracción (min)" },
  { key: "full_rate", label: "Tarifa plena (COP)" },
  { key: "full_rate_after_minutes", label: "Tarifa plena desde (min)", helper: "Cada 12 h se cobra otra tarifa plena" },
];

const describe = (config: TariffConfig) =>
  `${money(config.hourly_rate)}/h · ${money(config.fraction_rate)} por ${config.fraction_minutes} min · plena ${money(
    config.full_rate
  )} desde ${duration(config.full_rate_after_minutes)}`;

export default function TariffsPage() {
  const [vehicleType, setVehicleType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [skip, setSkip] = useState(0);

  const { data: tariffs, error, reload: reloadTariffs } = usePolling(tariffsApi.list, [], 0);
  const { data: history, reload: reloadHistory } = usePolling(
    () => tariffsApi.history({ vehicle_type: vehicleType, date_from: dateFrom, date_to: dateTo, skip, limit: PAGE_SIZE }),
    [vehicleType, dateFrom, dateTo, skip],
    0
  );

  const onSaved = () => {
    void reloadTariffs();
    void reloadHistory();
  };

  return (
    <div className="space-y-8">
      {error && <ErrorNotice message={error} />}

      <div className="grid gap-4 lg:grid-cols-2">
        {tariffs?.map((tariff) => (
          <TariffForm key={tariff.id} tariff={tariff} onSaved={onSaved} />
        ))}
      </div>

      <section className="space-y-3">
        <h2 className="text-sm font-semibold">Histórico de cambios</h2>
        <div className="card p-4 flex flex-wrap gap-3">
          <div className="w-44">
            <Select
              label="Tipo de vehículo"
              value={vehicleType}
              onChange={(e) => {
                setVehicleType(e.target.value);
                setSkip(0);
              }}
              options={[
                { value: "", label: "Todos" },
                { value: "car", label: "Carro" },
                { value: "motorcycle", label: "Moto" },
              ]}
            />
          </div>
          <div className="w-44">
            <Input
              label="Desde"
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setSkip(0);
              }}
            />
          </div>
          <div className="w-44">
            <Input
              label="Hasta"
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setSkip(0);
              }}
            />
          </div>
        </div>

        <TableCard>
          <table className="data-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Tipo</th>
                <th>Usuario</th>
                <th>Anterior</th>
                <th>Nueva</th>
              </tr>
            </thead>
            <tbody>
              {history?.count === 0 && <EmptyRow colSpan={5}>Todavía no hay cambios de tarifa.</EmptyRow>}
              {history?.data.map((entry) => (
                <tr key={entry.id}>
                  <td className="whitespace-nowrap">{dateTime(entry.changed_at)}</td>
                  <td>{VEHICLE_LABELS[entry.vehicle_type]}</td>
                  <td>{entry.changed_by_username}</td>
                  <td className="text-xs">{describe(entry.previous_config)}</td>
                  <td className="text-xs text-text-primary">{describe(entry.new_config)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableCard>
        {history && <Pager skip={skip} limit={PAGE_SIZE} count={history.count} onChange={setSkip} />}
      </section>
    </div>
  );
}

function TariffForm({ tariff, onSaved }: { tariff: Tariff; onSaved: () => void }) {
  const { toast } = useToast();
  const [values, setValues] = useState<Record<keyof TariffConfig, string>>(() => toStrings(tariff));
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setValues(toStrings(tariff));
  }, [tariff]);

  const dirty = FIELDS.some(({ key }) => Number(values[key]) !== tariff[key]);
  const Icon = tariff.vehicle_type === "car" ? Car : Bike;

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await tariffsApi.update(tariff.vehicle_type, {
        hourly_rate: Number(values.hourly_rate),
        fraction_rate: Number(values.fraction_rate),
        fraction_minutes: Number(values.fraction_minutes),
        full_rate: Number(values.full_rate),
        full_rate_after_minutes: Number(values.full_rate_after_minutes),
      });
      toast(`Tarifa de ${VEHICLE_LABELS[tariff.vehicle_type].toLowerCase()} actualizada`, "success");
      onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar la tarifa");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="card p-5 space-y-4">
      <h2 className="flex items-center gap-2 font-semibold">
        <Icon className="w-5 h-5" />
        {VEHICLE_LABELS[tariff.vehicle_type]}
      </h2>

      <div className="grid gap-3 sm:grid-cols-2">
        {FIELDS.map(({ key, label, helper }) => (
          <Input
            key={key}
            id={`${tariff.vehicle_type}-${key}`}
            label={label}
            helperText={helper}
            type="number"
            min={1}
            value={values[key]}
            onChange={(e) => setValues((current) => ({ ...current, [key]: e.target.value }))}
          />
        ))}
      </div>

      {error && <ErrorNotice message={error} />}

      <div className="flex items-center justify-between gap-3">
        <p className="text-xs text-text-muted">Vigente desde {dateTime(tariff.updated_at)}</p>
        <Button onClick={save} isLoading={saving} disabled={!dirty}>
          Guardar
        </Button>
      </div>
    </section>
  );
}

function toStrings(config: TariffConfig): Record<keyof TariffConfig, string> {
  return {
    hourly_rate: String(config.hourly_rate),
    fraction_rate: String(config.fraction_rate),
    fraction_minutes: String(config.fraction_minutes),
    full_rate: String(config.full_rate),
    full_rate_after_minutes: String(config.full_rate_after_minutes),
  };
}
