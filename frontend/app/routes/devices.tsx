import { useState } from "react";
import { DeviceList } from "../components/operations/DeviceList";
import { EmptyRow, ErrorNotice, Pager, TableCard } from "../components/ui/DataStates";
import { usePolling } from "../hooks/usePolling";
import { dateTime } from "../lib/format";
import { devicesApi } from "../services/operations";

const PAGE_SIZE = 20;

export default function DevicesPage() {
  const [skip, setSkip] = useState(0);

  const { data, error } = usePolling(async () => {
    const [devices, events] = await Promise.all([devicesApi.list(), devicesApi.events({ skip, limit: PAGE_SIZE })]);
    return { devices, events };
  }, [skip]);

  return (
    <div className="space-y-6">
      {error && <ErrorNotice message={error} />}
      {data && <DeviceList devices={data.devices} title="Estado actual" wide />}

      <section className="space-y-2">
        <h2 className="text-sm font-semibold">Eventos técnicos</h2>
        <TableCard>
          <table className="data-table">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Componente</th>
                <th>Código</th>
                <th>Descripción</th>
              </tr>
            </thead>
            <tbody>
              {data?.events.count === 0 && <EmptyRow colSpan={4}>Sin eventos registrados.</EmptyRow>}
              {data?.events.data.map((event) => (
                <tr key={event.id}>
                  <td className="whitespace-nowrap">{dateTime(event.created_at)}</td>
                  <td className="font-medium text-text-primary">{event.component}</td>
                  <td className="font-mono text-xs">{event.error_code}</td>
                  <td>{event.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableCard>
        {data && <Pager skip={skip} limit={PAGE_SIZE} count={data.events.count} onChange={setSkip} />}
      </section>
    </div>
  );
}
