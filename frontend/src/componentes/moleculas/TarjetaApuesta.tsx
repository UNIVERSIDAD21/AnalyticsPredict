/**
 * TarjetaApuesta.tsx — Tarjeta visual para una apuesta de bitácora
 */

import { useState } from 'react';
import { Calendar, Trophy, Target, Trash2, Percent } from 'lucide-react';
import { Apuesta } from '../../tipos';
import { Boton, Tarjeta } from '../atomos';

/**
 * Formatea una fecha ISO (YYYY-MM-DD) sin problemas de timezone.
 * Evita que new Date() interprete la fecha como UTC y muestre día anterior.
 */
function formatearFechaLocal(fechaISO: string): string {
  const [anio, mes, dia] = fechaISO.split('-').map(Number);
  const fecha = new Date(anio, mes - 1, dia);
  return fecha.toLocaleDateString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

interface PropsTarjetaApuesta {
  apuesta: Apuesta;
  onResolver: (apuesta: Apuesta) => void;
  onEliminar: (apuesta: Apuesta) => void;
}

const coloresResultado: Record<string, string> = {
  GANADA: 'text-neon-verde',
  PERDIDA: 'text-neon-rojo',
  PUSH: 'text-advertencia-500',
  ANULADA: 'text-nba-gris-400',
  PENDIENTE: 'text-neon-cyan',
};

export function TarjetaApuesta({ apuesta, onResolver, onEliminar }: PropsTarjetaApuesta) {
  const [confirmandoEliminar, setConfirmandoEliminar] = useState(false);

  const fecha = apuesta.fecha_partido
    ? formatearFechaLocal(apuesta.fecha_partido)
    : 'Sin fecha';
  const resultadoColor = coloresResultado[apuesta.resultado] || 'text-texto-secundario';
  const esPendiente = apuesta.resultado === 'PENDIENTE';

  // Formatear probabilidad del sistema como porcentaje
  const probSistema = apuesta.probabilidad_sistema != null
    ? `${(apuesta.probabilidad_sistema * 100).toFixed(1)}%`
    : null;

  const manejarEliminar = () => {
    if (!confirmandoEliminar) {
      setConfirmandoEliminar(true);
      return;
    }
    onEliminar(apuesta);
    setConfirmandoEliminar(false);
  };

  const cancelarEliminar = () => {
    setConfirmandoEliminar(false);
  };

  return (
    <Tarjeta className="space-y-4">
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <h3 className="text-lg font-futurista text-texto-principal">
            {apuesta.equipo_local} vs {apuesta.equipo_visitante}
          </h3>
          <span className={`text-xs font-semibold uppercase ${resultadoColor}`}>
            {apuesta.resultado}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-4 text-sm text-texto-secundario">
          <div className="flex items-center gap-2">
            <Target size={14} className="text-neon-cyan" />
            <span>
              {apuesta.lado} {apuesta.linea} · {apuesta.mercado}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Calendar size={14} className="text-neon-magenta" />
            <span>{fecha}</span>
          </div>
          {probSistema && (
            <div className="flex items-center gap-2">
              <Percent size={14} className="text-neon-amarillo" />
              <span>
                Prob: <span className="text-texto-principal font-semibold">{probSistema}</span>
              </span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Trophy size={14} className="text-neon-verde" />
            <span>
              Stake {apuesta.stake.toFixed(2)} · Cuota {apuesta.cuota.toFixed(2)}
            </span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-texto-secundario">
          <span className="text-texto-principal font-semibold">Ganancia:</span>{' '}
          <span className={apuesta.ganancia >= 0 ? 'text-neon-verde' : 'text-neon-rojo'}>
            {apuesta.ganancia.toFixed(2)}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {esPendiente && (
            <Boton
              variante="secundario"
              tamano="sm"
              onClick={() => onResolver(apuesta)}
            >
              Marcar resultado
            </Boton>
          )}
          {esPendiente && !confirmandoEliminar && (
            <Boton
              variante="peligro"
              tamano="sm"
              iconoInicio={<Trash2 size={14} />}
              onClick={manejarEliminar}
            >
              Eliminar
            </Boton>
          )}
          {esPendiente && confirmandoEliminar && (
            <>
              <Boton
                variante="fantasma"
                tamano="sm"
                onClick={cancelarEliminar}
              >
                Cancelar
              </Boton>
              <Boton
                variante="peligro"
                tamano="sm"
                iconoInicio={<Trash2 size={14} />}
                onClick={manejarEliminar}
              >
                Confirmar eliminar
              </Boton>
            </>
          )}
        </div>
      </div>
    </Tarjeta>
  );
}
