import React from "react";
import { useSearchParams, useNavigate } from "react-router";
import { Sparkles, ArrowLeft, Layers, ShieldCheck, CheckCircle2 } from "lucide-react";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";

export default function PlaceholderFeature() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const featureKey = searchParams.get("f") || "modulo";

  const featureMetadata: Record<
    string,
    { title: string; subtitle: string; description: string; sprint: string }
  > = {
    "multi-sede": {
      title: "Administración Centralizada Multi-Sede",
      subtitle: "Escalabilidad empresarial para red de parqueaderos",
      description:
        "Este módulo permitirá gestionar sedes distribuidas en diferentes ciudades, consolidando recaudos, tarifas regionales y ocupación en un único panel corporativo sin reconstruir la arquitectura base.",
      sprint: "Fase 2 - Escalado Enterprise",
    },
    convenios: {
      title: "Convenios Comerciales & Tarifas Preferenciales",
      subtitle: "Acuerdos corporativos y descuentos automatizados",
      description:
        "Módulo para asociar convenios con centros comerciales, universidades y gimnasios con validación de códigos QR y subsidio de tarifa por fracción.",
      sprint: "Fase 2 - Convenios B2B",
    },
    "pasarela-api": {
      title: "Integración Directa Pasarela Electrónica API",
      subtitle: "Conectores bancarios y webhooks en vivo",
      description:
        "Infraestructura de conciliación bancaria directa con pasarelas de pago (Wompi, MercadoPago, PSE) y validación criptográfica de comprobantes de pago sin intervención humana.",
      sprint: "Fase 2 - FinTech",
    },
    "totem-pago": {
      title: "Módulo Público de Pago para Conductores (Kiosco)",
      subtitle: "Interfaz autoservicio para el usuario final",
      description:
        "Punto físico táctil donde el conductor digita su placa, consulta el valor calculado según las horas transcurridas y realiza el pago con tarjeta o QR antes de dirigirse a la salida.",
      sprint: "Fase 2 - Módulos Públicos",
    },
    "talanquera-in": {
      title: "Punto de Control: Talanquera de Ingreso",
      subtitle: "Automatización de carril de entrada",
      description:
        "Simulador industrial de lazo inductivo electromagnético, control de semáforo verde/rojo y barrera física automática sincronizada con el motor OCR.",
      sprint: "Fase 2 - Hardware IoT",
    },
    "talanquera-out": {
      title: "Punto de Control: Talanquera de Salida",
      subtitle: "Automatización de carril de salida",
      description:
        "Validación instantánea del estado 'Pagado' de la transacción en curso para ordenar la apertura de la talanquera de salida y registrar la finalización del servicio.",
      sprint: "Fase 2 - Hardware IoT",
    },
    "telemetria-ocr": {
      title: "Telemetría Avanzada de Cámaras OCR",
      subtitle: "Analítica de visión por computador e IA",
      description:
        "Métricas en tiempo real de FPS, tiempo de inferencia del modelo YOLO/OCR, temperatura del sensor y registro de imágenes infrarrojas para ajuste de contraste.",
      sprint: "Fase 2 - IA & Visión",
    },
    "logs-red": {
      title: "Consola de Protocolos Industriales & Red",
      subtitle: "Captura de paquetes Modbus TCP y RTSP",
      description:
        "Inspección en bajo nivel de los frames de comunicación entre los controladores PLC de las talanqueras y el servidor backend.",
      sprint: "Fase 2 - Red & Seguridad",
    },
  };

  const current = featureMetadata[featureKey] || {
    title: "Módulo Corporativo en Desarrollo",
    subtitle: "Funcionalidad planificada en el roadmap de SIGAP",
    description:
      "Esta función se encuentra reservada en la navegación del menú y será desplegada en la siguiente fase de integración.",
    sprint: "Próxima Actualización",
  };

  return (
    <div className="max-w-3xl mx-auto py-12 px-4 animate-in fade-in duration-300">
      <Card glow className="p-8 sm:p-12 text-center relative overflow-hidden bg-[#0c1222]/90 border-white/[0.08]">
        {/* Glow accent */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 space-y-6">
          <div className="inline-flex p-4 rounded-2xl bg-gradient-to-tr from-blue-600/20 to-indigo-600/20 border border-blue-500/30 text-cyan-400 shadow-xl">
            <Layers className="w-10 h-10" />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-center gap-2">
              <Badge variant="cyan" size="md">
                <Sparkles className="w-3.5 h-3.5" />
                {current.sprint}
              </Badge>
              <Badge variant="neutral" size="md">
                Arquitectura Modular
              </Badge>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              {current.title}
            </h1>
            <p className="text-sm text-blue-300 font-medium">{current.subtitle}</p>
          </div>

          <p className="text-xs sm:text-sm text-slate-300 max-w-xl mx-auto leading-relaxed">
            {current.description}
          </p>

          <div className="p-4 rounded-xl bg-slate-950/60 border border-white/[0.06] text-left max-w-md mx-auto space-y-2 text-xs text-slate-400">
            <div className="flex items-center gap-2 text-slate-300 font-semibold">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Estado de la plataforma:</span>
            </div>
            <p>
              La estructura del menú y las capas de servicio ya se encuentran preparadas para
              vincular este componente en el momento en que se habilite el endpoint correspondiente.
            </p>
          </div>

          <div className="pt-4">
            <Button
              variant="primary"
              size="md"
              leftIcon={<ArrowLeft className="w-4 h-4" />}
              onClick={() => navigate("/dashboard")}
            >
              Volver al Dashboard
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
