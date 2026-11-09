import { useAuth } from "../context/AuthContext";
import AdminDashboard from "./admin/dashboard";
import OperatorDashboard from "./operator/dashboard";
import SupportDashboard from "./support/dashboard";

export default function RoleDashboard() {
  const { role } = useAuth();

  if (role === "admin") return <AdminDashboard />;
  if (role === "operator") return <OperatorDashboard />;
  if (role === "support") return <SupportDashboard />;
  return null;
}
