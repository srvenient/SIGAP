import { Link } from "react-router";

export default function CatchAll() {
  return (
    <main className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-sm text-center">
        <p className="text-sm text-text-muted tabular-nums">Error 404</p>
        <h1 className="mt-1.5 text-xl font-semibold tracking-tight">Esta página no existe</h1>
        <p className="mt-1.5 text-sm text-text-secondary">Puede que la dirección esté mal escrita.</p>
        <Link to="/" className="btn-primary mt-5">
          Ir al inicio
        </Link>
      </div>
    </main>
  );
}
