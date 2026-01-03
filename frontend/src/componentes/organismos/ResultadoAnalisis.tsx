/**
 * ResultadoAnalisis.tsx — Contenedor principal de resultados
 */

import { Clock, MapPin, Activity } from 'lucide-react';
import { ResultadoAnalisis as TipoResultado, NivelConfianza } from '../../tipos';
import { TarjetaProbabilidad } from './TarjetaProbabilidad';
import { ListaRazones } from './ListaRazones';
import { AnalisisMercadoCard } from './AnalisisMercadoCard';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsResultadoAnalisis {
  /** Datos del resultado */
  resultado: TipoResultado;
}

// ══════════════════════════════════════════════════════════════
// UTILIDADES
// ══════════════════════════════════════════════════════════════

function obtenerConfigConfianza(nivel: NivelConfianza) {
  switch (nivel) {
    case 'ALTA':
      return { texto: 'Alta', color: 'bg-exito-500' };
    case 'MEDIA':
      return { texto: 'Media', color: 'bg-advertencia-500' };
    case 'BAJA':
      return { texto: 'Baja', color: 'bg-error-500' };
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
 * Muestra todos los resultados del análisis
 */
export function ResultadoAnalisis({ resultado }: PropsResultadoAnalisis) {
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

  return (
    <div className="space-y-6 animate-entrada">
      {/* Encabezado del resultado */}
      <div className="bg-gradient-to-r from-nba-azul to-nba-azul/80 rounded-xl p-6 text-white">
        {/* Equipos */}
        <div className="text-center mb-4">
          <div className="flex items-center justify-center gap-4 text-2xl font-bold">
            <span>{resultado.equipo_nombre_completo}</span>
            <span className="text-white/60">vs</span>
            <span>{resultado.rival_nombre_completo}</span>
          </div>
          <div className="text-white/80 mt-1">
            Mercado: {mercado === 'COMPLETO' ? 'Juego Completo' : mercado}
          </div>
        </div>

        {/* Metadatos */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-white/80">
          <div className="flex items-center gap-1">
            <MapPin size={14} />
            <span>{resultado.equipo_nombre_completo} (Local)</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock size={14} />
            <span>{formatearFecha(resultado.fecha_analisis)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Activity size={14} />
            <span>Confianza: </span>
            <span className={`px-2 py-0.5 rounded-full text-white text-xs ${configConfianza.color}`}>
              {configConfianza.texto}
            </span>
          </div>
        </div>
      </div>

      {/* Probabilidades */}
      {linea > 0 && (
        <TarjetaProbabilidad
          linea={linea}
          probabilidadOver={probabilidadOver}
          probabilidadUnder={probabilidadUnder}
          mediaTotal={mediaTotal}
          desviacion={desviacion}
        />
      )}

      {/* Análisis de mercado (si hay cuota) */}
      {resultado.analisis_mercado && (
        <AnalisisMercadoCard analisis={resultado.analisis_mercado} />
      )}

      {/* Razones */}
      <ListaRazones razones={resultado.razones} />
    </div>
  );
}
