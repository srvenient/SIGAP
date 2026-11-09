import { apiFetch } from "./api";
import type {
  AuditEntry,
  Dashboard,
  Device,
  Gate,
  GateCommand,
  GateDisplay,
  Occupancy,
  OperationAlert,
  Paged,
  ParkingLot,
  PaymentMethods,
  PaymentState,
  Quote,
  Revenue,
  Tariff,
  TariffConfig,
  TariffHistoryEntry,
  TechnicalEvent,
  Ticket,
  TicketDetail,
  Transaction,
  TransactionDetail,
} from "../types/operations";

type Params = Record<string, string | number | undefined | null>;

function query(params: Params): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

const post = <T>(path: string, body?: unknown) =>
  apiFetch<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

const send = <T>(method: "PUT" | "PATCH", path: string, body: unknown) =>
  apiFetch<T>(path, { method, body: JSON.stringify(body) });

export const publicApi = {
  quote: (plate: string) => apiFetch<Quote>(`/public/quote/${encodeURIComponent(plate)}`),
  methods: () => apiFetch<PaymentMethods>("/public/payment-methods"),
  startPayment: (plate: string, method: string) => post<PaymentState>("/public/payments", { plate, method }),
  paymentState: (reference: string) => apiFetch<PaymentState>(`/public/payments/${encodeURIComponent(reference)}`),
  cancelPayment: (reference: string) => post<PaymentState>(`/public/payments/${encodeURIComponent(reference)}/cancel`),
  simulatePayment: (reference: string, outcome: "approved" | "rejected") =>
    post<PaymentState>(`/public/payments/${encodeURIComponent(reference)}/simulate`, { outcome }),
  gateDisplay: (gate: Gate) => apiFetch<GateDisplay>(`/public/gates/${gate}/display`),
};

export const parkingApi = {
  get: () => apiFetch<ParkingLot>("/parking"),
  update: (changes: Partial<Omit<ParkingLot, "id">>) => send<ParkingLot>("PATCH", "/parking", changes),
  occupancy: () => apiFetch<Occupancy>("/parking/occupancy"),
};

export const reportsApi = {
  dashboard: () => apiFetch<Dashboard>("/reports/dashboard"),
  revenue: (params: Params) => apiFetch<Revenue>(`/reports/revenue${query(params)}`),
};

export const transactionsApi = {
  search: (params: Params) => apiFetch<Paged<Transaction>>(`/transactions${query(params)}`),
  detail: (id: string) => apiFetch<TransactionDetail>(`/transactions/${id}`),
  inside: (plate?: string) => apiFetch<Transaction[]>(`/transactions/inside${query({ plate })}`),
};

export const tariffsApi = {
  list: () => apiFetch<Tariff[]>("/tariffs"),
  update: (vehicleType: string, config: TariffConfig) => send<Tariff>("PUT", `/tariffs/${vehicleType}`, config),
  history: (params: Params) => apiFetch<Paged<TariffHistoryEntry>>(`/tariffs/history${query(params)}`),
};

export const auditApi = {
  search: (params: Params) => apiFetch<Paged<AuditEntry>>(`/audit${query(params)}`),
};

export const devicesApi = {
  list: () => apiFetch<Device[]>("/devices"),
  events: (params: Params) => apiFetch<Paged<TechnicalEvent>>(`/devices/events${query(params)}`),
};

export const interventionsApi = {
  alerts: () => apiFetch<OperationAlert[]>("/interventions/alerts"),
  snapshotUrl: (alertId: string) => `/api/v1/interventions/alerts/${alertId}/snapshot`,
  resolve: (alertId: string, plate: string, reason: string) =>
    post<GateCommand>(`/interventions/alerts/${alertId}/resolve`, { plate, reason }),
  dismiss: (alertId: string, reason: string) => post(`/interventions/alerts/${alertId}/dismiss`, { reason }),
  manualEntry: (plate: string, reason: string) => post<GateCommand>("/interventions/manual-entry", { plate, reason }),
  correctPlate: (transactionId: string, plate: string, reason: string) =>
    send<Transaction>("PATCH", `/interventions/transactions/${transactionId}/plate`, { plate, reason }),
  openGate: (gate: Gate, reason: string) => post<GateCommand>(`/interventions/gates/${gate}/open`, { reason }),
  commands: () => apiFetch<GateCommand[]>("/interventions/commands"),
};

export const ticketsApi = {
  search: (params: Params) => apiFetch<Paged<Ticket>>(`/tickets${query(params)}`),
  detail: (id: string) => apiFetch<TicketDetail>(`/tickets/${id}`),
  create: (data: { component: string; description: string; transaction_id?: string }) => post<Ticket>("/tickets", data),
  take: (id: string) => post<Ticket>(`/tickets/${id}/take`),
  saveNotes: (id: string, notes: { diagnosis?: string; actions_taken?: string; result?: string }) =>
    send<Ticket>("PATCH", `/tickets/${id}/notes`, notes),
  close: (id: string, data: { status: string; diagnosis: string; actions_taken: string; result: string }) =>
    post<Ticket>(`/tickets/${id}/close`, data),
};
