/**
 * Minimal SVG sparkline (no client JS). Renders a smooth line + soft area fill.
 * `data` is any numeric series; it is normalized to the viewbox internally.
 */
export function Sparkline({
  data,
  width = 120,
  height = 36,
  className = "text-brand",
  id,
}: {
  data: number[];
  width?: number;
  height?: number;
  className?: string;
  id: string;
}) {
  if (data.length < 2) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const pad = 2;
  const w = width - pad * 2;
  const h = height - pad * 2;

  const points = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * w;
    const y = pad + h - ((v - min) / range) * h;
    return [x, y] as const;
  });

  const line = points.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const area = `${pad},${height - pad} ${line} ${width - pad},${height - pad}`;
  const gradId = `spark-${id}`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className={className}
      preserveAspectRatio="none"
      aria-hidden
    >
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="currentColor" stopOpacity="0.25" />
          <stop offset="100%" stopColor="currentColor" stopOpacity="0" />
        </linearGradient>
      </defs>
      <polygon points={area} fill={`url(#${gradId})`} />
      <polyline
        points={line}
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

/** Deterministic, smooth pseudo-series for illustrative sparklines. */
export function seededSeries(seed: number, points = 16): number[] {
  let s = (seed % 1000) + 1;
  const rand = () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff;
    return s / 0x7fffffff;
  };
  const out: number[] = [];
  let v = 0.5;
  for (let i = 0; i < points; i++) {
    v += (rand() - 0.45) * 0.25;
    v = Math.max(0.1, Math.min(0.95, v));
    out.push(v);
  }
  return out;
}
