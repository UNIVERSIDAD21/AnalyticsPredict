/**
 * PanelEstadisticasEquipo.tsx — Panel desplegable con estadísticas rápidas
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp, Info } from 'lucide-react';
import { EstadisticasEquipo } from '../../tipos';

interface PropsPanelEstadisticasEquipo {
  equipoLocal?: EstadisticasEquipo;
  equipoVisitante?: EstadisticasEquipo;
  cargando?: boolean;
}

const formatoPct = (valor: number) => `${(valor * 100).toFixed(1)}%`;

export function PanelEstadisticasEquipo({
  equipoLocal,
  equipoVisitante,
  cargando = false,
}: PropsPanelEstadisticasEquipo) {
  const [abierto, setAbierto] = useState(false);

  const equipos = [
    { etiqueta: 'Local', data: equipoLocal },
    { etiqueta: 'Visitante', data: equipoVisitante },
  ];

  return (
    <div className="rounded-lg border border-neon-cyan/10 bg-futurista-oscuro/40">
      <button
        type="button"
        className="w-full flex items-center justify-between px-4 py-3 text-sm text-texto-principal hover:text-neon-cyan transition"
        onClick={() => setAbierto((prev) => !prev)}
        disabled={cargando}
      >
        <span className="flex items-center gap-2">
          <Info size={16} className="text-neon-cyan" />
          Ver estadísticas rápidas
        </span>
        {abierto ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
      </button>

      {abierto && (
        <div className="px-4 pb-4 space-y-4">
          {equipos.map(({ etiqueta, data }) => (
            <div
              key={etiqueta}
              className="rounded-lg border border-neon-cyan/10 bg-futurista-oscuro/50 p-3"
            >
              <p className="text-xs uppercase tracking-wider text-texto-terciario mb-2">
                {etiqueta}
              </p>
              {data ? (
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-texto-principal">{data.nombre}</span>
                    <span className="text-texto-secundario">
                      {data.record.victorias}-{data.record.derrotas} · {formatoPct(
                        data.record.victorias /
                          Math.max(1, data.record.victorias + data.record.derrotas)
                      )}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-texto-secundario">
                    <span>PPG Total</span>
                    <span>{data.promedios.anotados.total.toFixed(1)}</span>
                  </div>
                  <div className="flex items-center justify-between text-texto-secundario">
                    <span>OPP Total</span>
                    <span>{data.promedios.recibidos.total.toFixed(1)}</span>
                  </div>
                  <div className="flex items-center justify-between text-texto-secundario">
                    <span>Over % Total</span>
                    <span>{formatoPct(data.tendencias_over.total)}</span>
                  </div>
                  <div className="flex items-center justify-between text-texto-secundario">
                    <span>Racha</span>
                    <span className="font-mono">{data.racha.join('-')}</span>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-texto-terciario">
                  Selecciona un equipo para ver estadísticas.
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
