// hace parte del diseño de analisis
/**
 * FormularioGuardarApuesta.tsx — Modal para guardar una apuesta
 *
 * MEJORAS IMPLEMENTADAS:
 * - Extrae TODOS los campos de P1 (devig, score, sizing) del análisis
 * - UI simplificada: muestra resumen readonly y solo pide STAKE
 * - Incluye partido_id para resolución automática
 */

import { useEffect, useMemo, useState } from 'react';
import { Boton, Input } from '../atomos';
import { LadoApuesta, Mercado, PeticionCrearApuesta, ResultadoAnalisis } from '../../tipos';

interface PropsFormularioGuardarApuesta {
  abierto: boolean;
  resultado: ResultadoAnalisis;
  ladoSeleccionado: LadoApuesta;
  lineaSeleccionada: number;
  fechaPartido?: string;
  partidoId?: string;
  /** Cuota ingresada en el formulario de análisis - tiene prioridad sobre las demás */
  cuotaIngresada?: number;
  onCerrar: () => void;
  onGuardar: (apuesta: PeticionCrearApuesta) => void;
}

export function FormularioGuardarApuesta({
  abierto,
  resultado,
  ladoSeleccionado,
  lineaSeleccionada,
  fechaPartido,
  partidoId,
  cuotaIngresada,
  onCerrar,
  onGuardar,
}: PropsFormularioGuardarApuesta) {
  const [stake, setStake] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [mostrarOpcionales, setMostrarOpcionales] = useState(false);

  const mercado = (resultado.metadata?.mercado || 'COMPLETO') as Mercado;

  // Extraer cuota del análisis - priorizar cuotaIngresada del formulario
  const cuotaAutoLlenada = useMemo(() => {
    // 1. PRIORIDAD: Cuota ingresada directamente en el formulario de análisis
    if (cuotaIngresada && cuotaIngresada >= 1.01) {
      return cuotaIngresada;
    }

    const analisisMercado = resultado.analisis_mercado;
    const detalle = resultado.mejor_apuesta_detalle;

    // 2. Intentar desde mejor_apuesta_detalle
    if (detalle?.cuota) {
      return detalle.cuota;
    }

    // 3. Fallback a analisis_mercado según el lado
    if (analisisMercado) {
      if (ladoSeleccionado === 'OVER' && analisisMercado.cuota_over) {
        return analisisMercado.cuota_over;
      }
      if (ladoSeleccionado === 'UNDER' && analisisMercado.cuota_under) {
        return analisisMercado.cuota_under;
      }
    }

    return null;
  }, [cuotaIngresada, resultado, ladoSeleccionado]);

  // Obtener la fecha actual en formato YYYY-MM-DD (Eastern Time para NBA)
  const obtenerFechaHoyNBA = (): string => {
    const ahora = new Date();
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: 'America/New_York',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
    return formatter.format(ahora); // Formato YYYY-MM-DD
  };

  // Extraer fecha del partido - SIEMPRE debe tener una fecha válida
  const fechaAutoLlenada = useMemo(() => {
    // 1. Prioridad: fecha pasada como prop
    if (fechaPartido) {
      return fechaPartido;
    }
    // 2. Intentar desde metadata del resultado
    const metadataFecha = resultado.metadata?.fecha_partido;
    if (typeof metadataFecha === 'string' && metadataFecha) {
      return metadataFecha;
    }
    // 3. Fallback: usar la fecha actual (Eastern Time para NBA)
    return obtenerFechaHoyNBA();
  }, [fechaPartido, resultado]);

  // Estados para overrides opcionales
  const [cuotaManual, setCuotaManual] = useState('');
  const [fechaManual, setFechaManual] = useState('');

  useEffect(() => {
    if (abierto) {
      setStake('');
      setCuotaManual(cuotaAutoLlenada ? cuotaAutoLlenada.toFixed(2) : '');
      setFechaManual(fechaAutoLlenada);
      setError(null);
      setMostrarOpcionales(false);
    }
  }, [abierto, cuotaAutoLlenada, fechaAutoLlenada]);

  // Extraer snapshot completo del análisis incluyendo campos P1
  const snapshot = useMemo(() => {
    const probabilidadSistema = ladoSeleccionado === 'OVER'
      ? resultado.probabilidad_over ?? 0
      : resultado.probabilidad_under ?? 0;

    const prediccion = mercado === 'COMPLETO'
      ? resultado.prediccion_juego_completo
      : resultado.predicciones[mercado];

    const detalle = resultado.mejor_apuesta_detalle;

    return {
      // Probabilidades básicas
      probabilidad: probabilidadSistema,
      media: prediccion?.media_total ?? null,
      desviacion: prediccion?.desviacion_total ?? null,
      valorEsperado: resultado.analisis_mercado?.valor_esperado ?? detalle?.valor_esperado ?? null,

      // Cuotas
      cuota_over: detalle?.cuota_over ?? resultado.analisis_mercado?.cuota_over ?? null,
      cuota_under: detalle?.cuota_under ?? resultado.analisis_mercado?.cuota_under ?? null,

      // Campos de De-Vig (P1)
      devig_metodo: detalle?.devig_metodo ?? null,
      devig_overround: detalle?.devig_overround ?? null,
      devig_p_mkt_raw: detalle?.devig_p_mkt_raw ?? null,
      devig_p_mkt_fair: detalle?.devig_p_mkt_fair ?? null,
      devig_advertencias: detalle?.devig_advertencias ?? null,
      edge_real: detalle?.edge_real ?? null,

      // Campos de Score (P1)
      score_total: detalle?.score_total ?? null,
      score_componentes: detalle?.score_componentes ?? null,
      score_explicacion: detalle?.score_explicacion ?? null,
      score_penalizaciones: detalle?.score_penalizaciones ?? null,

      // Campos de Sizing/Kelly (P1)
      kelly_full: detalle?.kelly_full ?? null,
      kelly_fraccional: detalle?.kelly_fraccional ?? null,
      fraccion_kelly: detalle?.fraccion_kelly ?? null,
      stake_porcentaje: detalle?.stake_porcentaje ?? null,
      bankroll_momento: detalle?.bankroll_momento ?? null,
      perfil_riesgo_usado: detalle?.perfil_riesgo_usado ?? null,
      sizing_advertencias: detalle?.sizing_advertencias ?? null,
      sizing_penalizaciones: detalle?.sizing_penalizaciones ?? null,
    };
  }, [ladoSeleccionado, mercado, resultado]);

  // Obtener partido_id desde props o metadata
  const partidoIdFinal = useMemo(() => {
    if (partidoId) return partidoId;
    const metadataPartidoId = resultado.metadata?.partido_id;
    if (typeof metadataPartidoId === 'string') return metadataPartidoId;
    return null;
  }, [partidoId, resultado.metadata]);

  if (!abierto) return null;

  const manejarGuardar = () => {
    const stakeNumero = Number(stake);
    const cuotaFinal = cuotaManual ? Number(cuotaManual) : cuotaAutoLlenada;
    const fechaFinal = fechaManual || fechaAutoLlenada;

    if (!stake || stakeNumero <= 0) {
      setError('Ingresa un stake válido.');
      return;
    }
    if (!cuotaFinal || cuotaFinal < 1.01) {
      setError('Cuota inválida. Ingresa una cuota >= 1.01');
      return;
    }

    setError(null);

    // Construir payload con TODOS los campos de P1
    const payload: PeticionCrearApuesta = {
      // Datos básicos
      partido_id: partidoIdFinal,
      equipo_local: resultado.equipo_nombre_completo,
      equipo_visitante: resultado.rival_nombre_completo,
      fecha_partido: fechaFinal || undefined,
      mercado,
      lado: ladoSeleccionado,
      linea: lineaSeleccionada,
      cuota: cuotaFinal,
      cuota_over: snapshot.cuota_over ?? undefined,
      cuota_under: snapshot.cuota_under ?? undefined,
      stake: stakeNumero,
      probabilidad_sistema: snapshot.probabilidad,
      confianza_sistema: resultado.nivel_confianza,
      valor_esperado: snapshot.valorEsperado ?? undefined,
      prediccion_media: snapshot.media ?? undefined,
      prediccion_desviacion: snapshot.desviacion ?? undefined,
      razones: resultado.razones as unknown as Array<Record<string, unknown>>,

      // Campos de De-Vig (P1)
      devig_metodo: snapshot.devig_metodo ?? undefined,
      devig_overround: snapshot.devig_overround ?? undefined,
      devig_p_mkt_raw: snapshot.devig_p_mkt_raw ?? undefined,
      devig_p_mkt_fair: snapshot.devig_p_mkt_fair ?? undefined,
      devig_advertencias: snapshot.devig_advertencias ?? undefined,
      edge_real: snapshot.edge_real ?? undefined,

      // Campos de Score (P1)
      score_total: snapshot.score_total ?? undefined,
      score_componentes: snapshot.score_componentes as Record<string, number> | undefined,
      score_explicacion: snapshot.score_explicacion ?? undefined,
      score_penalizaciones: snapshot.score_penalizaciones ?? undefined,

      // Campos de Sizing/Kelly (P1)
      kelly_full: snapshot.kelly_full ?? undefined,
      kelly_fraccional: snapshot.kelly_fraccional ?? undefined,
      fraccion_kelly: snapshot.fraccion_kelly ?? undefined,
      stake_porcentaje: snapshot.stake_porcentaje ?? undefined,
      bankroll_momento: snapshot.bankroll_momento ?? undefined,
      perfil_riesgo_usado: snapshot.perfil_riesgo_usado ?? undefined,
      sizing_advertencias: snapshot.sizing_advertencias ?? undefined,
      sizing_penalizaciones: snapshot.sizing_penalizaciones as Record<string, number> | undefined,
    };

    onGuardar(payload);
  };

  // Formatear probabilidad para mostrar
  const formatearProbabilidad = (p: number) => `${(p * 100).toFixed(1)}%`;
  const formatearEdge = (e: number | null) => e != null ? `${(e * 100).toFixed(2)}%` : 'N/A';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="w-full max-w-lg rounded-xl border border-neon-cyan/30 bg-futurista-oscuro p-6 max-h-[90vh] overflow-y-auto">
        <h3 className="text-lg font-futurista text-texto-principal mb-4">
          Guardar en Bitacora
        </h3>

        {/* Resumen de la apuesta (readonly) */}
        <div className="mb-4 p-4 rounded-lg bg-futurista-medio/50 border border-neon-cyan/20">
          <h4 className="text-sm font-semibold text-neon-cyan mb-3">Resumen de la apuesta</h4>

          <div className="space-y-2 text-sm text-texto-secundario">
            <div className="flex justify-between">
              <span>Partido:</span>
              <span className="text-texto-principal font-medium">
                {resultado.equipo_nombre_completo} vs {resultado.rival_nombre_completo}
              </span>
            </div>

            <div className="flex justify-between">
              <span>Mercado:</span>
              <span className="text-texto-principal">
                {mercado} {ladoSeleccionado} {lineaSeleccionada}
              </span>
            </div>

            <div className="flex justify-between">
              <span>Cuota:</span>
              <span className="text-texto-principal">
                @ {cuotaAutoLlenada?.toFixed(2) || 'N/A'}
              </span>
            </div>

            <div className="flex justify-between">
              <span>Probabilidad:</span>
              <span className="text-texto-principal">
                {formatearProbabilidad(snapshot.probabilidad)}
              </span>
            </div>

            <div className="flex justify-between">
              <span>Confianza:</span>
              <span className={`font-medium ${
                resultado.nivel_confianza === 'ALTA' ? 'text-neon-verde' :
                resultado.nivel_confianza === 'MEDIA' ? 'text-neon-amarillo' :
                'text-neon-rojo'
              }`}>
                {resultado.nivel_confianza}
              </span>
            </div>

            {snapshot.edge_real != null && (
              <div className="flex justify-between">
                <span>Edge Real:</span>
                <span className={`font-medium ${snapshot.edge_real > 0 ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                  {formatearEdge(snapshot.edge_real)}
                </span>
              </div>
            )}

            {snapshot.score_total != null && (
              <div className="flex justify-between">
                <span>Score:</span>
                <span className="text-texto-principal">{snapshot.score_total.toFixed(1)}</span>
              </div>
            )}

            {snapshot.kelly_fraccional != null && (
              <div className="flex justify-between">
                <span>Kelly sugerido:</span>
                <span className="text-neon-cyan">
                  {(snapshot.kelly_fraccional * 100).toFixed(2)}% del bankroll
                </span>
              </div>
            )}

            {fechaAutoLlenada && (
              <div className="flex justify-between">
                <span>Fecha:</span>
                <span className="text-texto-principal">{fechaAutoLlenada}</span>
              </div>
            )}

            {!partidoIdFinal && (
              <div className="mt-2 p-2 rounded bg-neon-amarillo/10 border border-neon-amarillo/30">
                <span className="text-xs text-neon-amarillo">
                  Sin partido_id: la resolucion automatica no funcionara
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Campo principal: STAKE */}
        <div className="space-y-4">
          <div className="p-4 rounded-lg border-2 border-neon-cyan/50 bg-neon-cyan/5">
            <Input
              etiqueta="Cuanto vas a apostar? (obligatorio)"
              type="number"
              min="0"
              step="0.01"
              value={stake}
              onChange={(event) => setStake(event.target.value)}
              placeholder={snapshot.bankroll_momento
                ? `Sugerido: $${((snapshot.kelly_fraccional ?? 0) * snapshot.bankroll_momento).toFixed(2)}`
                : 'Monto a apostar'}
              autoFocus
            />
            {snapshot.stake_porcentaje != null && snapshot.bankroll_momento != null && (
              <p className="mt-2 text-xs text-texto-secundario">
                Kelly sugiere {(snapshot.stake_porcentaje * 100).toFixed(2)}% =
                ${((snapshot.stake_porcentaje) * snapshot.bankroll_momento).toFixed(2)}
              </p>
            )}
          </div>

          {/* Opciones avanzadas (colapsables) */}
          <button
            type="button"
            onClick={() => setMostrarOpcionales(!mostrarOpcionales)}
            className="text-sm text-neon-cyan hover:text-neon-cyan/80 flex items-center gap-1"
          >
            <span>{mostrarOpcionales ? '▼' : '▶'}</span>
            {mostrarOpcionales ? 'Ocultar opciones' : 'Modificar cuota/fecha'}
          </button>

          {mostrarOpcionales && (
            <div className="space-y-3 pl-4 border-l-2 border-neon-cyan/20">
              <div className="relative">
                <Input
                  etiqueta="Cuota (override)"
                  type="number"
                  min="1.01"
                  step="0.01"
                  value={cuotaManual}
                  onChange={(event) => setCuotaManual(event.target.value)}
                  placeholder={cuotaAutoLlenada?.toFixed(2) || 'Ingresa cuota'}
                />
              </div>
              <div className="relative">
                <Input
                  etiqueta="Fecha del partido (override)"
                  type="date"
                  value={fechaManual}
                  onChange={(event) => setFechaManual(event.target.value)}
                />
              </div>
            </div>
          )}

          {error && <p className="text-neon-rojo text-sm">{error}</p>}
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Boton variante="fantasma" onClick={onCerrar}>
            Cancelar
          </Boton>
          <Boton variante="primario" onClick={manejarGuardar}>
            Guardar apuesta
          </Boton>
        </div>
      </div>
    </div>
  );
}
