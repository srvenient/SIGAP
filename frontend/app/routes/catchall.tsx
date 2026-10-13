import React from "react";
import { Link } from "react-router";
import { ArrowLeft, Compass } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

export default function CatchAll() {
  return (
    <div className="min-h-screen bg-[#070b14] flex items-center justify-center p-4">
      <Card className="max-w-md w-full p-8 text-center space-y-6 bg-[#0c1222]/90 border-white/[0.08]">
        <div className="inline-flex p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-cyan-400">
          <Compass className="w-12 h-12" />
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-white tracking-tight">Ruta No Encontrada (404)</h1>
          <p className="text-xs sm:text-sm text-slate-400">
            La página solicitada no existe o fue reubicada en la plataforma SIGAP.
          </p>
        </div>

        <Link to="/" className="block">
          <Button
            variant="primary"
            size="md"
            className="w-full"
            leftIcon={<ArrowLeft className="w-4 h-4" />}
          >
            Ir a la Pantalla Principal
          </Button>
        </Link>
      </Card>
    </div>
  );
}
