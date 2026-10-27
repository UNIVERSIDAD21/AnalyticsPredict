import type { AnalisisIntegral } from '../../tipos/analisisIntegral';
import { SeccionesAnalisisIntegral } from './SeccionesAnalisisIntegral';
// hace parte del diseño de analisis
/**
 * ResultadoAnalisis.tsx — Contenedor principal de resultados con estilo futurista
 *
 * Fase 2: Integra componentes profesionales de de-vig, score, sizing y calibración.
 * Muestra advertencias del backend y toda la información necesaria para decisiones informadas.
 */

import { Clock, MapPin, Activity, CheckCircle, AlertTriangle, BookOpen } from 'lucide-react';
import {
  NivelConfianza,
  LadoApuesta,
  MejorApuestaDetalle,
} from '../../tipos';
import type { ResultadoVista } from '../../tipos/resultadoVista';
import type { ResultadoEuro } from '../../servicios/euroliga';
import { formaEquipoEuroliga, h2hEuroliga } from '../../utilidades/resultadoEuroliga';
import { SeccionHistorialEuroliga } from './SeccionHistorialEuroliga';
import { PanelDiagnosticoEuroliga } from './PanelDiagnosticoEuroliga';
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
import type { TipoMercadoFutbol } from '../../tipos/futbol';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsResultadoAnalisis {
  /** Datos del resultado */
  resultado: ResultadoVista;
  fuenteEuroliga?: ResultadoEuro;

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

function obtenerConfigConfianza(nivel: NivelConfianza | null) {
  switch (nivel) {
    case 'ALTA':
      return { texto: 'Alta', color: 'bg-neon-verde', textColor: 'text-neon-verde' };
    case 'MEDIA':
      return { texto: 'Media', color: 'bg-advertencia-500', textColor: 'text-advertencia-500' };
    case 'BAJA':
      return { texto: 'Baja', color: 'bg-neon-rojo', textColor: 'text-neon-rojo' };
    default:
      return { texto: 'No certificada', color: 'bg-futurista-medio', textColor: 'text-texto-secundario' };
  }
}

function formatearFecha(fechaISO: string, zona?: string): string {
  const fecha = new Date(fechaISO);
  return fecha.toLocaleString('es-ES', {
    ...(zona ? { timeZone: zona } : {}),
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
function extraerMejorApuestaDetalle(resultado: ResultadoVista): MejorApuestaDetalle | null {
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

function numeroValido(n: unknown): n is number {
  return typeof n === 'number' && Number.isFinite(n);
}

function unidadPorMercadoFutbol(mercado: string | undefined): string {
  const m = (mercado || '').toUpperCase();
  if (m.startsWith('GOLES')) return 'goles';
  if (m.startsWith('CORNERS')) return 'corners';
  if (m.includes('DISPAROS')) return 'tiros al arco';
  return 'unidades';
}

function etiquetaPeriodoFutbol(mercado: string | undefined): string {
  const m = (mercado || '').toUpperCase();
  if (m.includes('_1T') || m === 'Q1') return 'Primer tiempo';
  if (m.includes('_2T') || m === 'Q2') return 'Segundo tiempo';
  if (m.endsWith('_FT') || m === 'COMPLETO') return 'Tiempo completo';
  return m || 'Mercado';
}

function esEstadoNoApto(resultado: ResultadoVista, detalle: MejorApuestaDetalle | null): boolean {
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
  fuenteEuroliga,
  advertencias = [],
  seleccionUsuario,
  equipoLocalId,
  equipoVisitanteId,
  onGuardar,
  onConfigurarBankroll,
  onNavegarlEquipo,
}: PropsResultadoAnalisis) {
  const mercado = resultado.metadata?.mercado as string;
  const esEuro = Boolean(fuenteEuroliga);
  const esWnba = resultado.metadata?.liga === 'wnba';
  const mercadosNoDisponibles = (esWnba ? resultado.metadata?.mercados_no_disponibles : null) as Record<string,string> | undefined;
  const motivoMercadoNoDisponible = mercadosNoDisponibles?.[mercado];
  const integral = (fuenteEuroliga?.analisis_integral ?? resultado.metadata?.analisis_integral) as AnalisisIntegral | undefined;
  const seccionIntegral = (seccion: 'ganador' | 'periodos' | 'contexto' | 'valor' | 'razones') => integral ? <SeccionesAnalisisIntegral key={`${resultado.fecha_analisis}-${seccion}`} datos={integral} seccion={seccion} local={resultado.equipo_nombre_completo} visitante={resultado.rival_nombre_completo} lado={seleccionUsuario?.lado} /> : null;
  const esCorte = resultado.es_en_vivo;
  const modo = String(resultado.metadata?.modo_analisis ?? (esCorte ? `CIERRE_Q${Object.keys(resultado.cuartos_reales ?? {}).length}` : 'PREPARTIDO'));
  const modoLabel = modo === 'HISTORICO_RECONSTRUIDO' ? 'Histórico reconstruido' : modo === 'PREPARTIDO' ? 'Prepartido' : `Corte al cierre de ${modo.replace('CIERRE_', '')}`;
  const esFutbol = resultado.metadata?.deporte === 'futbol';
  const consultaExploratoria = modo === 'HISTORICO_RECONSTRUIDO' || (esFutbol && resultado.metadata?.consulta_exploratoria === true);
  const configConfianza = obtenerConfigConfianza(esCorte ? null : resultado.nivel_confianza);

  const detalle = extraerMejorApuestaDetalle(resultado);
  const detalleVista = detalle ?? resultado.detalle_descriptivo;
  const tieneDetalleAvanzado = detalleVista != null;

  const mercadoCanon = detalle?.mercado || mercado;
  const prediccionMercado = mercadoCanon === 'COMPLETO'
    ? resultado.prediccion_juego_completo
    : (mercadoCanon ? resultado.predicciones[mercadoCanon] : null);

  const linea = numeroValido(seleccionUsuario?.linea)
    ? seleccionUsuario!.linea
    : (numeroValido(detalle?.linea) ? detalle!.linea : (resultado.linea_analizada ?? 0));

  const probabilidadOver = numeroValido(resultado.probabilidad_over)
    ? resultado.probabilidad_over!
    : (numeroValido(resultado.prediccion_ajustada?.probabilidad_over_ajustada)
      ? resultado.prediccion_ajustada!.probabilidad_over_ajustada
      : (numeroValido(prediccionMercado?.probabilidad_over) ? prediccionMercado!.probabilidad_over : null));
  const probabilidadUnder = numeroValido(resultado.probabilidad_under)
    ? resultado.probabilidad_under!
    : (numeroValido(resultado.prediccion_ajustada?.probabilidad_under_ajustada)
      ? resultado.prediccion_ajustada!.probabilidad_under_ajustada
      : (numeroValido(prediccionMercado?.probabilidad_under) ? prediccionMercado!.probabilidad_under : null));

  const mediaTotal = numeroValido(detalle?.prediccion_media)
    ? detalle!.prediccion_media
    : (numeroValido(resultado.prediccion_ajustada?.media_ajustada)
      ? resultado.prediccion_ajustada!.media_ajustada
      : (numeroValido(prediccionMercado?.media_total)
        ? prediccionMercado!.media_total
        : (numeroValido(resultado.prediccion_base?.media) ? resultado.prediccion_base!.media : null)));
  const desviacion = numeroValido(detalle?.prediccion_desviacion)
    ? detalle!.prediccion_desviacion
    : (numeroValido(resultado.prediccion_ajustada?.desviacion_base)
      ? resultado.prediccion_ajustada!.desviacion_base
      : (numeroValido(prediccionMercado?.desviacion_total) ? prediccionMercado!.desviacion_total : null));

  const unidadAnalisis = esFutbol ? unidadPorMercadoFutbol(mercadoCanon) : 'puntos';

  const prediccionGanador = esEuro ? resultado.prediccion_juego_completo : mercadoCanon === 'COMPLETO'
    ? resultado.prediccion_juego_completo
    : (mercadoCanon ? resultado.predicciones[mercadoCanon] : null);
  const etiquetaGanador = esEuro ? 'Ventaja al terminar la regulación (sin OT)' : mercadoCanon === 'COMPLETO' ? 'Ganador del partido' : (esFutbol ? 'Ganador estimado' : 'Ganador del cuarto');
  const etiquetaPeriodo = esFutbol
    ? etiquetaPeriodoFutbol(mercadoCanon)
    : mercadoCanon === 'Q1'
      ? 'Primer cuarto'
      : mercadoCanon === 'Q2'
        ? 'Segundo cuarto'
        : mercadoCanon === 'COMPLETO'
          ? 'Juego completo'
          : mercadoCanon;
  const nombreGanador = prediccionGanador?.ganador_probable === 'equipo'
    ? resultado.equipo_nombre_completo
    : resultado.rival_nombre_completo;
  // `probabilidad_ganador` es la probabilidad del equipo analizado (local).
  // Si el ganador probable es el rival, presentar su complemento.
  const probabilidadGanadorMostrado = prediccionGanador && numeroValido(prediccionGanador.probabilidad_ganador)
    ? (prediccionGanador.ganador_tres_vias
      ? Math.max(prediccionGanador.ganador_tres_vias.local, prediccionGanador.ganador_tres_vias.empate, prediccionGanador.ganador_tres_vias.visitante)
      : prediccionGanador.ganador_probable === 'equipo'
      ? prediccionGanador.probabilidad_ganador
      : 1 - prediccionGanador.probabilidad_ganador)
    : null;

  // Determinar si la predicción del usuario coincide con el sistema
  const tieneRecomendacionSistema = Boolean(detalle || resultado.mejor_apuesta);
  const sistemaRecomienda: LadoApuesta = (probabilidadOver !== null && probabilidadUnder !== null && probabilidadOver > probabilidadUnder) ? 'OVER' : 'UNDER';
  const coincideConSistema = Boolean(tieneRecomendacionSistema && seleccionUsuario?.lado === sistemaRecomienda);
  const puedeGuardar = Boolean(!consultaExploratoria && seleccionUsuario && linea > 0 && onGuardar);
  const probabilidadesNulas = probabilidadOver === null || probabilidadUnder === null;
  const probabilidadesCero = (probabilidadOver ?? 0) <= 0 && (probabilidadUnder ?? 0) <= 0;
  const metricaObjetivoInvalida = mediaTotal === null || desviacion === null || probabilidadesNulas || probabilidadesCero;

  const objetivoMeta = resultado.metadata?.objetivo as { calidad_datos?: { muestra_insuficiente?: boolean; datos_incompletos?: boolean; penalizaciones_aplicadas?: string[] }; trazabilidad?: { estado_operativo_mercado?: string; motivos_estado_operativo?: string[] } } | undefined;
  const penalizacionesObjetivo = objetivoMeta?.calidad_datos?.penalizaciones_aplicadas || [];
  const estadoOperativoMercado = esEuro || esCorte ? 'NO_CERTIFICADO' : objetivoMeta?.trazabilidad?.estado_operativo_mercado || 'LABORATORIO';
  const motivosEstadoOperativo = objetivoMeta?.trazabilidad?.motivos_estado_operativo || [];
  const gateCriticoBeta = Boolean(
    objetivoMeta?.calidad_datos?.muestra_insuficiente
    || objetivoMeta?.calidad_datos?.datos_incompletos
    || penalizacionesObjetivo.includes('estado_mercados_vacio')
    || penalizacionesObjetivo.includes('mercado_objetivo_fuera_estado_mercados')
  );

  const hayAjusteContextualReal = Boolean(
    resultado.prediccion_ajustada
    && resultado.prediccion_base
    && (
      Math.abs((resultado.prediccion_ajustada.media_ajustada ?? 0) - (resultado.prediccion_base.media ?? 0)) > 1e-6
      || Math.abs((resultado.prediccion_ajustada.probabilidad_over_ajustada ?? 0) - (resultado.prediccion_base.probabilidad_over ?? 0)) > 1e-6
      || Math.abs((resultado.prediccion_ajustada.probabilidad_under_ajustada ?? 0) - (resultado.prediccion_base.probabilidad_under ?? 0)) > 1e-6
      || Boolean(resultado.prediccion_ajustada.ajustes_aplicados?.ajustes?.length)
    )
  );

  // Fase 2: Extraer datos avanzados
  const noApto = esEstadoNoApto(resultado, detalle);

  return (
    <div className="space-y-6 animate-entrada">
      {/* ═══════════════════════════════════════════════════════════
          1. ADVERTENCIAS DEL BACKEND (si hay)
          ═══════════════════════════════════════════════════════════ */}
      {advertencias.length > 0 && (
        <PanelAdvertencias advertencias={advertencias} />
      )}

      <div className="tarjeta p-3 border border-neon-cyan/20">
        <p className="text-xs uppercase tracking-wider text-texto-terciario">Estado operativo del mercado</p>
        <p className="text-sm font-semibold text-neon-cyan">{estadoOperativoMercado}</p>
        {!esEuro && !esWnba && !esCorte && !consultaExploratoria && estadoOperativoMercado !== 'PROMOCIONABLE' && (
          <p className="text-xs text-advertencia-500 mt-1">Modo activo: PAPER/SHADOW (validación prolongada, no mercado promocionado).</p>
        )}
        {motivosEstadoOperativo.length > 0 && (
          <p className="text-xs text-texto-secundario mt-1">Motivos: {motivosEstadoOperativo.join(', ')}</p>
        )}
      </div>

      {gateCriticoBeta && !consultaExploratoria && (
        <PanelAdvertencias advertencias={[
          'MODO VALIDACIÓN BETA: mercado no promocionable. Este resultado es solo para shadow/paper trading y monitoreo cuantitativo.',
          ...penalizacionesObjetivo.map((p) => `Gate crítico activo: ${p}`),
        ]} />
      )}

      {/* ═══════════════════════════════════════════════════════════
          2. ENCABEZADO DEL PARTIDO
          ═══════════════════════════════════════════════════════════ */}
      <div className="tarjeta relative overflow-hidden">
        {/* Línea decorativa superior */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-neon-cyan via-neon-magenta to-neon-cyan" />

        <p className="text-center text-xs text-neon-cyan mb-4">{esEuro ? 'Euroliga' : esWnba ? 'WNBA' : esFutbol ? 'Fútbol' : 'NBA'} · {modoLabel}{esEuro || esCorte ? ' · Regulación sin OT · RAW' : ''}</p>
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
              {(esEuro || (esWnba && !resultado.metadata.incluye_ot)) && mercado === 'COMPLETO' ? 'REGULACIÓN · 40 MIN · SIN OT' : esFutbol ? etiquetaPeriodo.toUpperCase() : (mercado === 'COMPLETO' ? 'JUEGO COMPLETO' : `CUARTO ${mercado}`)}
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
            <span className="font-mono">{esFutbol && typeof resultado.metadata?.fecha_partido === 'string'
              ? `Partido: ${formatearFecha(resultado.metadata.fecha_partido, 'America/Bogota')} COT`
              : formatearFecha(resultado.fecha_analisis)}</span>
            {fuenteEuroliga && <span>Datos hasta {fuenteEuroliga.corte_datos}</span>}
          </div>
          <div className="flex items-center gap-2">
            <Activity size={14} className={configConfianza.textColor} />
            <span>Confianza:</span>
            <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${configConfianza.color} ${resultado.nivel_confianza && !esCorte ? 'text-futurista-negro' : 'text-texto-secundario'}`}>
              {configConfianza.texto}
            </span>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          3. ADVERTENCIA NO APTO (si aplica)
          Se muestra como aviso pero el análisis continúa visible
          ═══════════════════════════════════════════════════════════ */}
      {consultaExploratoria && <div className="tarjeta p-4 border border-neon-cyan/20">
        <p className="text-sm text-neon-cyan">Consulta exploratoria RAW · sin recomendación operativa</p>
        <p className="mt-1 text-xs text-texto-secundario">Las probabilidades no están calibradas ni acreditan rendimiento futuro. Una reconstrucción histórica no es un pronóstico emitido entonces.</p>
        <p className="mt-1 text-xs text-texto-secundario">Consulta realizada: {formatearFecha(resultado.fecha_analisis, 'America/Bogota')} COT.</p>
      </div>}
      {noApto && !consultaExploratoria && (
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
                {esEuro || esCorte || esFutbol || consultaExploratoria ? 'Tu análisis: ' : 'Tu apuesta: '}<span className={`font-semibold ${seleccionUsuario.lado === 'OVER' ? 'text-neon-verde' : 'text-neon-rojo'}`}>
                  {seleccionUsuario.lado === 'OVER' ? 'Over' : 'Under'} {seleccionUsuario.linea}
                </span>
              </p>
              <p className={`text-xs ${coincideConSistema ? 'text-neon-verde' : 'text-advertencia-500'}`}>
                {!tieneRecomendacionSistema
                  ? 'Sin recomendación formal del sistema para este mercado en el estado actual.'
                  : (coincideConSistema
                    ? 'Tu predicción coincide con la recomendación del sistema'
                    : `El sistema recomienda ${sistemaRecomienda === 'OVER' ? 'Over' : 'Under'} - considera revisar`)
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {seccionIntegral('ganador')}
      {!integral && !esFutbol && prediccionGanador && probabilidadGanadorMostrado !== null && (
        <div className="tarjeta p-4 border border-neon-cyan/20">
          <p className="text-xs uppercase tracking-wider text-neon-cyan font-semibold">{etiquetaGanador}</p>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-lg font-futurista text-texto-principal">{prediccionGanador.ganador_tres_vias && prediccionGanador.ganador_tres_vias.empate >= Math.max(prediccionGanador.ganador_tres_vias.local,prediccionGanador.ganador_tres_vias.visitante) ? 'Empate' : nombreGanador}</p>
              <p className="text-sm text-texto-secundario">
                Probabilidad: <span className="text-neon-verde font-semibold">{((probabilidadGanadorMostrado ?? 0) * 100).toFixed(1)}%</span>
              </p>
            </div>
            <div className="text-right text-xs text-texto-secundario">
              <p>Marcador estimado: {prediccionGanador.media_equipo.toFixed(1)} - {prediccionGanador.media_rival.toFixed(1)}</p>
              <p>Total estimado: {prediccionGanador.media_total.toFixed(1)}</p>
            </div>
          </div>
          {fuenteEuroliga && <p className="text-xs text-texto-secundario mt-2">{fuenteEuroliga.ventaja_regulacion.definicion}</p>}
        </div>
      )}
      {motivoMercadoNoDisponible && <div className="tarjeta p-4 border border-neon-cyan/20">
        <p className="text-xs uppercase tracking-wider text-neon-cyan font-semibold">{etiquetaGanador}</p>
        <p className="text-lg font-futurista text-texto-principal">N/D</p>
        <p className="text-sm text-texto-secundario">{motivoMercadoNoDisponible}</p>
      </div>}

      {/* ═══════════════════════════════════════════════════════════
          5. PROBABILIDADES
          ═══════════════════════════════════════════════════════════ */}
      {linea > 0 && !metricaObjetivoInvalida && (
        <TarjetaProbabilidad
          linea={linea}
          probabilidadOver={probabilidadOver}
          probabilidadUnder={probabilidadUnder}
          mediaTotal={mediaTotal}
          desviacion={desviacion}
          seleccionUsuario={seleccionUsuario?.lado}
          unidadLabel={unidadAnalisis}
          probabilidadPush={esWnba && !Number.isInteger(linea) ? undefined : integral?.probabilidades.push ?? fuenteEuroliga?.probabilidades.push ?? (typeof resultado.metadata?.probabilidad_push === 'number' ? resultado.metadata.probabilidad_push : undefined)}
          decimales={esEuro ? 2 : 1}
        />
      )}

      {metricaObjetivoInvalida && (
        <PanelAdvertencias advertencias={[
          motivoMercadoNoDisponible ? `${motivoMercadoNoDisponible} Media, desviación, Over/Under y push de este mercado: N/D.` : 'Datos insuficientes del mercado objetivo: no se puede renderizar media/desviación/probabilidades sin degradación honesta.',
        ]} />
      )}

      {seccionIntegral('periodos')}
      {!integral && !esFutbol && <div className="tarjeta p-6 space-y-3">
        <h3 className="text-lg font-futurista">Proyección por periodo</h3>
        <p className="text-xs text-texto-secundario">{esEuro ? 'Cuartos de 10 minutos; regulación de 40 minutos, sin OT.' : esWnba ? `Cuartos de 10 minutos; regulación de 40 minutos. Juego completo ${resultado.metadata.incluye_ot ? 'incluye OT; la suma de cuartos conserva regulación' : 'sin OT en cortes entre cuartos'}.` : 'Cuartos de 12 minutos; la suma de cuartos no incluye prórroga.'} Observado no significa pronosticado.</p>
        <div className="overflow-x-auto"><table className="w-full text-sm text-left"><thead><tr><th className="p-2">Periodo</th><th className="p-2">Local</th><th className="p-2">Visitante</th><th className="p-2">Total</th><th className="p-2">Desviación</th></tr></thead><tbody>{[...new Set([...Object.keys(resultado.predicciones),...Object.keys(mercadosNoDisponibles??{})])].sort((a,b) => ['Q1','Q2','Q3','Q4','COMPLETO'].indexOf(a)-['Q1','Q2','Q3','Q4','COMPLETO'].indexOf(b)).map(m => {
          const p=resultado.predicciones[m];
          return <tr key={m} title={mercadosNoDisponibles?.[m]} className="border-t border-neon-cyan/10"><th className="p-2">{m}{resultado.cuartos_reales?.[m] ? ' (observado)' : ''}</th><td className="p-2">{p?p.media_equipo.toFixed(2):'N/D'}</td><td className="p-2">{p?p.media_rival.toFixed(2):'N/D'}</td><td className="p-2">{p?p.media_total.toFixed(2):'N/D'}</td><td className="p-2">{p?p.desviacion_total.toFixed(2):'N/D'}</td></tr>;
        })}</tbody></table></div>
        {mercadosNoDisponibles && Object.entries(mercadosNoDisponibles).map(([m,motivo])=><p key={m} className="text-xs text-texto-secundario">{motivo}</p>)}
      </div>}
      {(esCorte || esEuro) && <div className="tarjeta p-4 text-sm text-texto-secundario space-y-2">
        <p>{modoLabel}. No es un pronóstico con reloj ni marcador parcial actualizado.</p>
        <p>{fuenteEuroliga ? (esCorte ? 'Distribución gaussiana condicionada a cuartos completos, sin calibración probabilística acreditada.' : 'Distribución gaussiana prepartido, sin calibración probabilística acreditada.') : String(resultado.metadata.metodo_live)}</p>
        {fuenteEuroliga && <p>Intervalo predictivo 80 % RAW: {(integral ? [-1,1].map(signo=>(mediaTotal ?? 0)+signo*1.2815515655*(desviacion ?? 0)) : fuenteEuroliga.predicciones[fuenteEuroliga.mercado].intervalo_predictivo_80_raw).map(n=>n.toFixed(2)).join(' – ')}. Cobertura nominal, no certificada. El escenario contextual conserva la dispersión Ridge sin validación adicional.</p>}
      </div>}

      {/* ═══════════════════════════════════════════════════════════
          6. SECCIÓN: AJUSTES CONTEXTUALES (Fase 3)
          ═══════════════════════════════════════════════════════════ */}

      {/* Panel de Comparación Base vs Ajustada */}
      {seccionIntegral('contexto')}
      {!integral && hayAjusteContextualReal && resultado.prediccion_ajustada && resultado.prediccion_base
        && numeroValido(resultado.prediccion_base.media)
        && numeroValido(resultado.prediccion_base.probabilidad_over)
        && numeroValido(resultado.prediccion_base.probabilidad_under)
        && numeroValido(resultado.prediccion_ajustada.media_ajustada)
        && numeroValido(resultado.prediccion_ajustada.probabilidad_over_ajustada)
        && numeroValido(resultado.prediccion_ajustada.probabilidad_under_ajustada) && (
        <PanelComparacionPrediccion
          prediccionBase={{
            media: resultado.prediccion_base.media,
            probabilidadOver: resultado.prediccion_base.probabilidad_over,
            probabilidadUnder: resultado.prediccion_base.probabilidad_under,
          }}
          prediccionAjustada={{
            media: resultado.prediccion_ajustada.media_ajustada,
            probabilidadOver: resultado.prediccion_ajustada.probabilidad_over_ajustada,
            probabilidadUnder: resultado.prediccion_ajustada.probabilidad_under_ajustada,
          }}
          linea={linea}
          recomendacionHabilitada={!esWnba}
          confianzaBase={resultado.prediccion_ajustada.confianza_base}
          confianzaAjustada={resultado.prediccion_ajustada.confianza_ajustada}
          unidadLabel={unidadAnalisis}
        />
      )}

      {!integral && !hayAjusteContextualReal && resultado.prediccion_ajustada && resultado.prediccion_base && (
        <PanelAdvertencias advertencias={[
          'Predicción base y ajustada coinciden para el mercado objetivo: no hubo ajuste contextual efectivo en esta corrida.',
        ]} />
      )}

      {/* Lista de Ajustes Aplicados */}
      {!integral && resultado.ajustes && resultado.ajustes.ajustes && resultado.ajustes.ajustes.length > 0 && (
        <SeccionAjustesAplicados
          ajustes={resultado.ajustes.ajustes}
          ajusteTotal={resultado.ajustes.ajuste_total_capped}
          fueCapped={resultado.ajustes.fue_capped}
          inicialmenteExpandido={true}
          unidadLabel={unidadAnalisis}
        />
      )}

      {/* ═══════════════════════════════════════════════════════════
          7. BLOQUE DE-VIG + CALIBRACIÓN (Fase 2)
          Solo mostrar si hay detalle avanzado
          ═══════════════════════════════════════════════════════════ */}
      {!consultaExploratoria && !integral && tieneDetalleAvanzado && detalleVista && (
        <div className="space-y-4">
          <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-cyan flex items-center gap-2">
            <span className="w-8 h-[2px] bg-gradient-to-r from-neon-cyan to-transparent" />
            Análisis de Valor
          </h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* TarjetaDeVig */}
            <TarjetaDeVig
              calibrado={!esWnba || detalleVista.p_calibrada != null}
              metodo={detalleVista.devig_metodo ?? 'no_aplicado'}
              overround={detalleVista.devig_overround ?? null}
              pMktRaw={detalleVista.devig_p_mkt_raw ?? null}
              pMktFair={detalleVista.devig_p_mkt_fair ?? null}
              edgeRaw={detalleVista.edge_raw ?? null}
              edgeReal={detalleVista.edge_real ?? null}
              advertencias={detalleVista.devig_advertencias ?? []}
            />

            {/* SeccionCalibracion */}
            <div className="flex flex-col justify-center">
              <SeccionCalibracion
                pRaw={detalleVista.p_raw ?? null}
                pCalibrada={detalleVista.p_calibrada ?? null}
                calibradorUsado={detalleVista.calibrador_usado ?? null}
                unidadDelta="pp"
              />
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          8. BLOQUE SCORE + SIZING (Fase 2)
          Solo mostrar si hay detalle avanzado
          ═══════════════════════════════════════════════════════════ */}
      {!consultaExploratoria && !integral && tieneDetalleAvanzado && detalleVista && (
        <div className="space-y-4">
          <h3 className="text-sm font-futurista font-bold uppercase tracking-wider text-neon-magenta flex items-center gap-2">
            <span className="w-8 h-[2px] bg-gradient-to-r from-neon-magenta to-transparent" />
            Decisión y Riesgo
          </h3>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* TarjetaScore */}
            <TarjetaScore
              conservarCampos={esWnba}
              scoreTotal={detalleVista.score_total ?? null}
              componentes={detalleVista.score_componentes ?? null}
              explicacion={detalleVista.score_explicacion ?? null}
              penalizaciones={detalleVista.score_penalizaciones ?? []}
              valorEsperado={detalleVista.valor_esperado ?? null}
            />

            {/* TarjetaSizing */}
            <TarjetaSizing
              conservarCampos={esWnba}
              kellyFull={detalleVista.kelly_full ?? null}
              kellyFraccional={detalleVista.kelly_fraccional ?? null}
              fraccionKelly={detalleVista.fraccion_kelly ?? null}
              stake={detalleVista.stake ?? null}
              stakePorcentaje={detalleVista.stake_porcentaje ?? null}
              bankroll={detalleVista.bankroll_momento ?? null}
              perfilRiesgo={detalleVista.perfil_riesgo_usado ?? null}
              advertencias={detalleVista.sizing_advertencias ?? []}
              penalizaciones={detalleVista.sizing_penalizaciones ?? null}
              aplicaronCaps={detalleVista.aplicaron_caps ?? false}
              onConfigurarBankroll={onConfigurarBankroll}
            />
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════════════
          9. ANÁLISIS DE MERCADO (legacy, si hay cuota pero no detalle avanzado)
          ═══════════════════════════════════════════════════════════ */}
      {seccionIntegral('valor')}
      {!integral && !tieneDetalleAvanzado && resultado.analisis_mercado && (
        <AnalisisMercadoCard analisis={resultado.analisis_mercado} />
      )}

      {/* ═══════════════════════════════════════════════════════════
          10. SECCIÓN: CONTEXTO DEL PARTIDO (Fase 3)
          ═══════════════════════════════════════════════════════════ */}

      {/* Head-to-Head */}
      {(!gateCriticoBeta || esFutbol) && resultado.contexto?.h2h && (
        <SeccionH2H
          nota={esFutbol ? "Balance de victorias por goles; medias y línea por la métrica seleccionada." : undefined}
          h2h={resultado.contexto.h2h}
          equipoNombre={resultado.equipo_nombre_completo}
          rivalNombre={resultado.rival_nombre_completo}
          lineaActual={linea}
          unidadLabel={unidadAnalisis}
          inicialmenteExpandido={false}
        />
      )}

      {/* Forma Reciente */}
      {(!gateCriticoBeta || esFutbol) && resultado.contexto && (esFutbol || resultado.contexto.forma_equipo || resultado.contexto.forma_rival) && (
        <SeccionFormaReciente
          nota={esFutbol ? "V/E/D y racha por goles; promedios de la métrica y periodo seleccionados." : undefined}
          formaEquipo={resultado.contexto.forma_equipo}
          formaRival={resultado.contexto.forma_rival}
          descansoEquipo={resultado.contexto.descanso_equipo}
          descansoRival={resultado.contexto.descanso_rival}
          equipoNombre={resultado.equipo_nombre_completo}
          rivalNombre={resultado.rival_nombre_completo}
          equipoId={resultado.ubicacion === 'LOCAL' ? equipoLocalId : equipoVisitanteId}
          rivalId={resultado.ubicacion === 'LOCAL' ? equipoVisitanteId : equipoLocalId}
          inicialmenteExpandido={true}
          deporte={esFutbol ? 'futbol' : 'baloncesto'}
          onVerEstadisticas={onNavegarlEquipo}
        />
      )}

      {fuenteEuroliga && <>
        <SeccionH2H h2h={h2hEuroliga(fuenteEuroliga)} equipoNombre={fuenteEuroliga.equipo_local} rivalNombre={fuenteEuroliga.equipo_visitante}
          compararLinea={false} nota="Marcadores finales que pueden incluir OT; no se comparan con la línea de regulación ni con una línea por cuarto." unidadLabel="puntos" />
        <SeccionFormaReciente formaEquipo={formaEquipoEuroliga(fuenteEuroliga, fuenteEuroliga.equipo_local)}
          formaRival={formaEquipoEuroliga(fuenteEuroliga, fuenteEuroliga.equipo_visitante)} descansoEquipo={null} descansoRival={null}
          equipoNombre={fuenteEuroliga.equipo_local} rivalNombre={fuenteEuroliga.equipo_visitante} soloRegulacionDescriptiva
          nota="Últimos 10 finales previos disponibles: resultados, puntos a favor/en contra y balance en regulación. El uso de forma en el escenario contextual se desglosa en Ajustes aplicados; la salida Ridge original se conserva." />
        <SeccionHistorialEuroliga equipos={fuenteEuroliga.contexto.equipos} local={fuenteEuroliga.equipo_local}
          visitante={fuenteEuroliga.equipo_visitante} corte={fuenteEuroliga.contexto.corte_exclusivo ?? fuenteEuroliga.fecha_partido} />
        <PanelDiagnosticoEuroliga resultado={fuenteEuroliga} />
      </>}
      {esCorte && !esEuro && <details className="tarjeta p-4 text-xs text-texto-secundario"><summary className="cursor-pointer">Modelo y corte {esWnba ? 'WNBA' : 'NBA'}</summary>
        <p className="mt-3">Versión: {String(resultado.metadata.modelo_version ?? 'N/D')}. Peso heurístico de ritmo: {esWnba ? 'N/D: WNBA usa covarianza condicional, no un peso heurístico de ritmo' : String(resultado.metadata.peso_en_vivo ?? 'N/D')}.</p>
        <p>Solo consulta. No se guarda como apuesta ni predicción prepartido y no acredita calibración.</p>
      </details>}

      {/* ═══════════════════════════════════════════════════════════
          11. HISTORIAL DETALLADO
          ═══════════════════════════════════════════════════════════ */}
      {(!gateCriticoBeta || esFutbol) && !esEuro && equipoLocalId && equipoVisitanteId && linea > 0 && mercadoCanon && (
        <SeccionHistorialDetallado
          equipoLocalId={equipoLocalId}
          equipoLocalNombre={resultado.equipo_nombre_completo}
          equipoLocalAbr={resultado.equipo?.toUpperCase() || 'LOC'}
          equipoVisitanteId={equipoVisitanteId}
          equipoVisitanteNombre={resultado.rival_nombre_completo}
          equipoVisitanteAbr={resultado.rival?.toUpperCase() || 'VIS'}
          mercado={esFutbol ? (mercadoCanon as TipoMercadoFutbol) : (mercado as Mercado)}
          linea={linea}
          deporte={esFutbol ? 'futbol' : 'baloncesto'}
          fuenteWnba={esWnba ? String(resultado.metadata.analisis_id) : undefined}
          inicialmenteExpandido={false}
        />
      )}

      {/* ═══════════════════════════════════════════════════════════
          12. RAZONES
          ═══════════════════════════════════════════════════════════ */}
      {seccionIntegral('razones')}
      {!integral && !gateCriticoBeta && !esEuro && (
        <ListaRazones razones={resultado.razones} deporte={esFutbol ? 'futbol' : 'baloncesto'} unidadLabel={unidadAnalisis} />
      )}

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
