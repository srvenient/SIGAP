import type { ReactNode } from "react";
import { Camera, RectangleHorizontal } from "lucide-react";
import { Badge } from "../ui/Badge";
import { Card, CardHeader } from "../ui/Card";
import { DEVICE_STATUS, shortDateTime } from "../../lib/format";
import type { Device } from "../../types/operations";

export function DeviceList({
  devices,
  title = "Dispositivos",
  wide = false,
  action,
}: {
  devices: Device[];
  title?: string;
  wide?: boolean;
  action?: ReactNode;
}) {
  const connected = devices.filter((device) => device.status === "connected").length;

  return (
    <Card className="overflow-hidden">
      <CardHeader title={title} subtitle={`${connected} de ${devices.length} conectados`} action={action} />
      <ul className={`grid gap-px bg-border-secondary grid-cols-1 sm:grid-cols-2 ${wide ? "xl:grid-cols-4" : ""}`}>
        {devices.map((device) => {
          const status = DEVICE_STATUS[device.status];
          const Icon = device.kind === "camera" ? Camera : RectangleHorizontal;

          return (
            <li key={device.code} className="bg-bg-surface p-4 flex flex-col gap-3">
              <div className="flex items-center justify-between gap-2">
                <span className="w-8 h-8 rounded-md bg-bg-accent flex items-center justify-center text-text-secondary">
                  <Icon className="w-4 h-4" />
                </span>
                <Badge variant={status.variant} size="sm" dot>
                  {status.label}
                </Badge>
              </div>
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{device.name}</p>
                {device.last_error ? (
                  <p className="mt-0.5 text-xs text-status-error">{device.last_error}</p>
                ) : (
                  <p className="mt-0.5 text-xs text-text-muted">Última señal: {shortDateTime(device.last_seen_at)}</p>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
