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
} from '../moleculas';

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

  /** Acción para guardar en bitácora */
  onGuardar?: () => void;

  /** Acción para configurar bankroll (Fase 4 placeholder) */
  onConfigurarBankroll?: () => void;
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
  onGuardar,
  onConfigurarBankroll,
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

      {noApto ? (
        <>
          <TarjetaNoApta mensaje={resultado.mensaje_apuesta} candidatos={resultado.candidatos} />
          {resultado.razones && resultado.razones.length > 0 && (
            <ListaRazones razones={resultado.razones} />
          )}
        </>
      ) : (
        <>
          {/* ═══════════════════════════════════════════════════════════
              3. INDICADOR DE APUESTA DEL USUARIO
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

          {/* ═══════════════════════════════════════════════════════════
              4. PROBABILIDADES
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
              5. BLOQUE DE-VIG + CALIBRACIÓN (Fase 2)
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
              6. BLOQUE SCORE + SIZING (Fase 2)
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
                  onConfigurarBankroll={onConfigurarBankroll}
                />
              </div>
            </div>
          )}

          {/* ═══════════════════════════════════════════════════════════
              7. ANÁLISIS DE MERCADO (legacy, si hay cuota pero no detalle avanzado)
              ═══════════════════════════════════════════════════════════ */}  
          {!tieneDetalleAvanzado && resultado.analisis_mercado && (
            <AnalisisMercadoCard analisis={resultado.analisis_mercado} />
          )}

          {/* ═══════════════════════════════════════════════════════════
              8. RAZONES
              ═══════════════════════════════════════════════════════════ */}  
          <ListaRazones razones={resultado.razones} />

          {/* ═══════════════════════════════════════════════════════════
              9. GUARDAR EN BITÁCORA
              ═══════════════════════════════════════════════════════════ */}  
          {puedeGuardar && (
            <div className="tarjeta p-4 flex items-center justify-between gap-4">
              <div>
                <p className="text-sm text-texto-secundario">Guarda esta apuesta en tu bitácora</p>
                <p className="text-xs text-texto-terciario">Se guardará el snapshot del análisis</p>
              </div>
              <Boton variante="primario" iconoInicio={<BookOpen size={16} />} onClick={onGuardar}>
                Guardar en Bitácora
              </Boton>
            </div>
          )}
        </>
      )}
    </div>
  );
}
