// hace parte del diseño de analisis
/**
 * ResultadoAnalisis.tsx — Contenedor principal de resultados con estilo futurista
 */

import { Clock, MapPin, Activity, CheckCircle, AlertTriangle, BookOpen } from 'lucide-react';
import { ResultadoAnalisis as TipoResultado, NivelConfianza, LadoApuesta } from '../../tipos';
import { TarjetaProbabilidad } from './TarjetaProbabilidad';
import { ListaRazones } from './ListaRazones';
import { AnalisisMercadoCard } from './AnalisisMercadoCard';
import { Boton } from '../atomos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsResultadoAnalisis {
  /** Datos del resultado */
  resultado: TipoResultado;
  /** Selección del usuario (Over/Under) */
  seleccionUsuario?: {
    lado: LadoApuesta;
    linea: number;
  } | null;
  /** Acción para guardar en bitácora */
  onGuardar?: () => void;
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

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra todos los resultados del análisis con estilo futurista
 */
export function ResultadoAnalisis({ resultado, seleccionUsuario, onGuardar }: PropsResultadoAnalisis) {
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

  return (
    <div className="space-y-6 animate-entrada">
      {/* Encabezado del resultado */}
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

      {/* Indicador de apuesta del usuario */}
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

      {/* Probabilidades */}
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

      {/* Análisis de mercado (si hay cuota) */}
      {resultado.analisis_mercado && (
        <AnalisisMercadoCard analisis={resultado.analisis_mercado} />
      )}

      {/* Razones */}
      <ListaRazones razones={resultado.razones} />

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
    </div>
  );
}
