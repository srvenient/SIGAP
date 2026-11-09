import { ArrowDownToLine, ArrowUpFromLine, Banknote } from "lucide-react";
import { DeviceList } from "../../components/operations/DeviceList";
import { OccupancyCard } from "../../components/operations/OccupancyCard";
import { ErrorNotice, PageLoading } from "../../components/ui/DataStates";
import { StatCard, StatGrid } from "../../components/ui/StatCard";
import { usePolling } from "../../hooks/usePolling";
import { money } from "../../lib/format";
import { reportsApi } from "../../services/operations";

export default function AdminDashboard() {
  const { data, error } = usePolling(reportsApi.dashboard);

  if (!data) return error ? <ErrorNotice message={error} /> : <PageLoading />;

  return (
    <div className="space-y-5">
      {error && <ErrorNotice message={`Datos sin actualizar: ${error}`} />}

      <StatGrid columns={4}>
        <OccupancyCard occupancy={data.occupancy} />
        <StatCard
          title="Recaudo de hoy"
          value={money(data.revenue_today)}
          subtitle="Pagos aprobados"
          icon={<Banknote className="w-4 h-4" />}
        />
        <StatCard
          title="Ingresos de hoy"
          value={data.entries_today}
          subtitle="Vehículos registrados"
          icon={<ArrowDownToLine className="w-4 h-4" />}
        />
        <StatCard
          title="Salidas de hoy"
          value={data.exits_today}
          subtitle="Vehículos finalizados"
          icon={<ArrowUpFromLine className="w-4 h-4" />}
        />
      </StatGrid>

      <DeviceList devices={data.devices} wide />
    </div>
  );
}
