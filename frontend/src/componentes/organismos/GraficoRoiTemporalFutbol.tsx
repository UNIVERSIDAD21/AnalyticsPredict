import { TrendingUp } from 'lucide-react';
import { clsx } from 'clsx';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';
import { Tarjeta } from '../atomos';

interface PropsGraficoTemporal {
  datos: { fecha: string; roi: number }[];
}

function formatearEtiquetaDia(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-ES', { day: '2-digit', month: 'short' });
}

export function GraficoRoiTemporalFutbol({ datos }: PropsGraficoTemporal) {
  const roiFinal = datos[datos.length - 1]?.roi ?? 0;
  const esPositivo = roiFinal >= 0;

  return (
    <Tarjeta className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <TrendingUp size={20} className="text-neon-cyan" />
          <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-texto-principal">
            ROI Acumulado - Ultimos 30 dias
          </h3>
        </div>
        <span
          className={clsx(
            'font-mono font-bold text-lg',
            esPositivo ? 'text-neon-verde' : 'text-neon-rojo'
          )}
        >
          {esPositivo ? '+' : ''}
          {roiFinal.toFixed(1)}%
        </span>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={datos} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorROI" x1="0" y1="0" x2="0" y2="1">
                <stop
                  offset="5%"
                  stopColor={esPositivo ? '#10b981' : '#ef4444'}
                  stopOpacity={0.3}
                />
                <stop
                  offset="95%"
                  stopColor={esPositivo ? '#10b981' : '#ef4444'}
                  stopOpacity={0}
                />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(34, 211, 238, 0.1)"
              vertical={false}
            />
            <XAxis
              dataKey="fecha"
              stroke="rgba(156, 163, 175, 0.5)"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
              tickFormatter={formatearEtiquetaDia}
            />
            <YAxis
              stroke="rgba(156, 163, 175, 0.5)"
              fontSize={10}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `${value.toFixed(0)}%`}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(15, 23, 42, 0.9)',
                border: '1px solid rgba(34, 211, 238, 0.3)',
                borderRadius: '8px',
                boxShadow: '0 0 20px rgba(34, 211, 238, 0.2)',
              }}
              labelStyle={{ color: '#9ca3af', fontSize: 12 }}
              itemStyle={{ color: esPositivo ? '#10b981' : '#ef4444' }}
              labelFormatter={(value) => formatearEtiquetaDia(String(value))}
              formatter={(value: number) => [`${value.toFixed(2)}%`, 'ROI']}
            />
            <Area
              type="monotone"
              dataKey="roi"
              stroke={esPositivo ? '#10b981' : '#ef4444'}
              strokeWidth={2}
              fill="url(#colorROI)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Tarjeta>
  );
}
