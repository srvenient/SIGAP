import React, { useEffect, useRef, useState } from "react";
import { Link } from "react-router";
import { ArrowLeft, CheckCircle2, CreditCard, Landmark, Loader2, Smartphone, XCircle } from "lucide-react";
import { Brand } from "../../components/ui/Brand";
import { Button } from "../../components/ui/Button";
import { Plate } from "../../components/ui/Plate";
import { ApiError } from "../../services/api";
import { publicApi } from "../../services/operations";
import { PAYMENT_METHODS, VEHICLE_LABELS, duration, money } from "../../lib/format";
import type { PaymentMethods, PaymentState, Quote } from "../../types/operations";

const POLL_MS = 2000;
const METHOD_ICONS: Record<string, typeof CreditCard> = { card: CreditCard, pse: Landmark, nequi: Smartphone };

type Step =
  | { name: "plate" }
  | { name: "quote"; quote: Quote }
  | { name: "processing"; payment: PaymentState }
  | { name: "approved"; payment: PaymentState }
  | { name: "failed"; payment: PaymentState };

const errorText = (err: unknown) =>
  err instanceof ApiError ? err.message : "No pudimos conectar con el sistema. Inténtalo de nuevo.";

export default function PaymentModule() {
  const [step, setStep] = useState<Step>({ name: "plate" });
  const [plate, setPlate] = useState("");
  const [methods, setMethods] = useState<PaymentMethods | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    publicApi.methods().then(setMethods).catch(() => setMethods(null));
  }, []);

  const reset = () => {
    setStep({ name: "plate" });
    setPlate("");
    setError(null);
  };

  const run = async (action: () => Promise<void>) => {
    setBusy(true);
    setError(null);
    try {
      await action();
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  };

  const showQuote = () => run(async () => setStep({ name: "quote", quote: await publicApi.quote(plate) }));

  const pay = (method: string) =>
    run(async () => setStep({ name: "processing", payment: await publicApi.startPayment(plate, method) }));

  return (
    <div className="min-h-screen flex flex-col">
      <header className="h-16 shrink-0 px-5 sm:px-8 flex items-center justify-between border-b border-border-primary">
        <Brand subtitle="Módulo de pago" />
        <Link to="/" className="text-sm text-text-muted hover:text-text-primary">
          Personal autorizado
        </Link>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-md card p-6 sm:p-8">
          {error && (
            <p role="alert" className="mb-5 rounded-md border border-status-error-border bg-status-error-soft px-3 py-2 text-center text-sm text-status-error">
              {error}
            </p>
          )}

          {step.name === "plate" && (
            <PlateStep plate={plate} onChange={setPlate} onSubmit={showQuote} busy={busy} />
          )}
          {step.name === "quote" && (
            <QuoteStep quote={step.quote} methods={methods} onPay={pay} onBack={reset} busy={busy} />
          )}
          {step.name === "processing" && (
            <ProcessingStep
              payment={step.payment}
              onResolved={(payment) =>
                setStep(payment.status === "approved" ? { name: "approved", payment } : { name: "failed", payment })
              }
            />
          )}
          {step.name === "approved" && <ApprovedStep payment={step.payment} onDone={reset} />}
          {step.name === "failed" && (
            <FailedStep payment={step.payment} onRetry={showQuote} onCancel={reset} busy={busy} />
          )}
        </div>
      </main>
    </div>
  );
}

function PlateStep({
  plate,
  onChange,
  onSubmit,
  busy,
}: {
  plate: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  busy: boolean;
}) {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (plate.length === 6) onSubmit();
  };

  return (
    <form onSubmit={handleSubmit} className="text-center space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Paga tu parqueo</h1>
        <p className="mt-1 text-sm text-text-muted">Escribe la placa de tu vehículo para consultar el valor.</p>
      </div>
      <label htmlFor="plate" className="sr-only">
        Placa del vehículo
      </label>
      <input
        id="plate"
        autoFocus
        autoComplete="off"
        spellCheck={false}
        value={plate}
        onChange={(e) => onChange(e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 6))}
        placeholder="ABC123"
        className="w-full block text-center rounded-lg bg-plate text-ink placeholder:text-ink/25 font-mono font-semibold text-5xl tracking-widest py-4 outline-none ring-1 ring-inset ring-black/35 focus:ring-4 focus:ring-inset focus:ring-steel"
      />
      <Button type="submit" size="lg" disabled={plate.length !== 6} isLoading={busy} className="w-full">
        Consultar valor
      </Button>
    </form>
  );
}

