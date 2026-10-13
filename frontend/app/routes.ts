import { type RouteConfig, index, route, layout } from "@react-router/dev/routes";

export default [
  index("routes/login.tsx"),
  route("unauthorized", "routes/unauthorized.tsx"),

  layout("routes/dashboard-layout.tsx", [
    route("dashboard", "routes/dashboard.tsx"),
    route("dashboard/users", "routes/admin/users.tsx"),
    route("dashboard/feature-in-progress", "routes/placeholder.tsx"),
  ]),

  // 3. Catch-all para URLs no reconocidas y requests del navegador
  route("*", "routes/catchall.tsx"),
] satisfies RouteConfig;
