export type VehicleType = "car" | "motorcycle" | "unknown";
export type TransactionStatus = "entered" | "paid" | "completed";
export type Gate = "entry" | "exit";

export interface Paged<T> {
  data: T[];
  count: number;
}

export interface Occupancy {
  capacity: number;
  occupied: number;
  available: number;
  percentage: number;
}

export interface ParkingLot {
  id: string;
  name: string;
  address: string | null;
  capacity: number;
  gate_open_seconds: number;
}

export interface Transaction {
  id: string;
  plate: string;
  vehicle_type: VehicleType;
  status: TransactionStatus;
  entry_time: string;
  exit_time: string | null;
  total_amount: number | null;
  billed_minutes: number | null;
  payment_method: string | null;
  payment_reference: string | null;
  paid_at: string | null;
  manual_intervention: boolean;
  manual_reason: string | null;
}

export interface PaymentAttempt {
  id: string;
  reference: string;
  method: string;
  amount: number;
  status: string;
  failure_reason: string | null;
  created_at: string;
  resolved_at: string | null;
}

export interface TransactionDetail extends Transaction {
  tariff_snapshot: TariffConfig | null;
  payment_attempts: PaymentAttempt[];
}

export interface TariffConfig {
  hourly_rate: number;
  fraction_rate: number;
  fraction_minutes: number;
  full_rate: number;
  full_rate_after_minutes: number;
}

export interface Tariff extends TariffConfig {
  id: string;
  vehicle_type: VehicleType;
  updated_at: string;
}

export interface TariffHistoryEntry {
  id: string;
  vehicle_type: VehicleType;
  previous_config: TariffConfig;
  new_config: TariffConfig;
  changed_by_username: string;
  changed_at: string;
}

export interface Device {
  code: string;
  kind: "camera" | "gate";
  name: string;
  status: "connected" | "no_communication" | "error";
  last_error: string | null;
  last_seen_at: string | null;
}

export interface TechnicalEvent {
  id: string;
  component: string;
  error_code: string;
  description: string;
  transaction_id: string | null;
  created_at: string;
}

export interface Dashboard {
  occupancy: Occupancy;
  revenue_today: number;
  entries_today: number;
  exits_today: number;
  devices: Device[];
}

export interface RevenueLine {
  key: string;
  total: number;
  count: number;
}

export interface Revenue {
  total: number;
  count: number;
  by_vehicle_type: RevenueLine[];
  by_payment_method: RevenueLine[];
}

export interface AuditEntry {
  id: string;
  actor_label: string;
  action: string;
  entity_type: string;
  entity_id: string | null;
  entity_label: string | null;
  result: "success" | "failure";
  detail: Record<string, unknown>;
  created_at: string;
}

export interface OperationAlert {
  id: string;
  gate: Gate;
  alert_type: string;
  status: string;
  plate_read: string | null;
  message: string;
  has_snapshot: boolean;
  created_at: string;
}

export interface GateCommand {
  id: string;
  gate: Gate;
  reason: string;
  requested_by_username: string;
  status: string;
  error: string | null;
  created_at: string;
}

export type TicketStatus = "pending" | "in_review" | "solved" | "not_solved";

export interface Ticket {
  id: string;
  origin: "manual" | "automatic";
  status: TicketStatus;
  component: string;
  error_code: string | null;
  description: string;
  transaction_id: string | null;
  created_by_username: string;
  assignee_username: string | null;
  diagnosis: string | null;
  actions_taken: string | null;
  result: string | null;
  created_at: string;
  updated_at: string;
}

export interface TicketDetail extends Ticket {
  history: {
    from_status: TicketStatus | null;
    to_status: TicketStatus;
    username: string;
    note: string | null;
    created_at: string;
  }[];
}

export interface Quote {
  plate: string;
  vehicle_type: VehicleType;
  status: TransactionStatus;
  entry_time: string;
  minutes: number;
  amount: number;
  charge_mode: "hourly" | "full_rate" | null;
  periods: number;
}

export interface PaymentMethods {
  methods: { code: string; label: string }[];
  simulated: boolean;
}

export interface PaymentState {
  reference: string;
  plate: string;
  method: string;
  amount: number;
  status: "pending" | "approved" | "rejected" | "cancelled" | "expired";
  failure_reason: string | null;
  expires_at: string;
  simulated: boolean;
}

export interface GateDisplay {
  display: {
    gate: Gate;
    state: "idle" | "validating" | "granted" | "denied" | "error";
    message: string;
    plate: string | null;
  };
  occupancy: Occupancy;
}
