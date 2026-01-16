/**
 * TarjetaApuestaSimple.tsx — Tarjeta para apuestas simples en bitácora
 */

import { Trash2, CheckCircle } from 'lucide-react';
import { RegistroBitacoraUnificada } from '../../tipos';
import { Boton } from '../atomos';

interface PropsTarjetaApuestaSimple {
  apuesta: RegistroBitacoraUnificada;
  onResolver: () => void;
  onEliminar: () => void;
}

const estilosEstado: Record<string, string> = {
  GANADA: 'text-neon-verde',
  PERDIDA: 'text-neon-rojo',
  PUSH: 'text-advertencia-500',
  PENDIENTE: 'text-neon-cyan',
  ANULADA: 'text-texto-terciario',
};

export function TarjetaApuestaSimple({ apuesta, onResolver, onEliminar }: PropsTarjetaApuestaSimple) {
  return (
    <div className="tarjeta p-4 flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-widest text-texto-terciario">SIMPLE</p>
          <h4 className="text-lg font-semibold text-texto-principal">
            {apuesta.equipo_local} vs {apuesta.equipo_visitante}
          </h4>
          <p className="text-sm text-texto-secundario">
            {apuesta.mercado} · {apuesta.lado} {apuesta.linea} · @ {apuesta.cuota ?? '—'}
          </p>
        </div>
        <div className="text-right">
          <p className={`text-sm font-semibold ${estilosEstado[apuesta.resultado] || 'text-texto-principal'}`}>
            {apuesta.resultado}
          </p>
          <p className="text-sm text-texto-secundario">Stake: ${apuesta.stake}</p>
          <p className="text-sm text-texto-secundario">Ganancia: ${apuesta.ganancia?.toFixed(2)}</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Boton variante="secundario" tamano="sm" onClick={onResolver}>
          <CheckCircle className="w-4 h-4 mr-1" />
          Resolver
        </Boton>
        <Boton variante="fantasma" tamano="sm" onClick={onEliminar}>
          <Trash2 className="w-4 h-4 mr-1" />
          Eliminar
        </Boton>
      </div>
    </div>
  );
}
