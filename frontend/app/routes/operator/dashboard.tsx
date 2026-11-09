import { Link } from "react-router";
import { TriangleAlert } from "lucide-react";
import { OccupancyCard } from "../../components/operations/OccupancyCard";
import { Badge } from "../../components/ui/Badge";
import { Card, CardHeader } from "../../components/ui/Card";
import { EmptyPanel, ErrorNotice, PageLoading } from "../../components/ui/DataStates";
import { Plate } from "../../components/ui/Plate";
import { StatCard, StatGrid } from "../../components/ui/StatCard";
import { usePolling } from "../../hooks/usePolling";
import { ALERT_LABELS, GATE_LABELS, dateTime } from "../../lib/format";
import { interventionsApi, parkingApi } from "../../services/operations";

export default function OperatorDashboard() {
  const { data, error } = usePolling(async () => {
    const [occupancy, alerts] = await Promise.all([parkingApi.occupancy(), interventionsApi.alerts()]);
    return { occupancy, alerts };
  });

  if (!data) return error ? <ErrorNotice message={error} /> : <PageLoading />;

  return (
    <div className="space-y-5">
      {error && <ErrorNotice message={`Datos sin actualizar: ${error}`} />}

      <StatGrid columns={2}>
        <OccupancyCard occupancy={data.occupancy} />
        <StatCard
          title="Alertas por atender"
          value={data.alerts.length}
          subtitle={data.alerts.length === 0 ? "Operación sin novedades" : "Requieren intervención"}
          icon={<TriangleAlert className="w-4 h-4" />}
        />
      </StatGrid>

      <Card className="overflow-hidden">
        <CardHeader
          title={`Alertas pendientes (${data.alerts.length})`}
          action={
            <Link to="/dashboard/alerts" className="btn-secondary">
              Atender alertas
            </Link>
          }
        />
        {data.alerts.length === 0 ? (
          <EmptyPanel>No hay alertas por atender.</EmptyPanel>
        ) : (
          <ul className="divide-y divide-border-secondary">
            {data.alerts.slice(0, 8).map((alert) => (
              <li key={alert.id} className="flex flex-wrap items-center gap-3 px-5 py-3">
                <Badge variant="warning" size="sm">
                  {GATE_LABELS[alert.gate]}
                </Badge>
                <span className="text-sm font-medium">{ALERT_LABELS[alert.alert_type]}</span>
                {alert.plate_read && <Plate value={alert.plate_read} size="sm" />}
                <span className="ml-auto text-xs text-text-muted">{dateTime(alert.created_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
