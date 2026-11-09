import { type RouteConfig, index, route, layout } from "@react-router/dev/routes";

export default [
  index("routes/login.tsx"),

  // Interfaz operativa: pública, para el conductor
  route("pago", "routes/public/pago.tsx"),
  route("punto/:gate", "routes/public/punto.tsx"),

  layout("routes/dashboard-layout.tsx", [
    route("dashboard", "routes/dashboard.tsx"),
    route("dashboard/users", "routes/admin/users.tsx"),
    route("dashboard/transactions", "routes/admin/transactions.tsx"),
    route("dashboard/revenue", "routes/admin/revenue.tsx"),
    route("dashboard/tariffs", "routes/admin/tariffs.tsx"),
    route("dashboard/audit", "routes/admin/audit.tsx"),
    route("dashboard/settings", "routes/admin/settings.tsx"),
    route("dashboard/vehicles", "routes/vehicles.tsx"),
    route("dashboard/alerts", "routes/alerts.tsx"),
    route("dashboard/devices", "routes/devices.tsx"),
    route("dashboard/tickets", "routes/tickets.tsx"),
  ]),

  // Catch-all para URLs no reconocidas y requests del navegador
  route("*", "routes/catchall.tsx"),
] satisfies RouteConfig;
