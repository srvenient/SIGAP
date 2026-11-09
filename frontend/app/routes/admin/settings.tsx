import React, { useEffect, useState } from "react";
import { Button } from "../../components/ui/Button";
import { ErrorNotice } from "../../components/ui/DataStates";
import { Input } from "../../components/ui/Input";
import { useToast } from "../../context/ToastContext";
import { ApiError } from "../../services/api";
import { parkingApi } from "../../services/operations";

export default function SettingsPage() {
  const { toast } = useToast();
  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [capacity, setCapacity] = useState("");
  const [seconds, setSeconds] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    parkingApi
      .get()
      .then((lot) => {
        setName(lot.name);
        setAddress(lot.address ?? "");
        setCapacity(String(lot.capacity));
        setSeconds(String(lot.gate_open_seconds));
      })
      .catch((err) => setError(err instanceof ApiError ? err.message : "No se pudo cargar la configuración"));
  }, []);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await parkingApi.update({
        name: name.trim(),
        address: address.trim(),
        capacity: Number(capacity),
        gate_open_seconds: Number(seconds),
      });
      toast("Configuración guardada", "success");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "No se pudo guardar");
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={save} className="card p-5 space-y-4 max-w-lg">
      <Input label="Nombre del parqueadero" value={name} onChange={(e) => setName(e.target.value)} maxLength={120} required />
      <Input label="Dirección" value={address} onChange={(e) => setAddress(e.target.value)} maxLength={200} />
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="Capacidad (cupos)" type="number" min={1} value={capacity} onChange={(e) => setCapacity(e.target.value)} required />
        <Input
          label="Apertura de talanquera (s)"
          helperText="Tiempo antes del cierre automático, de 1 a 60"
          type="number"
          min={1}
          max={60}
          value={seconds}
          onChange={(e) => setSeconds(e.target.value)}
          required
        />
      </div>

      {error && <ErrorNotice message={error} />}

      <Button type="submit" isLoading={saving}>
        Guardar
      </Button>
    </form>
  );
}
