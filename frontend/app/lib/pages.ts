export interface PageInfo {
  title: string;
  description: string;
  section?: string;
}

export const PAGES: Record<string, PageInfo> = {
  "/dashboard": { title: "Panel", description: "Estado del parqueadero en tiempo real." },
  "/dashboard/vehicles": {
    title: "Vehículos dentro",
    description: "Vehículos que ocupan un cupo en este momento.",
    section: "Operación",
  },
  "/dashboard/alerts": {
    title: "Alertas e intervención",
    description: "Lecturas por confirmar y aperturas manuales de contingencia.",
    section: "Operación",
  },
  "/dashboard/transactions": {
    title: "Transacciones",
    description: "Historial de ingresos, salidas y pagos.",
    section: "Operación",
  },
  "/dashboard/revenue": {
    title: "Recaudo",
    description: "Pagos aprobados por periodo, tipo de vehículo y medio de pago.",
    section: "Operación",
  },
  "/dashboard/devices": {
    title: "Dispositivos",
    description: "Cámaras, talanqueras y su registro de eventos técnicos.",
    section: "Operación",
  },
  "/dashboard/tickets": {
    title: "Tickets técnicos",
    description: "Reportes de fallas y su seguimiento.",
    section: "Operación",
  },
  "/dashboard/tariffs": {
    title: "Tarifas",
    description: "Valores vigentes por tipo de vehículo. Los cambios no alteran lo ya liquidado.",
    section: "Administración",
  },
  "/dashboard/users": {
    title: "Usuarios",
    description: "Cuentas de acceso y roles del personal.",
    section: "Administración",
  },
  "/dashboard/settings": {
    title: "Parqueadero",
    description: "Datos de la sede, capacidad y tiempo de apertura de las talanqueras.",
    section: "Administración",
  },
  "/dashboard/audit": {
    title: "Auditoría",
    description: "Registro inmutable de las acciones realizadas en el sistema.",
    section: "Administración",
  },
};