function QuoteStep({
  quote,
  methods,
  onPay,
  onBack,
  busy,
}: {
  quote: Quote;
  methods: PaymentMethods | null;
  onPay: (method: string) => void;
  onBack: () => void;
  busy: boolean;
}) {
  if (quote.status === "paid") {
    return (
      <div className="text-center space-y-5">
        <CheckCircle2 className="w-10 h-10 mx-auto text-status-success" strokeWidth={1.5} />
        <Plate value={quote.plate} size="lg" />
        <h1 className="text-xl font-semibold tracking-tight">Este vehículo ya está pago</h1>
        <p className="text-text-secondary">Puedes dirigirte a la salida.</p>
        <Button variant="outline" onClick={onBack}>
          Volver
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-5">
        <Plate value={quote.plate} size="lg" />
        <div>
          <p className="text-sm text-text-muted">Total a pagar</p>
          <p className="mt-1 text-5xl font-semibold tabular-nums tracking-tight">{money(quote.amount)}</p>
          <p className="mt-2 text-sm text-text-secondary">
            {VEHICLE_LABELS[quote.vehicle_type]} · {duration(quote.minutes)}
            {quote.charge_mode === "full_rate" &&
              ` · tarifa plena${quote.periods > 1 ? ` × ${quote.periods}` : ""}`}
          </p>
        </div>
      </div>

      <div className="space-y-2">
        <p className="text-sm text-text-secondary">Elige cómo pagar</p>
        <div className="space-y-2">
          {methods?.methods.map((method) => {
            const Icon = METHOD_ICONS[method.code] ?? CreditCard;
            return (
              <button
                key={method.code}
                disabled={busy}
                onClick={() => onPay(method.code)}
                className="w-full h-12 px-4 flex items-center gap-3 rounded-md border border-border-primary hover:border-border-strong hover:bg-bg-accent text-sm font-medium transition-colors cursor-pointer disabled:opacity-50"
              >
                <Icon className="w-4.5 h-4.5 text-text-secondary" />
                {method.label}
              </button>
            );
          })}
        </div>
      </div>

      <button onClick={onBack} className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary cursor-pointer">
        <ArrowLeft className="w-4 h-4" />
        Cambiar placa
      </button>
    </div>
  );
}

function ProcessingStep({
  payment,
  onResolved,
}: {
  payment: PaymentState;
  onResolved: (payment: PaymentState) => void;
}) {
  const [busy, setBusy] = useState(false);
  const onResolvedRef = useRef(onResolved);
  onResolvedRef.current = onResolved;

  useEffect(() => {
    const timer = setInterval(async () => {
      try {
        const state = await publicApi.paymentState(payment.reference);
        if (state.status !== "pending") onResolvedRef.current(state);
      } catch {
        // Un fallo puntual de red no debe interrumpir la espera: el siguiente ciclo reintenta
      }
    }, POLL_MS);
    return () => clearInterval(timer);
  }, [payment.reference]);

  const resolveWith = async (action: () => Promise<PaymentState>) => {
    setBusy(true);
    try {
      onResolved(await action());
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="text-center space-y-5">
      <Loader2 className="w-9 h-9 mx-auto animate-spin text-steel" />
      <h1 className="text-xl font-semibold tracking-tight">Procesando pago</h1>
      <div className="text-sm text-text-secondary space-y-1">
        <p className="text-3xl font-semibold tabular-nums tracking-tight text-text-primary">{money(payment.amount)}</p>
        <p>{PAYMENT_METHODS[payment.method] ?? payment.method}</p>
        <p className="text-xs font-mono break-all text-text-muted">Referencia: {payment.reference}</p>
      </div>

      {payment.simulated && (
        <div className="rounded-md border border-dashed border-border-strong p-4 space-y-3">
          <p className="text-xs text-text-muted">Pasarela simulada: no se cobra dinero real</p>
          <div className="flex gap-2 justify-center">
            <Button
              variant="success"
              disabled={busy}
              onClick={() => resolveWith(() => publicApi.simulatePayment(payment.reference, "approved"))}
            >
              Aprobar
            </Button>
            <Button
              variant="danger"
              disabled={busy}
              onClick={() => resolveWith(() => publicApi.simulatePayment(payment.reference, "rejected"))}
            >
              Rechazar
            </Button>
          </div>
        </div>
      )}

      <button
        disabled={busy}
        onClick={() => resolveWith(() => publicApi.cancelPayment(payment.reference))}
        className="text-sm text-text-muted hover:text-text-primary underline underline-offset-2 cursor-pointer"
      >
        Cancelar pago
      </button>
    </div>
  );
}

function ApprovedStep({ payment, onDone }: { payment: PaymentState; onDone: () => void }) {
  return (
    <div className="text-center space-y-5">
      <CheckCircle2 className="w-11 h-11 mx-auto text-status-success" strokeWidth={1.5} />
      <h1 className="text-2xl font-semibold tracking-tight">Pago aprobado</h1>
      <Plate value={payment.plate} size="lg" />
      <p className="text-sm text-text-secondary">Ya puedes dirigirte a la salida.</p>
      <Button variant="outline" onClick={onDone}>
        Terminar
      </Button>
    </div>
  );
}

function FailedStep({
  payment,
  onRetry,
  onCancel,
  busy,
}: {
  payment: PaymentState;
  onRetry: () => void;
  onCancel: () => void;
  busy: boolean;
}) {
  return (
    <div className="text-center space-y-5">
      <XCircle className="w-11 h-11 mx-auto text-status-error" strokeWidth={1.5} />
      <h1 className="text-xl font-semibold tracking-tight">El pago no se completó</h1>
      <p className="text-sm text-text-secondary">{payment.failure_reason}</p>
      <div className="flex flex-col sm:flex-row gap-2 justify-center">
        <Button onClick={onRetry} isLoading={busy}>
          Intentar de nuevo
        </Button>
        <Button variant="outline" onClick={onCancel}>
          Salir
        </Button>
      </div>
    </div>
  );
}
