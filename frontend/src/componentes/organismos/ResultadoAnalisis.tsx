// hace parte del diseño de analisis
/**
 * ResultadoAnalisis.tsx — Contenedor principal de resultados con estilo futurista
 *
 * Fase 2: Integra componentes profesionales de de-vig, score, sizing y calibración.
 * Muestra advertencias del backend y toda la información necesaria para decisiones informadas.
 */

import { Clock, MapPin, Activity, CheckCircle, AlertTriangle, BookOpen } from 'lucide-react';
import {
  ResultadoAnalisis as TipoResultado,
  NivelConfianza,
  LadoApuesta,
  MejorApuestaDetalle,
} from '../../tipos';
import { TarjetaProbabilidad } from './TarjetaProbabilidad';
import { ListaRazones } from './ListaRazones';
import { AnalisisMercadoCard } from './AnalisisMercadoCard';
import { Boton } from '../atomos';
import {
  PanelAdvertencias,
  TarjetaDeVig,
  TarjetaScore,
  TarjetaSizing,
  SeccionCalibracion,
  TarjetaNoApta,
  PanelComparacionPrediccion,
  SeccionAjustesAplicados,
} from '../moleculas';
import { SeccionH2H, SeccionFormaReciente, SeccionHistorialDetallado } from './index';
import type { Mercado } from '../../tipos/analisis';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsResultadoAnalisis {
  /** Datos del resultado */
  resultado: TipoResultado;

  /** Advertencias del backend (Fase 2) */
  advertencias?: string[];

  /** Selección del usuario (Over/Under) */
  seleccionUsuario?: {
    lado: LadoApuesta;
    linea: number;
  } | null;

  /** ID del equipo local (para navegación a estadísticas) */
  equipoLocalId?: string;

  /** ID del equipo visitante (para navegación a estadísticas) */
  equipoVisitanteId?: string;

  /** Acción para guardar en bitácora */
  onGuardar?: () => void;

  /** Acción para configurar bankroll (Fase 4 placeholder) */
  onConfigurarBankroll?: () => void;

  /** Callback cuando el usuario quiere ver estadísticas de un equipo */
  onNavegarlEquipo?: (equipoId: string) => void;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

function obtenerConfigConfianza(nivel: NivelConfianza) {
  switch (nivel) {
    case 'ALTA':
      return { texto: 'Alta', color: 'bg-neon-verde', textColor: 'text-neon-verde' };
    case 'MEDIA':
      return { texto: 'Media', color: 'bg-advertencia-500', textColor: 'text-advertencia-500' };
    case 'BAJA':
      return { texto: 'Baja', color: 'bg-neon-rojo', textColor: 'text-neon-rojo' };
    default:
      return { texto: 'Media', color: 'bg-advertencia-500', textColor: 'text-advertencia-500' };
  }
}

function formatearFecha(fechaISO: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleString('es-ES', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Extrae mejor_apuesta_detalle del resultado.
 * El backend puede enviar los datos en diferentes lugares según la versión.
 */
function extraerMejorApuestaDetalle(resultado: TipoResultado): MejorApuestaDetalle | null {
  // Primero intentar desde el campo dedicado
  if (resultado.mejor_apuesta_detalle) {
    return resultado.mejor_apuesta_detalle;
  }

  // Si no existe, intentar construirlo desde mejor_apuesta si tiene los campos avanzados
  const ma = resultado.mejor_apuesta as MejorApuestaDetalle | null;
  if (ma && 'devig_metodo' in ma && 'score_total' in ma) {
    return ma;
  }

  return null;
}

function esEstadoNoApto(resultado: TipoResultado, detalle: MejorApuestaDetalle | null): boolean {
  const mensaje = resultado.mensaje_apuesta?.toUpperCase();
  const mensajeNoApto = Boolean(mensaje?.includes('NO_APTO') || mensaje?.includes('NO APTO'));
  const scoreNoApto = detalle?.score_total === -1000;
  const sinRecomendacion = !resultado.mejor_apuesta && !detalle;

  return mensajeNoApto || scoreNoApto || (sinRecomendacion && Boolean(resultado.mensaje_apuesta));
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra todos los resultados del análisis con estilo futurista.
 * Fase 2: Incluye de-vig, score, sizing, calibración y advertencias.
 */
export function ResultadoAnalisis({
  resultado,
  advertencias = [],
  seleccionUsuario,
  equipoLocalId,
  equipoVisitanteId,
  onGuardar,
  onConfigurarBankroll,
  onNavegarlEquipo,
}: PropsResultadoAnalisis) {
  const mercado = resultado.metadata?.mercado as string;
  const configConfianza = obtenerConfigConfianza(resultado.nivel_confianza);

  // Obtener datos de probabilidad según el mercado
  const probabilidadOver = resultado.probabilidad_over ?? 0;
  const probabilidadUnder = resultado.probabilidad_under ?? 0;
  const linea = resultado.linea_analizada ?? 0;

  // Obtener media y desviación
  let mediaTotal = 0;
  let desviacion = 0;
  const prediccionGanador = mercado === 'COMPLETO'
    ? resultado.prediccion_juego_completo
    : (mercado ? resultado.predicciones[mercado] : null);
  const etiquetaGanador = mercado === 'COMPLETO' ? 'Ganador del partido' : 'Ganador del cuarto';
  const nombreGanador = prediccionGanador?.ganador_probable === 'equipo'
    ? resultado.equipo_nombre_completo
    : resultado.rival_nombre_completo;

  if (mercado === 'COMPLETO' && resultado.prediccion_juego_completo) {
    mediaTotal = resultado.prediccion_juego_completo.media_total;
    desviacion = resultado.prediccion_juego_completo.desviacion_total;
  } else if (mercado && resultado.predicciones[mercado]) {
    mediaTotal = resultado.predicciones[mercado].media_total;
    desviacion = resultado.predicciones[mercado].desviacion_total;
  }

  // Determinar si la predicción del usuario coincide con el sistema
  const sistemaRecomienda: LadoApuesta = probabilidadOver > probabilidadUnder ? 'OVER' : 'UNDER';
  const coincideConSistema = seleccionUsuario?.lado === sistemaRecomienda;
  const puedeGuardar = Boolean(seleccionUsuario && linea > 0 && onGuardar);

  // Fase 2: Extraer datos avanzados
  const detalle = extraerMejorApuestaDetalle(resultado);
  const tieneDetalleAvanzado = detalle !== null;
  const noApto = esEstadoNoApto(resultado, detalle);

  return (
    <div className="space-y-6 animate-entrada">
      {/* ═══════════════════════════════════════════════════════════
          1. ADVERTENCIAS DEL BACKEND (si hay)
          ═══════════════════════════════════════════════════════════ */}
      {advertencias.length > 0 && (
        <PanelAdvertencias advertencias={advertencias} />
      )}

      {/* ═══════════════════════════════════════════════════════════
          2. ENCABEZADO DEL PARTIDO
          ═══════════════════════════════════════════════════════════ */}
      <div className="tarjeta relative overflow-hidden">
        {/* Línea decorativa superior */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-neon-cyan via-neon-magenta to-neon-cyan" />

        {/* Equipos */}
        <div className="text-center mb-6 pt-2">
          <div className="flex items-center justify-center gap-3 md:gap-6 flex-wrap">
            <span className="text-xl md:text-2xl font-futurista font-bold text-texto-principal tracking-wider">
              {resultado.equipo_nombre_completo}
            </span>
            <span className="text-neon-cyan font-futurista text-lg">VS</span>
            <span className="text-xl md:text-2xl font-futurista font-bold text-texto-principal tracking-wider">
              {resultado.rival_nombre_completo}
            </span>
          </div>
          <div className="mt-2 inline-block px-4 py-1 rounded-full bg-neon-cyan/10 border border-neon-cyan/30">
            <span className="text-sm text-neon-cyan font-mono">
              {mercado === 'COMPLETO' ? 'JUEGO COMPLETO' : `CUARTO ${mercado}`}
            </span>
          </div>
        </div>

        {/* Metadatos */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-texto-secundario">
          <div className="flex items-center gap-2">
            <MapPin size={14} className="text-neon-cyan" />
            <span>{resultado.equipo_nombre_completo} (Local)</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock size={14} className="text-neon-magenta" />
            <span className="font-mono">{formatearFecha(resultado.fecha_analisis)}</span>
          </div>
          <div className="flex items-center gap-2">
            <Activity size={14} className={configConfianza.textColor} />
            <span>Confianza:</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${configConfianza.color} text-futurista-negro`}>
              {configConfianza.texto}
            </span>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          3. ADVERTENCIA NO APTO (si aplica)
          Se muestra como aviso pero el análisis continúa visible
          ═══════════════════════════════════════════════════════════ */}
      {noApto && (
        <TarjetaNoApta mensaje={resultado.mensaje_apuesta} candidatos={resultado.candidatos} />
      )}

      {/* ═══════════════════════════════════════════════════════════
          4. INDICADOR DE APUESTA DEL USUARIO
          ═══════════════════════════════════════════════════════════ */}
      {seleccionUsuario && linea > 0 && (
        <div className={`tarjeta p-4 ${coincideConSistema ? 'border-neon-verde/30' : 'border-advertencia-500/30'}`}>
          <div className="flex items-center gap-3">
            {coincideConSistema ? (
              <CheckCircle className="w-6 h-6 text-neon-verde flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-6 h-6 text-advertencia-500 flex-shrink-0" />
            )}
            <div>
              <p className="text-sm text-texto-secundario">
                Tu apuesta: <span className={`font-semibold ${seleccionUsuario.lado === 'OVER' ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                  {seleccionUsuario.lado === 'OVER' ? 'Over' : 'Under'} {seleccionUsuario.linea}
                </span>
              </p>
              <p className={`text-xs ${coincideConSistema ? 'text-neon-verde' : 'text-advertencia-500'}`}>
                {coincideConSistema
                  ? 'Tu predicción coincide con la recomendación del sistema'
                  : `El sistema recomienda ${sistemaRecomienda === 'OVER' ? 'Over' : 'Under'} - considera revisar`
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {prediccionGanador && (
        <div className="tarjeta p-4 border border-neon-cyan/20">
          <p className="text-xs uppercase tracking-wider text-neon-cyan font-semibold">{etiquetaGanador}</p>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-lg font-futurista text-texto-principal">{nombreGanador}</p>
              <p className="text-sm text-texto-secundario">
                Probabilidad: <span className="text-neon-verde font-semibold">{(prediccionGanador.probabilidad_ganador * 100).toFixed(1)}%</span>
              </p>
            </div>
            <div className="text-right text-xs text-texto-secundario">
              <p>Marcador estimado: {prediccionGanador.media_equipo.toFixed(1)} - {prediccionGanador.media_rival.toFixed(1)}</p>
              <p>Total estimado: {prediccionGanador.media_total.toFixed(1)}</p>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          5. PROBABILIDADES
          ═══════════════════════════════════════════════════════════ */}
      {linea > 0 && (
        <TarjetaProbabilidad
          linea={linea}
          probabilidadOver={probabilidadOver}
          probabilidadUnder={probabilidadUnder}
          mediaTotal={mediaTotal}
          desviacion={desviacion}
          seleccionUsuario={seleccionUsuario?.lado}
        />
      )}

      {/* ═══════════════════════════════════════════════════════════
          6. SECCIÓN: AJUSTES CONTEXTUALES (Fase 3)
          ═══════════════════════════════════════════════════════════ */}

      {/* Panel de Comparación Base vs Ajustada */}
      {resultado.prediccion_ajustada && resultado.prediccion_base && (
        <PanelComparacionPrediccion
          prediccionBase={{
            media: resultado.prediccion_base.media,
            probabilidadOver: resultado.prediccion_base.probabilidad_over ?? 0,
            probabilidadUnder: resultado.prediccion_base.probabilidad_under ?? 0,
          }}
          prediccionAjustada={{
            media: resultado.prediccion_ajustada.media_ajustada,
            probabilidadOver: resultado.prediccion_ajustada.probabilidad_over_ajustada,
            probabilidadUnder: resultado.prediccion_ajustada.probabilidad_under_ajustada,
          }}
          linea={linea}
          confianzaBase={resultado.prediccion_ajustada.confianza_base}
          confianzaAjustada={resultado.prediccion_ajustada.confianza_ajustada}
        />
      )}

      {/* Lista de Ajustes Aplicados */}
      {resultado.ajustes && resultado.ajustes.ajustes && resultado.ajustes.ajustes.length > 0 && (
        <SeccionAjustesAplicados
          ajustes={resultado.ajustes.ajustes}
          ajusteTotal={resultado.ajustes.ajuste_total_capped}
          fueCapped={resultado.ajustes.fue_capped}
          inicialmenteExpandido={true}
        />
      )}

      {/* ═══════════════════════════════════════════════════════════
          7. BLOQUE DE-VIG + CALIBRACIÓN (Fase 2)
          Solo mostrar si hay detalle avanzado
          ═══════════════════════════════════════════════════════════ */}
      {tieneDetalleAvanzado && detalle && (
        <div className="space-y-4">
          <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-cyan flex items-center gap-2">
            <span className="w-8 h-[2px] bg-gradient-to-r from-neon-cyan to-transparent" />
            Análisis de Valor
          </h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* TarjetaDeVig */}
            <TarjetaDeVig
              metodo={detalle.devig_metodo}
              overround={detalle.devig_overround}
              pMktRaw={detalle.devig_p_mkt_raw}
              pMktFair={detalle.devig_p_mkt_fair}
              edgeRaw={detalle.edge_raw}
              edgeReal={detalle.edge_real}
              advertencias={detalle.devig_advertencias}
            />

            {/* SeccionCalibracion */}
            <div className="flex flex-col justify-center">
              <SeccionCalibracion
                pRaw={detalle.p_raw}
                pCalibrada={detalle.p_calibrada}
                calibradorUsado={detalle.calibrador_usado}
              />
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          8. BLOQUE SCORE + SIZING (Fase 2)
          Solo mostrar si hay detalle avanzado
          ═══════════════════════════════════════════════════════════ */}
      {tieneDetalleAvanzado && detalle && (
        <div className="space-y-4">
          <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-magenta flex items-center gap-2">
            <span className="w-8 h-[2px] bg-gradient-to-r from-neon-magenta to-transparent" />
            Decisión y Riesgo
          </h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* TarjetaScore */}
            <TarjetaScore
              scoreTotal={detalle.score_total}
              componentes={detalle.score_componentes}
              explicacion={detalle.score_explicacion}
              penalizaciones={detalle.score_penalizaciones}
              valorEsperado={detalle.valor_esperado}
            />

            {/* TarjetaSizing */}
            <TarjetaSizing
              kellyFull={detalle.kelly_full}
              kellyFraccional={detalle.kelly_fraccional}
              fraccionKelly={detalle.fraccion_kelly}
              stake={detalle.stake}
              stakePorcentaje={detalle.stake_porcentaje}
              bankroll={detalle.bankroll_momento}
              perfilRiesgo={detalle.perfil_riesgo_usado}
              advertencias={detalle.sizing_advertencias}
              penalizaciones={detalle.sizing_penalizaciones}
              aplicaronCaps={detalle.aplicaron_caps}
              onConfigurarBankroll={onConfigurarBankroll}
            />
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          9. ANÁLISIS DE MERCADO (legacy, si hay cuota pero no detalle avanzado)
          ═══════════════════════════════════════════════════════════ */}
      {!tieneDetalleAvanzado && resultado.analisis_mercado && (
        <AnalisisMercadoCard analisis={resultado.analisis_mercado} />
      )}

      {/* ═══════════════════════════════════════════════════════════
          10. SECCIÓN: CONTEXTO DEL PARTIDO (Fase 3)
          ═══════════════════════════════════════════════════════════ */}

      {/* Head-to-Head */}
      {resultado.contexto?.h2h && (
        <SeccionH2H
          h2h={resultado.contexto.h2h}
          equipoNombre={resultado.equipo_nombre_completo}
          rivalNombre={resultado.rival_nombre_completo}
          lineaActual={linea}
          inicialmenteExpandido={false}
        />
      )}

      {/* Forma Reciente */}
      {resultado.contexto && resultado.contexto.forma_equipo && resultado.contexto.forma_rival && (
        <SeccionFormaReciente
          formaEquipo={resultado.contexto.forma_equipo}
          formaRival={resultado.contexto.forma_rival}
          descansoEquipo={resultado.contexto.descanso_equipo}
          descansoRival={resultado.contexto.descanso_rival}
          equipoNombre={resultado.equipo_nombre_completo}
          rivalNombre={resultado.rival_nombre_completo}
          equipoId={resultado.ubicacion === 'LOCAL' ? equipoLocalId : equipoVisitanteId}
          rivalId={resultado.ubicacion === 'LOCAL' ? equipoVisitanteId : equipoLocalId}
          inicialmenteExpandido={true}
          onVerEstadisticas={onNavegarlEquipo}
        />
      )}

      {/* ═══════════════════════════════════════════════════════════
          11. HISTORIAL DETALLADO
          ═══════════════════════════════════════════════════════════ */}
      {equipoLocalId && equipoVisitanteId && linea > 0 && mercado && (
        <SeccionHistorialDetallado
          equipoLocalId={equipoLocalId}
          equipoLocalNombre={resultado.equipo_nombre_completo}
          equipoLocalAbr={resultado.equipo?.toUpperCase() || 'LOC'}
          equipoVisitanteId={equipoVisitanteId}
          equipoVisitanteNombre={resultado.rival_nombre_completo}
          equipoVisitanteAbr={resultado.rival?.toUpperCase() || 'VIS'}
          mercado={mercado as Mercado}
          linea={linea}
          inicialmenteExpandido={false}
        />
      )}

      {/* ═══════════════════════════════════════════════════════════
          12. RAZONES
          ═══════════════════════════════════════════════════════════ */}
      <ListaRazones razones={resultado.razones} />

      {/* ═══════════════════════════════════════════════════════════
          13. GUARDAR EN BITÁCORA
          Siempre disponible si hay selección válida (incluso en NO_APTO)
          ═══════════════════════════════════════════════════════════ */}
      {puedeGuardar && (
        <div className="tarjeta p-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm text-texto-secundario">Guarda esta apuesta en tu bitácora</p>
            <p className="text-xs text-texto-terciario">
              {noApto
                ? 'Se guardará el análisis aunque no haya candidatos aptos'
                : 'Se guardará el snapshot del análisis'}
            </p>
          </div>
          <Boton variante="primario" iconoInicio={<BookOpen size={16} />} onClick={onGuardar}>
            Guardar en Bitácora
          </Boton>
        </div>
      )}
    </div>
  );
}
