const SIZES = {
  sm: "text-xs px-1.5 py-0.5 rounded-[3px]",
  md: "text-sm px-2 py-1 rounded",
  lg: "text-3xl px-5 py-2.5 rounded-md",
  xl: "text-6xl sm:text-8xl px-8 py-4 rounded-lg",
};

export function formatPlate(plate: string): string {
  return plate.length === 6 ? `${plate.slice(0, 3)} ${plate.slice(3)}` : plate;
}

/** La placa colombiana: único elemento amarillo de la interfaz. */
export function Plate({ value, size = "md" }: { value: string; size?: keyof typeof SIZES }) {
  return (
    <span
      className={`inline-block bg-plate text-ink font-mono font-semibold tracking-wider leading-none whitespace-nowrap ring-1 ring-inset ring-black/35 ${SIZES[size]}`}
      aria-label={`Placa ${value}`}
    >
      {formatPlate(value)}
    </span>
  );
}
