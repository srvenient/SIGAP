const TIME_ZONE = "America/Bogota";

const moneyFormat = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});

const dateTimeFormat = new Intl.DateTimeFormat("es-CO", {
  timeZone: TIME_ZONE,
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

const clockFormat = new Intl.DateTimeFormat("es-CO", {
  timeZone: TIME_ZONE,
  weekday: "short",
  day: "numeric",
  month: "short",
  hour: "numeric",
  minute: "2-digit",
});

export const clock = (date: Date): string => clockFormat.format(date);

const shortDateTimeFormat = new Intl.DateTimeFormat("es-CO", {
  timeZone: TIME_ZONE,
  day: "numeric",
  month: "short",
  hour: "numeric",
  minute: "2-digit",
});

export const shortDateTime = (iso: string | null | undefined): string =>
  iso ? shortDateTimeFormat.format(new Date(iso)) : "-";

export const money = (value: number | null | undefined): string =>
  value === null || value === undefined ? "-" : moneyFormat.format(value);

export const dateTime = (iso: string | null | undefined): string =>
  iso ? dateTimeFormat.format(new Date(iso)) : "-";

export function duration(minutes: number): string {
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (hours === 0) return `${rest} min`;
  return rest === 0 ? `${hours} h` : `${hours} h ${rest} min`;
}

export const minutesSince = (iso: string): number =>
  Math.max(1, Math.ceil((Date.now() - new Date(iso).getTime()) / 60000));

/** Fecha de hoy en Colombia, en el formato de <input type="date">. */
export const todayLocal = (): string =>
  new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE }).format(new Date());

export const VEHICLE_LABELS: Record<string, string> = {
  car: "Carro",
  motorcycle: "Moto",
  unknown: "Desconocido",
};

export const TRANSACTION_STATUS: Record<string, { label: string; variant: "warning" | "success" | "neutral" }> = {
  entered: { label: "Ingresado", variant: "warning" },
  paid: { label: "Pagado", variant: "success" },
  completed: { label: "Finalizado", variant: "neutral" },
};

export const PAYMENT_STATUS: Record<string, { label: string; variant: "warning" | "success" | "danger" | "neutral" }> = {
  pending: { label: "Procesando", variant: "warning" },
  approved: { label: "Aprobado", variant: "success" },
  rejected: { label: "Rechazado", variant: "danger" },
  cancelled: { label: "Cancelado", variant: "neutral" },
  expired: { label: "Vencido", variant: "danger" },
};

export const PAYMENT_METHODS: Record<string, string> = {
  card: "Tarjeta",
  pse: "PSE",
  nequi: "Nequi",
  sin_dato: "Sin dato",
};

export const DEVICE_STATUS: Record<string, { label: string; variant: "success" | "warning" | "danger" }> = {
  connected: { label: "Conectado", variant: "success" },
  no_communication: { label: "Sin comunicación", variant: "warning" },
  error: { label: "Con error", variant: "danger" },
};

export const TICKET_STATUS: Record<string, { label: string; variant: "warning" | "primary" | "success" | "danger" }> = {
  pending: { label: "Pendiente", variant: "warning" },
  in_review: { label: "En revisión", variant: "primary" },
  solved: { label: "Solucionado", variant: "success" },
  not_solved: { label: "No solucionado", variant: "danger" },
};

export const ALERT_LABELS: Record<string, string> = {
  plate_unreadable: "Placa no reconocida",
  payment_pending: "Pago pendiente en la salida",
  no_active_transaction: "Salida sin transacción activa",
};

export const GATE_LABELS: Record<string, string> = { entry: "Ingreso", exit: "Salida" };

export const COMMAND_STATUS: Record<string, { label: string; variant: "warning" | "success" | "danger" }> = {
  pending: { label: "En cola", variant: "warning" },
  sent: { label: "Enviada", variant: "warning" },
  done: { label: "Ejecutada", variant: "success" },
  failed: { label: "Falló", variant: "danger" },
  expired: { label: "Venció", variant: "danger" },
};

export const AUDIT_ACTIONS: Record<string, string> = {
  "transaction.created": "Ingreso registrado",
  "transaction.completed": "Transacción finalizada",
  "transaction.plate_corrected": "Placa corregida",
  "payment.approved": "Pago aprobado",
  "payment.failed": "Pago fallido",
  "gate.opened": "Talanquera abierta",
  "gate.open_failed": "Apertura fallida",
  "gate.open_requested": "Apertura solicitada",
  "tariff.updated": "Tarifa modificada",
  "parking.updated": "Parqueadero modificado",
  "user.created": "Cuenta creada",
  "user.updated": "Cuenta modificada",
  "user.password_reset": "Contraseña restablecida",
  "user.unlocked": "Cuenta desbloqueada",
  "auth.login": "Inicio de sesión",
  "auth.logout": "Cierre de sesión",
  "alert.resolved": "Alerta resuelta",
  "alert.dismissed": "Alerta descartada",
  "ticket.created": "Ticket creado",
  "ticket.status_changed": "Estado de ticket cambiado",
};
