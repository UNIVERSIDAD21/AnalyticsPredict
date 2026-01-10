/**
 * AlertasCalibracion.tsx — Tarjetas de alertas con acciones
 */

import { useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, RefreshCcw } from 'lucide-react';
import { Boton } from '../atomos';
import { recalibrarMercado, resolverAlertaCalibracion } from '../../servicios/metricas';
import type { AlertaCalibracion, RespuestaRecalibracion } from '../../tipos';

interface PropsAlertasCalibracion {
  alertas: AlertaCalibracion[];
  onAccionCompletada?: () => void;
}

type EstadoAccion = 'idle' | 'cargando' | 'exito' | 'error';

interface EstadoAlerta {
  estado: EstadoAccion;
  mensaje: string | null;
  recalibracion?: RespuestaRecalibracion | null;
}

const estilosSeveridad: Record<AlertaCalibracion['severidad'], string> = {
  INFO: 'border-neon-cyan/40 text-neon-cyan',
  WARNING: 'border-advertencia-500/40 text-advertencia-500',
  CRITICAL: 'border-neon-rojo/50 text-neon-rojo',
};

const badgesSeveridad: Record<AlertaCalibracion['severidad'], string> = {
  INFO: 'Info',
  WARNING: 'Warning',
  CRITICAL: 'Critical',
};

function formatearFechaCorta(fechaISO?: string | null) {
  if (!fechaISO) return '—';
  const fecha = new Date(fechaISO);
  return fecha.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
}

function formatearTiempoRelativo(fechaISO?: string | null) {
  if (!fechaISO) return '—';
  const fecha = new Date(fechaISO);
  const diffMs = Date.now() - fecha.getTime();
  const dias = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  if (dias <= 0) return 'Hoy';
  if (dias === 1) return 'Hace 1 día';
  return `Hace ${dias} días`;
}

function formatearNumero(valor: number | null, decimales = 3) {
  if (valor === null || !isFinite(valor)) return '—';
  return valor.toFixed(decimales);
}

export function AlertasCalibracion({ alertas, onAccionCompletada }: PropsAlertasCalibracion) {
  const [estadoPorAlerta, setEstadoPorAlerta] = useState<Record<string, EstadoAlerta>>({});

  const alertasOrdenadas = useMemo(
    () => {
      const orden = { CRITICAL: 0, WARNING: 1, INFO: 2 };
      return [...alertas].sort((a, b) => orden[a.severidad] - orden[b.severidad]);
    },
    [alertas]
  );

  const actualizarEstado = (alertaId: string, estado: EstadoAlerta) => {
    setEstadoPorAlerta((prev) => ({ ...prev, [alertaId]: estado }));
  };

  const manejarRecalibrar = async (alerta: AlertaCalibracion) => {
    actualizarEstado(alerta.id, { estado: 'cargando', mensaje: null });
    const cutoff = alerta.periodo_fin ?? new Date().toISOString().slice(0, 10);

    try {
      const respuesta = await recalibrarMercado(alerta.mercado, alerta.origen, cutoff);
      actualizarEstado(alerta.id, {
        estado: 'exito',
        mensaje: respuesta.mensaje,
        recalibracion: respuesta,
      });
      onAccionCompletada?.();
    } catch (error) {
      actualizarEstado(alerta.id, {
        estado: 'error',
        mensaje: error instanceof Error ? error.message : 'No se pudo recalibrar.',
      });
    }
  };

  const manejarIgnorar = async (alerta: AlertaCalibracion) => {
    actualizarEstado(alerta.id, { estado: 'cargando', mensaje: null });
    try {
      const respuesta = await resolverAlertaCalibracion(alerta.id);
      actualizarEstado(alerta.id, {
        estado: 'exito',
        mensaje: respuesta.mensaje,
      });
      onAccionCompletada?.();
    } catch (error) {
      actualizarEstado(alerta.id, {
        estado: 'error',
        mensaje: error instanceof Error ? error.message : 'No se pudo resolver la alerta.',
      });
    }
  };

  if (!alertasOrdenadas.length) {
    return (
      <div className="text-sm text-texto-secundario">
        No hay alertas activas en este periodo.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alertasOrdenadas.map((alerta) => {
        const estado = estadoPorAlerta[alerta.id];
        return (
          <div
            key={alerta.id}
            className={`rounded-xl border p-4 space-y-3 bg-futurista-oscuro/70 ${estilosSeveridad[alerta.severidad]}`}
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-widest">
                  {badgesSeveridad[alerta.severidad]}
                </p>
                <h4 className="text-sm font-semibold text-texto-principal">
                  {alerta.tipo_alerta} · {alerta.mercado}
                </h4>
                <p className="text-xs text-texto-secundario">
                  {alerta.metrica_afectada} · Detectado {formatearTiempoRelativo(alerta.timestamp_deteccion)} (
                  {formatearFechaCorta(alerta.timestamp_deteccion)})
                </p>
              </div>
              <div className="text-xs text-texto-secundario">
                <div>Actual: {formatearNumero(alerta.valor_actual)}</div>
                <div>Umbral: {formatearNumero(alerta.valor_umbral)}</div>
                <div>Baseline: {formatearNumero(alerta.valor_baseline)}</div>
              </div>
            </div>

            {alerta.mensaje && <p className="text-sm text-texto-secundario">{alerta.mensaje}</p>}

            <div className="flex flex-wrap items-center gap-2">
              <Boton
                variante="secundario"
                tamano="sm"
                iconoInicio={<RefreshCcw size={14} />}
                cargando={estado?.estado === 'cargando'}
                onClick={() => manejarRecalibrar(alerta)}
              >
                Recalibrar
              </Boton>
              <Boton
                variante="fantasma"
                tamano="sm"
                iconoInicio={<AlertTriangle size={14} />}
                cargando={estado?.estado === 'cargando'}
                onClick={() => manejarIgnorar(alerta)}
              >
                Ignorar
              </Boton>
            </div>

            {estado?.mensaje && (
              <div className="flex items-center gap-2 text-xs text-texto-secundario">
                {estado.estado === 'exito' ? (
                  <CheckCircle2 className="w-4 h-4 text-neon-verde" />
                ) : (
                  <AlertTriangle className="w-4 h-4 text-neon-rojo" />
                )}
                <span>{estado.mensaje}</span>
              </div>
            )}

            {estado?.recalibracion && (
              <div className="text-xs text-texto-terciario">
                {estado.recalibracion.creado
                  ? 'Calibrador creado y activado.'
                  : 'Calibrador existente reactivado.'}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
