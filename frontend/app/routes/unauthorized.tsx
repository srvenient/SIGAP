import React from "react";
import { useNavigate } from "react-router";
import { ShieldAlert, ArrowLeft, Lock } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useAuth } from "../context/AuthContext";

export default function UnauthorizedPage() {
  const navigate = useNavigate();
  const { role } = useAuth();

  const handleReturn = () => {
    navigate("/dashboard");
  };

  return (
    <div className="min-h-screen bg-[#070b14] flex items-center justify-center p-4">
      <Card className="max-w-md w-full p-8 text-center space-y-6 bg-[#0c1222]/90 border-white/[0.08]">
        <div className="inline-flex p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400">
          <ShieldAlert className="w-12 h-12" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-white tracking-tight">Acceso No Autorizado (403)</h1>
          <p className="text-xs sm:text-sm text-slate-400">
            Su cuenta actual con rol <span className="text-white font-bold capitalize">"{role}"</span>{" "}
            no posee los privilegios necesarios para consultar o modificar esta sección del sistema.
          </p>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-950/60 border border-white/[0.06] text-xs text-slate-400 flex items-center gap-2 text-left">
          <Lock className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            Las acciones no autorizadas son registradas preventivamente en el sistema de auditoría.
          </span>
        </div>

        <Button
          variant="primary"
          size="md"
          className="w-full"
          leftIcon={<ArrowLeft className="w-4 h-4" />}
          onClick={handleReturn}
        >
          Regresar al Dashboard
        </Button>
      </Card>
    </div>
  );
}
