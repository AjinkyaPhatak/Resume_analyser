"use client";

// Small SVG charts for the research page. Conventions (dataviz skill): thin marks, 2px
// lines, >= 8px markers with a surface ring, recessive grid, text in ink tokens (never
// the series colour), a hover tooltip on every chart, and a legend whenever colour
// carries meaning (identity is also given by labels).

import { useState, type ReactNode } from "react";

type Scale = (v: number) => number;
const linear = (d0: number, d1: number, r0: number, r1: number): Scale => (v) =>
  r0 + ((v - d0) / (d1 - d0 || 1)) * (r1 - r0);

function ticks(lo: number, hi: number, n = 5): number[] {
  const span = hi - lo || 1;
  const raw = span / n;
  const mag = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((s) => span / s <= n) ?? raw;
  const out: number[] = [];
  for (let v = Math.ceil(lo / step) * step; v <= hi + step * 1e-6; v += step) out.push(Number(v.toFixed(10)));
  return out;
}

const fmt = (v: number, digits = 2) => (Math.abs(v) < 1e-9 ? "0" : v.toFixed(digits));

function Tooltip({ x, y, w, h, children }: { x: number; y: number; w: number; h: number; children: ReactNode }) {
  const left = (x / w) * 100;
  const top = (y / h) * 100;
  const flip = left > 60;
  return (
    <div
      className="pointer-events-none absolute z-10 rounded-md border border-line bg-surface px-3 py-2 text-xs shadow-lg"
      style={{
        left: `${left}%`,
        top: `${top}%`,
        transform: `translate(${flip ? "calc(-100% - 12px)" : "12px"}, -50%)`,
        minWidth: 150,
      }}
    >
      {children}
    </div>
  );
}

// charts keep a readable minimum width and scroll sideways on phones instead of shrinking text
function Frame({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto">
      <div className="relative min-w-[560px]">{children}</div>
    </div>
  );
}

