import { Link } from "react-router";
import { DeviceList } from "../../components/operations/DeviceList";
import { Badge } from "../../components/ui/Badge";
import { Card, CardHeader } from "../../components/ui/Card";
import { EmptyPanel, ErrorNotice, PageLoading } from "../../components/ui/DataStates";
import { usePolling } from "../../hooks/usePolling";
import { TICKET_STATUS, dateTime } from "../../lib/format";
import { devicesApi, ticketsApi } from "../../services/operations";

export default function SupportDashboard() {
  const { data, error } = usePolling(async () => {
    const [devices, tickets] = await Promise.all([
      devicesApi.list(),
      ticketsApi.search({ status: "pending", limit: 8 }),
    ]);
    return { devices, tickets };
  });

  if (!data) return error ? <ErrorNotice message={error} /> : <PageLoading />;

  return (
    <div className="space-y-5">
      {error && <ErrorNotice message={`Datos sin actualizar: ${error}`} />}

      <div className="grid gap-5 lg:grid-cols-2 items-start">
        <DeviceList devices={data.devices} />

        <Card className="overflow-hidden">
          <CardHeader
            title={`Tickets pendientes (${data.tickets.count})`}
            action={
              <Link to="/dashboard/tickets" className="btn-secondary">
                Ver todos
              </Link>
            }
          />
          {data.tickets.data.length === 0 ? (
            <EmptyPanel>No hay tickets pendientes.</EmptyPanel>
          ) : (
            <ul className="divide-y divide-border-secondary">
              {data.tickets.data.map((ticket) => (
                <li key={ticket.id} className="px-5 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-medium truncate">{ticket.component}</p>
                    <Badge variant={TICKET_STATUS[ticket.status].variant} size="sm">
                      {TICKET_STATUS[ticket.status].label}
                    </Badge>
                  </div>
                  <p className="mt-0.5 text-xs text-text-muted truncate">
                    {dateTime(ticket.created_at)} · {ticket.description}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
