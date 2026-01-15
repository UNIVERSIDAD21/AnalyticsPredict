/**
 * GraficoCurvaCalibracion.tsx — Curva de calibración con Recharts
 */

import { useMemo } from 'react';
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { BinCalibracion, RespuestaCurvaCalibracion } from '../../tipos';

interface PropsGraficoCurvaCalibracion {
  datos: RespuestaCurvaCalibracion;
}

const formatearPorcentaje = (valor: number | null | undefined) => {
  if (valor === null || valor === undefined || !isFinite(valor)) return '—';
  return `${(valor * 100).toFixed(1)}%`;
};

const formatearNumero = (valor: number | null | undefined, decimales = 3) => {
  if (valor === null || valor === undefined || !isFinite(valor)) return '—';
  return valor.toFixed(decimales);
};

function obtenerInterpretacion(
  ece: number,
  mce: number,
  bins: BinCalibracion[]
): string {
  const total = bins.reduce((acc, bin) => acc + bin.n, 0);
  const sesgoPromedio = bins.reduce((acc, bin) => acc + bin.gap_con_signo * bin.n, 0) / (total || 1);

  let estado = 'Bien calibrado';
  if (ece > 0.08) {
    estado = 'Calibración débil';
  } else if (ece > 0.05) {
    estado = 'Calibración aceptable';
  } else if (ece <= 0.02) {
    estado = 'Calibración excelente';
  }

  let sesgo = 'Sin sesgo evidente';
  if (sesgoPromedio > 0.02) {
    sesgo = 'Sobreestima (overconfidence)';
  } else if (sesgoPromedio < -0.02) {
    sesgo = 'Subestima (underconfidence)';
  }

  const alerta = mce > 0.1 ? 'Alerta de drift probable.' : 'Sin señales fuertes de drift.';

  return `${estado}. ${sesgo}. ${alerta}`;
}

function TooltipBin({
  active,
  payload,
}: {
  active?: boolean;
  payload?: Array<{ payload: BinCalibracion }>;
}) {
  if (!active || !payload?.length) return null;
  const bin = payload[0].payload;
  return (
    <div className="rounded-lg border border-neon-cyan/30 bg-futurista-oscuro/90 p-3 text-xs text-texto-secundario space-y-1">
      <div className="font-semibold text-texto-principal">
        Bin {formatearPorcentaje(bin.rango_inicio)} → {formatearPorcentaje(bin.rango_fin)}
      </div>
      <div>N: {bin.n}</div>
      <div>Prob. promedio: {formatearPorcentaje(bin.probabilidad_promedio)}</div>
      <div>Frecuencia real: {formatearPorcentaje(bin.frecuencia_real)}</div>
      <div>Gap abs: {formatearPorcentaje(Math.abs(bin.gap))}</div>
      <div>Gap signo: {formatearPorcentaje(bin.gap_con_signo)}</div>
      {bin.advertencia && <div className="text-advertencia-500">{bin.advertencia}</div>}
    </div>
  );
}

export function GraficoCurvaCalibracion({ datos }: PropsGraficoCurvaCalibracion) {
  const puntosSistema = useMemo(
    () =>
      datos.bins.map((bin) => ({
        ...bin,
        prob: bin.probabilidad_promedio,
        real: bin.frecuencia_real,
      })),
    [datos.bins]
  );

  const interpretacion = useMemo(
    () => obtenerInterpretacion(datos.ece, datos.mce, datos.bins),
    [datos]
  );

  return (
    <div className="space-y-4">
      <div className="h-[320px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={puntosSistema} margin={{ top: 10, right: 20, left: -10, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 255, 255, 0.15)" />
            <XAxis
              dataKey="prob"
              type="number"
              domain={[0, 1]}
              tickFormatter={(value) => `${Math.round(value * 100)}%`}
              tick={{ fill: '#9AA4B2', fontSize: 12 }}
            />
            <YAxis
              type="number"
              domain={[0, 1]}
              tickFormatter={(value) => `${Math.round(value * 100)}%`}
              tick={{ fill: '#9AA4B2', fontSize: 12 }}
            />
            <ReferenceLine
              segment={[
                { x: 0, y: 0 },
                { x: 1, y: 1 },
              ]}
              stroke="#6B7280"
              strokeDasharray="6 4"
            />
            <Line
              type="monotone"
              dataKey="real"
              stroke="#22d3ee"
              strokeWidth={2}
              dot={{ r: 4, strokeWidth: 1, fill: '#22d3ee' }}
              activeDot={{ r: 6 }}
            />
            <Tooltip content={<TooltipBin />} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex flex-wrap items-center gap-3 text-xs text-texto-secundario">
        <span className="px-2 py-1 rounded-full border border-neon-cyan/30 text-neon-cyan">
          ECE: {formatearPorcentaje(datos.ece)}
        </span>
        <span className="px-2 py-1 rounded-full border border-neon-magenta/30 text-neon-magenta">
          MCE: {formatearPorcentaje(datos.mce)}
        </span>
        <span className="px-2 py-1 rounded-full border border-neon-verde/30 text-neon-verde">
          N total: {datos.n_predicciones_total.toLocaleString('es-ES')}
        </span>
        <span className="px-2 py-1 rounded-full border border-neon-cyan/10">
          Peor bin: {datos.bin_peor_calibrado ?? '—'}
        </span>
      </div>

      <div className="text-sm text-texto-secundario">
        <p className="text-texto-principal font-semibold">
          Interpretación
        </p>
        <p>{interpretacion}</p>
      </div>

      <div className="text-xs text-texto-terciario">
        Línea perfecta: {formatearNumero(0)} → {formatearNumero(1)}. Sistema representa promedio
        por bin de {datos.n_bins} divisiones ({datos.tipo_bins}).
      </div>
    </div>
  );
}