export function Legend({ items }: { items: { label: string; color: string; dashed?: boolean }[] }) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
      {items.map((i) => (
        <span key={i.label} className="inline-flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: i.color }} />
          {i.label}
        </span>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- scatter with 2-D CIs

export interface ScatterPoint {
  id: string;
  label: string;
  color: string;
  x: [number, number, number];
  y: [number, number, number];
  emphasis?: boolean;
  labelPos?: "right" | "left" | "above" | "below";
  detail?: ReactNode;
}

export function ScatterCI({
  points,
  xLabel,
  yLabel,
  xDomain,
  yDomain,
  note,
}: {
  points: ScatterPoint[];
  xLabel: string;
  yLabel: string;
  xDomain: [number, number];
  yDomain: [number, number];
  note?: string;
}) {
  const W = 720, H = 420, m = { l: 64, r: 24, t: 16, b: 52 };
  const sx = linear(xDomain[0], xDomain[1], m.l, W - m.r);
  const sy = linear(yDomain[0], yDomain[1], H - m.b, m.t);
  const [hover, setHover] = useState<string | null>(null);
  const hp = points.find((p) => p.id === hover);
  return (
    <Frame>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={`${yLabel} against ${xLabel}`}>
        {ticks(...xDomain, 6).map((t) => (
          <g key={`x${t}`}>
            <line x1={sx(t)} x2={sx(t)} y1={m.t} y2={H - m.b} stroke="var(--grid)" />
            <text x={sx(t)} y={H - m.b + 18} textAnchor="middle" className="fill-muted tabular" fontSize={11}>
              {fmt(t)}
            </text>
          </g>
        ))}
        {ticks(...yDomain, 5).map((t) => (
          <g key={`y${t}`}>
            <line x1={m.l} x2={W - m.r} y1={sy(t)} y2={sy(t)} stroke="var(--grid)" />
            <text x={m.l - 8} y={sy(t) + 4} textAnchor="end" className="fill-muted tabular" fontSize={11}>
              {fmt(t)}
            </text>
          </g>
        ))}
        <line x1={m.l} x2={W - m.r} y1={H - m.b} y2={H - m.b} stroke="var(--axis)" />
        <text x={(m.l + W - m.r) / 2} y={H - 10} textAnchor="middle" className="fill-ink-2" fontSize={12}>
          {xLabel}
        </text>
        <text transform={`translate(16 ${(m.t + H - m.b) / 2}) rotate(-90)`} textAnchor="middle" className="fill-ink-2" fontSize={12}>
          {yLabel}
        </text>
        {points.map((p) => {
          const dim = hover && hover !== p.id;
          const cx = sx(p.x[0]), cy = sy(p.y[0]);
          const pos = p.labelPos ?? "right";
          const lx = pos === "right" ? cx + 10 : pos === "left" ? cx - 10 : cx;
          const ly = pos === "above" ? cy - 12 : pos === "below" ? cy + 18 : cy + 4;
          const anchor = pos === "right" ? "start" : pos === "left" ? "end" : "middle";
          return (
            <g key={p.id} opacity={dim ? 0.3 : 1} onMouseEnter={() => setHover(p.id)} onMouseLeave={() => setHover(null)}>
              <line x1={sx(p.x[1])} x2={sx(p.x[2])} y1={cy} y2={cy} stroke={p.color} strokeWidth={2} />
              <line x1={cx} x2={cx} y1={sy(p.y[1])} y2={sy(p.y[2])} stroke={p.color} strokeWidth={2} />
              <circle cx={cx} cy={cy} r={p.emphasis ? 7 : 5.5} fill={p.color} stroke="var(--surface)" strokeWidth={2} />
              <circle cx={cx} cy={cy} r={18} fill="transparent" />
              <text x={lx} y={ly} textAnchor={anchor} fontSize={12} fontWeight={p.emphasis ? 600 : 400} className="fill-ink"
                stroke="var(--page)" strokeWidth={4} paintOrder="stroke" strokeLinejoin="round">
                {p.label}
              </text>
            </g>
          );
        })}
      </svg>
      {hp && (
        <Tooltip x={sx(hp.x[0])} y={sy(hp.y[0])} w={W} h={H}>
          <div className="mb-1 font-semibold text-ink">{hp.label}</div>
          <div className="tabular text-ink-2">
            {xLabel}: {hp.x[0].toFixed(3)} [{hp.x[1].toFixed(3)}, {hp.x[2].toFixed(3)}]
          </div>
          <div className="tabular text-ink-2">
            {yLabel}: {hp.y[0].toFixed(3)} [{hp.y[1].toFixed(3)}, {hp.y[2].toFixed(3)}]
          </div>
          {hp.detail}
        </Tooltip>
      )}
      {note && <p className="mt-1 text-xs text-muted">{note}</p>}
    </Frame>
  );
}

// ---------------------------------------------------------------- forest plot (dot + CI)

export interface ForestRow {
  id: string;
  label: string;
  color: string;
  ci: [number, number, number] | null;
  emphasis?: boolean;
  note?: string;
}

export function ForestPlot({
  rows,
  xLabel,
  domain,
  digits = 3,
  zeroLine = false,
}: {
  rows: ForestRow[];
  xLabel: string;
  domain?: [number, number];
  digits?: number;
  zeroLine?: boolean;
}) {
  const vals = rows.flatMap((r) => (r.ci ? [r.ci[1], r.ci[2]] : []));
  const lo = domain?.[0] ?? Math.min(0, ...vals);
  const hi = domain?.[1] ?? Math.max(...vals) * 1.08;
  const rowH = 30, W = 720, m = { l: 190, r: 90, t: 8, b: 40 };
  const H = m.t + rows.length * rowH + m.b;
  const sx = linear(lo, hi, m.l, W - m.r);
  const [hover, setHover] = useState<string | null>(null);
  const hr = rows.find((r) => r.id === hover);
  const hi_idx = rows.findIndex((r) => r.id === hover);
  return (
    <Frame>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={xLabel}>
        {ticks(lo, hi, 5).map((t) => (
          <g key={t}>
            <line x1={sx(t)} x2={sx(t)} y1={m.t} y2={H - m.b} stroke="var(--grid)" />
            <text x={sx(t)} y={H - m.b + 16} textAnchor="middle" fontSize={11} className="fill-muted tabular">
              {fmt(t, digits > 2 ? 2 : digits)}
            </text>
          </g>
        ))}
        {zeroLine && lo < 0 && <line x1={sx(0)} x2={sx(0)} y1={m.t} y2={H - m.b} stroke="var(--axis)" strokeWidth={1.5} />}
        <text x={(m.l + W - m.r) / 2} y={H - 6} textAnchor="middle" fontSize={12} className="fill-ink-2">
          {xLabel}
        </text>
        {rows.map((r, i) => {
          const y = m.t + i * rowH + rowH / 2;
          return (
            <g key={r.id} onMouseEnter={() => setHover(r.id)} onMouseLeave={() => setHover(null)} opacity={hover && hover !== r.id ? 0.35 : 1}>
              <rect x={0} y={y - rowH / 2} width={W} height={rowH} fill={hover === r.id ? "var(--surface-2)" : "transparent"} />
              <text x={m.l - 12} y={y + 4} textAnchor="end" fontSize={12} fontWeight={r.emphasis ? 600 : 400} className="fill-ink">
                {r.label}
              </text>
              {r.ci ? (
                <>
                  <line x1={sx(r.ci[1])} x2={sx(r.ci[2])} y1={y} y2={y} stroke={r.color} strokeWidth={2} strokeLinecap="round" />
                  <circle cx={sx(r.ci[0])} cy={y} r={r.emphasis ? 6.5 : 5} fill={r.color} stroke="var(--surface)" strokeWidth={2} />
                  <text x={W - m.r + 10} y={y + 4} fontSize={11} className="fill-ink-2 tabular">
                    {r.ci[0].toFixed(digits)}
                  </text>
                </>
              ) : (
                <text x={m.l} y={y + 4} fontSize={11} className="fill-muted">
                  not available
                </text>
              )}
            </g>
          );
        })}
      </svg>
      {hr && hr.ci && (
        <Tooltip x={sx(hr.ci[0])} y={m.t + hi_idx * rowH + rowH / 2} w={W} h={H}>
          <div className="font-semibold text-ink">{hr.label}</div>
          <div className="tabular text-ink-2">
            {hr.ci[0].toFixed(digits)} [95% CI {hr.ci[1].toFixed(digits)}, {hr.ci[2].toFixed(digits)}]
          </div>
          {hr.note && <div className="mt-1 text-muted">{hr.note}</div>}
        </Tooltip>
      )}
    </Frame>
  );
}

// ---------------------------------------------------------------- line chart with crosshair

export interface LineSeries {
  id: string;
  label: string;
  color: string;
  points: { x: number; y: number }[];
  dashed?: boolean;
}

export function LineChart({
  series,
  xLabel,
  yLabel,
  yDomain,
  digits = 3,
  markX,
}: {
  series: LineSeries[];
  xLabel: string;
  yLabel: string;
  yDomain?: [number, number];
  digits?: number;
  markX?: Record<string, number>;
}) {
  const W = 720, H = 300, m = { l: 56, r: 24, t: 12, b: 44 };
  const xs = series.flatMap((s) => s.points.map((p) => p.x));
  const ys = series.flatMap((s) => s.points.map((p) => p.y));
  const x0 = Math.min(...xs), x1 = Math.max(...xs);
  const [y0, y1] = yDomain ?? [Math.min(...ys), Math.max(...ys)];
  const sx = linear(x0, x1, m.l, W - m.r);
  const sy = linear(y0, y1, H - m.b, m.t);
  const [hx, setHx] = useState<number | null>(null);
  const onMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const vx = ((e.clientX - r.left) / r.width) * W;
    const xv = x0 + ((vx - m.l) / (W - m.l - m.r)) * (x1 - x0);
    setHx(Math.min(x1, Math.max(x0, Math.round(xv))));
  };
  // series can end at different x (early stopping), so identity comes from a legend, not end labels
  return (
    <Frame>
      {series.length > 1 && <Legend items={series.map((s) => ({ label: s.label, color: s.color }))} />}
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" onMouseMove={onMove} onMouseLeave={() => setHx(null)} role="img" aria-label={yLabel}>
        {ticks(y0, y1, 5).map((t) => (
          <g key={t}>
            <line x1={m.l} x2={W - m.r} y1={sy(t)} y2={sy(t)} stroke="var(--grid)" />
            <text x={m.l - 8} y={sy(t) + 4} textAnchor="end" fontSize={11} className="fill-muted tabular">
              {fmt(t)}
            </text>
          </g>
        ))}
        {ticks(x0, x1, Math.min(10, x1 - x0)).map((t) => (
          <text key={t} x={sx(t)} y={H - m.b + 18} textAnchor="middle" fontSize={11} className="fill-muted tabular">
            {t}
          </text>
        ))}
        <line x1={m.l} x2={W - m.r} y1={H - m.b} y2={H - m.b} stroke="var(--axis)" />
        <text x={(m.l + W - m.r) / 2} y={H - 8} textAnchor="middle" fontSize={12} className="fill-ink-2">
          {xLabel}
        </text>
        <text transform={`translate(14 ${(m.t + H - m.b) / 2}) rotate(-90)`} textAnchor="middle" fontSize={12} className="fill-ink-2">
          {yLabel}
        </text>
        {hx != null && <line x1={sx(hx)} x2={sx(hx)} y1={m.t} y2={H - m.b} stroke="var(--axis)" />}
        {series.map((s) => {
          const d = s.points.map((p, i) => `${i ? "L" : "M"}${sx(p.x)},${sy(p.y)}`).join("");
          const best = markX?.[s.id];
          const bp = s.points.find((p) => p.x === best);
          return (
            <g key={s.id}>
              <path d={d} fill="none" stroke={s.color} strokeWidth={2} strokeDasharray={s.dashed ? "5 4" : undefined} />
              {s.points.map((p) => (
                <circle key={p.x} cx={sx(p.x)} cy={sy(p.y)} r={hx === p.x ? 5 : 3} fill={s.color} stroke="var(--surface)" strokeWidth={1.5} />
              ))}
              {bp && <circle cx={sx(bp.x)} cy={sy(bp.y)} r={8} fill="none" stroke={s.color} strokeWidth={1.5} />}
            </g>
          );
        })}
      </svg>
      {hx != null && (
        <Tooltip x={sx(hx)} y={m.t + 40} w={W} h={H}>
          <div className="mb-1 font-semibold text-ink">
            {xLabel} {hx}
          </div>
          {series.map((s) => {
            const p = s.points.find((q) => q.x === hx);
            return p ? (
              <div key={s.id} className="flex items-center justify-between gap-4 tabular text-ink-2">
                <span className="inline-flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
                  {s.label}
                </span>
                <span>{p.y.toFixed(digits)}</span>
              </div>
            ) : null;
          })}
        </Tooltip>
      )}
    </Frame>
  );
}

// ---------------------------------------------------------------- horizontal bars

export interface BarRow {
  id: string;
  label: string;
  values: { key: string; value: number; color: string }[];
  emphasis?: boolean;
}

export function HBars({
  rows,
  xLabel,
  max,
  digits = 3,
  ci,
  labelWidth = 190,
}: {
  rows: BarRow[];
  xLabel: string;
  max?: number;
  digits?: number;
  ci?: Record<string, [number, number]>;
  labelWidth?: number;
}) {
  const nv = Math.max(...rows.map((r) => r.values.length));
  const barH = 12, gap = 2, rowH = nv * (barH + gap) + 14;
  const W = 720, m = { l: labelWidth, r: 70, t: 6, b: 40 };
  const H = m.t + rows.length * rowH + m.b;
  const top = max ?? Math.max(...rows.flatMap((r) => r.values.map((v) => v.value))) * 1.05;
  const sx = linear(0, top, m.l, W - m.r);
  const [hover, setHover] = useState<string | null>(null);
  const hi = rows.findIndex((r) => r.id === hover);
  return (
    <Frame>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label={xLabel}>
        {ticks(0, top, 5).map((t) => (
          <g key={t}>
            <line x1={sx(t)} x2={sx(t)} y1={m.t} y2={H - m.b} stroke="var(--grid)" />
            <text x={sx(t)} y={H - m.b + 16} textAnchor="middle" fontSize={11} className="fill-muted tabular">
              {fmt(t)}
            </text>
          </g>
        ))}
        <text x={(m.l + W - m.r) / 2} y={H - 6} textAnchor="middle" fontSize={12} className="fill-ink-2">
          {xLabel}
        </text>
        {rows.map((r, i) => {
          const y0 = m.t + i * rowH + 7;
          return (
            <g key={r.id} onMouseEnter={() => setHover(r.id)} onMouseLeave={() => setHover(null)} opacity={hover && hover !== r.id ? 0.4 : 1}>
              <rect x={0} y={y0 - 7} width={W} height={rowH} fill="transparent" />
              <text x={m.l - 12} y={y0 + (r.values.length * (barH + gap)) / 2 + 3} textAnchor="end" fontSize={12} fontWeight={r.emphasis ? 600 : 400} className="fill-ink">
                {r.label}
              </text>
              {r.values.map((v, j) => {
                const y = y0 + j * (barH + gap);
                const w = Math.max(0, sx(v.value) - m.l);
                return (
                  <g key={v.key}>
                    {/* rounded data end, square at the baseline */}
                    <path d={`M${m.l},${y}h${Math.max(0, w - 4)}a4,4 0 0 1 4,4v${barH - 8}a4,4 0 0 1 -4,4h${-Math.max(0, w - 4)}z`} fill={v.color} />
                    <text x={Math.max(m.l + w, ci?.[r.id] ? sx(ci[r.id][1]) : 0) + 6} y={y + barH - 2} fontSize={11} className="fill-ink-2 tabular">
                      {v.value.toFixed(digits)}
                    </text>
                  </g>
                );
              })}
              {ci?.[r.id] && (
                <line x1={sx(ci[r.id][0])} x2={sx(ci[r.id][1])} y1={y0 + barH / 2} y2={y0 + barH / 2} stroke="var(--ink-2)" strokeWidth={1.5} />
              )}
            </g>
          );
        })}
      </svg>
      {hi >= 0 && (
        <Tooltip x={sx(Math.max(...rows[hi].values.map((v) => v.value)))} y={m.t + hi * rowH + rowH / 2} w={W} h={H}>
          <div className="mb-1 font-semibold text-ink">{rows[hi].label}</div>
          {rows[hi].values.map((v) => (
            <div key={v.key} className="flex justify-between gap-4 tabular text-ink-2">
              <span className="inline-flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full" style={{ background: v.color }} />
                {v.key}
              </span>
              <span>{v.value.toFixed(digits)}</span>
            </div>
          ))}
          {ci?.[rows[hi].id] && (
            <div className="tabular text-muted">
              95% CI {ci[rows[hi].id][0].toFixed(digits)}–{ci[rows[hi].id][1].toFixed(digits)}
            </div>
          )}
        </Tooltip>
      )}
    </Frame>
  );
}

// ---------------------------------------------------------------- heatmap (near-miss bands)

export function BandHeatmap({
  cells,
  marks,
  minN,
}: {
  cells: { lo: number; hi: number; n: number; lenient: number | null }[];
  marks: { label: string; lo: number; hi: number }[];
  minN: number;
}) {
  const los = [...new Set(cells.map((c) => c.lo))].sort((a, b) => a - b);
  const his = [...new Set(cells.map((c) => c.hi))].sort((a, b) => a - b);
  const W = 720, m = { l: 56, r: 120, t: 10, b: 48 };
  const cw = (W - m.l - m.r) / los.length;
  const ch = cw * 0.62;
  const H = m.t + his.length * ch + m.b;
  const ramp = ["var(--seq-1)", "var(--seq-2)", "var(--seq-3)", "var(--seq-4)", "var(--seq-5)"];
  const vmax = Math.max(...cells.map((c) => c.lenient ?? 0));
  const color = (v: number) => ramp[Math.min(ramp.length - 1, Math.floor((v / (vmax || 1)) * ramp.length))];
  const [hover, setHover] = useState<{ lo: number; hi: number } | null>(null);
  const hc = hover && cells.find((c) => c.lo === hover.lo && c.hi === hover.hi);
  const cx = (lo: number) => m.l + los.indexOf(lo) * cw;
  const cy = (hi: number) => m.t + (his.length - 1 - his.indexOf(hi)) * ch;
  return (
    <Frame>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Suggestion precision by similarity band">
        {cells.map((c) => {
          const valid = c.lenient != null && c.n > 0;
          return (
            <rect
              key={`${c.lo}-${c.hi}`}
              x={cx(c.lo) + 1}
              y={cy(c.hi) + 1}
              width={cw - 2}
              height={ch - 2}
              rx={2}
              fill={valid ? color(c.lenient!) : "var(--surface-2)"}
              opacity={valid && c.n < minN ? 0.45 : 1}
              onMouseEnter={() => setHover({ lo: c.lo, hi: c.hi })}
              onMouseLeave={() => setHover(null)}
            />
          );
        })}
        {marks.map((mk) => (
          <g key={mk.label}>
            <rect x={cx(mk.lo)} y={cy(mk.hi)} width={cw} height={ch} fill="none" stroke="var(--ink)" strokeWidth={2} rx={2} />
            <text x={cx(mk.lo) + cw / 2} y={cy(mk.hi) - 4} textAnchor="middle" fontSize={11} fontWeight={600} className="fill-ink">
              {mk.label}
            </text>
          </g>
        ))}
        {los.filter((_, i) => i % 2 === 0).map((lo) => (
          <text key={lo} x={cx(lo) + cw / 2} y={H - m.b + 16} textAnchor="middle" fontSize={11} className="fill-muted tabular">
            {lo.toFixed(2)}
          </text>
        ))}
        {his.filter((_, i) => i % 2 === 0).map((hi) => (
          <text key={hi} x={m.l - 6} y={cy(hi) + ch / 2 + 4} textAnchor="end" fontSize={11} className="fill-muted tabular">
            {hi.toFixed(2)}
          </text>
        ))}
        <text x={(m.l + W - m.r) / 2} y={H - 8} textAnchor="middle" fontSize={12} className="fill-ink-2">
          band lower bound (cosine similarity)
        </text>
        <text transform={`translate(14 ${(m.t + H - m.b) / 2}) rotate(-90)`} textAnchor="middle" fontSize={12} className="fill-ink-2">
          band upper bound
        </text>
        {ramp.map((c, i) => (
          <g key={c}>
            <rect x={W - m.r + 24} y={m.t + i * 22} width={16} height={18} rx={2} fill={c} />
            <text x={W - m.r + 46} y={m.t + i * 22 + 13} fontSize={11} className="fill-ink-2 tabular">
              {((i / ramp.length) * vmax).toFixed(2)}+
            </text>
          </g>
        ))}
        <text x={W - m.r + 24} y={m.t + ramp.length * 22 + 14} fontSize={11} className="fill-muted">
          precision
        </text>
      </svg>
      {hc && (
        <Tooltip x={cx(hc.lo) + cw / 2} y={cy(hc.hi) + ch / 2} w={W} h={H}>
          <div className="font-semibold text-ink">
            band {hc.lo.toFixed(2)}–{hc.hi.toFixed(2)}
          </div>
          <div className="tabular text-ink-2">lenient precision: {hc.lenient == null ? "–" : hc.lenient.toFixed(3)}</div>
          <div className="tabular text-ink-2">dev suggestions: {hc.n}</div>
          {hc.n < minN && <div className="text-muted">fewer than {minN}: not eligible</div>}
        </Tooltip>
      )}
    </Frame>
  );
}
