/**
 * TarjetaCombinada.tsx — Tarjeta para combinadas en bitácora
 */

import { useState } from 'react';
import { ChevronDown, ChevronUp, Trash2 } from 'lucide-react';
import { RegistroBitacoraUnificada } from '../../tipos';
import { Boton } from '../atomos';
import { IndicadorCorrelacion } from '../moleculas';
import { ListaSelecciones } from './ListaSelecciones';

interface PropsTarjetaCombinada {
  combinada: RegistroBitacoraUnificada;
  onEliminar: () => void;
}

const estilosEstado: Record<string, string> = {
  GANADA: 'text-neon-verde',
  PERDIDA: 'text-neon-rojo',
  PUSH: 'text-advertencia-500',
  PENDIENTE: 'text-neon-cyan',
};

export function TarjetaCombinada({ combinada, onEliminar }: PropsTarjetaCombinada) {
  const [expandida, setExpandida] = useState(false);
  const total = combinada.n_selecciones ?? 0;
  const resueltas = (combinada.selecciones_ganadas ?? 0) + (combinada.selecciones_perdidas ?? 0)
    + (combinada.selecciones_push ?? 0);

  return (
    <div className="tarjeta p-4 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-widest text-texto-terciario">COMBINADA</p>
          <h4 className="text-lg font-semibold text-texto-principal flex items-center gap-2">
            🎰 Parlay ({total} legs)
          </h4>
          <p className="text-sm text-texto-secundario">
            Cuota total @ {combinada.cuota_total} · Stake ${combinada.stake}
          </p>
        </div>
        <div className="text-right space-y-2">
          <p className={`text-sm font-semibold ${estilosEstado[combinada.resultado] || 'text-texto-principal'}`}>
            {combinada.resultado}
          </p>
          <p className="text-sm text-texto-secundario">Ganancia: ${combinada.ganancia?.toFixed(2)}</p>
          <IndicadorCorrelacion
            factor={combinada.factor_correlacion ?? 1}
            tieneCorrelacion={Boolean(combinada.tiene_mismo_partido)}
          />
        </div>
      </div>

      <div className="flex items-center justify-between">
        <p className="text-xs text-texto-terciario">
          Progreso: {resueltas}/{total} resueltas
        </p>
        <div className="flex items-center gap-2">
          <Boton variante="fantasma" tamano="sm" onClick={() => setExpandida((prev) => !prev)}>
            {expandida ? (
              <>
                <ChevronUp className="w-4 h-4 mr-1" />
                Ocultar
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4 mr-1" />
                Ver legs
              </>
            )}
          </Boton>
          <Boton variante="fantasma" tamano="sm" onClick={onEliminar}>
            <Trash2 className="w-4 h-4 mr-1" />
            Eliminar
          </Boton>
        </div>
      </div>

      {expandida && combinada.selecciones && (
        <div className="border border-neon-cyan/20 rounded-lg p-3 bg-futurista-medio/40">
          <ListaSelecciones selecciones={combinada.selecciones} />
        </div>
      )}

      {combinada.advertencias?.length ? (
        <div className="text-xs text-advertencia-500 space-y-1">
          {combinada.advertencias.map((advertencia) => (
            <p key={advertencia}>{advertencia}</p>
          ))}
        </div>
      ) : null}
    </div>
  );
}
