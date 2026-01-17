/**
 * ListaRazones.tsx — Lista de razones con estilo futurista
 */

import { ArrowUp, ArrowDown, Info } from 'lucide-react';
import { Tarjeta } from '../atomos';
import { RazonPrediccion } from '../../tipos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsListaRazones {
  /** Lista de razones */
  razones: RazonPrediccion[];
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

function obtenerExplicacionRazon(razon: RazonPrediccion): string | null {
  switch (razon.factor) {
    case 'total_estimado':
      return 'Es la suma de puntos que el modelo espera entre ambos equipos.';
    case 'ataque_equipo':
      return 'Indica cuántos puntos se estima que anotará el equipo según sus datos recientes.';
    case 'ataque_rival':
      return 'Indica cuántos puntos se estima que anotará el rival según sus datos recientes.';
    case 'prediccion_sistema':
      return 'Es el total de puntos que calcula el sistema con los datos disponibles; se compara con la línea si existe.';
    case 'resumen_neto':
      return 'Resume cuánto se ajustó la predicción por el contexto (descanso, rachas, etc.).';
    case 'back_to_back':
      return 'Cuando hay partidos en días seguidos, el cansancio suele bajar el ritmo y los puntos.';
    case 'descanso_asimetrico':
      return 'Un equipo tuvo más descanso que el otro; eso puede darle ventaja y cambiar la proyección.';
    case 'h2h_tendencia':
      return 'Se considera lo que pasó en enfrentamientos directos recientes para ajustar el total.';
    case 'forma_ofensiva_equipo':
      return 'Compara los puntos recientes del equipo con su promedio de temporada para ajustar la predicción.';
    case 'forma_ofensiva_rival':
      return 'Compara los puntos recientes del rival con su promedio de temporada para ajustar la predicción.';
    default:
      return 'Este factor ajusta la predicción según información contextual del partido.';
  }
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE INTERNO
// ══════════════════════════════════════════════════════════════

function ItemRazon({ razon }: { razon: RazonPrediccion }) {
  const esSube = razon.direccion === 'sube';
  const Icono = esSube ? ArrowUp : ArrowDown;
  const explicacion = obtenerExplicacionRazon(razon);

  return (
    <li className="flex items-start gap-3 py-3 border-b border-neon-cyan/10 last:border-0">
      {/* Indicador de dirección */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border ${
          esSube
            ? 'bg-neon-verde/10 border-neon-verde/30 text-neon-verde'
            : 'bg-neon-rojo/10 border-neon-rojo/30 text-neon-rojo'
        }`}
      >
        <Icono size={16} />
      </div>

      {/* Contenido */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-texto-principal">
          {razon.descripcion}
        </p>
        {explicacion && (
          <p className="text-xs text-texto-secundario mt-1">
            En simple: {explicacion}
          </p>
        )}
        <div className="flex items-center gap-3 mt-1">
          <span className="text-xs text-texto-terciario font-mono">
            {razon.factor}
          </span>
          <span className={`text-xs font-mono font-semibold ${esSube ? 'text-neon-verde' : 'text-neon-rojo'}`}>
            {razon.impacto >= 0 ? '+' : ''}{razon.impacto.toFixed(1)} pts
          </span>
        </div>
      </div>
    </li>
  );
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

/**
 * Muestra las razones que justifican la predicción
 */
export function ListaRazones({ razones }: PropsListaRazones) {
  if (razones.length === 0) {
    return null;
  }

  return (
    <Tarjeta className="animate-deslizar-arriba">
      {/* Encabezado */}
      <div className="flex items-center gap-2 mb-4 pb-3 border-b border-neon-cyan/10">
        <div className="w-8 h-8 rounded-lg bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center">
          <Info className="text-neon-cyan" size={16} />
        </div>
        <h3 className="text-lg font-futurista font-semibold text-texto-principal tracking-wider">
          RAZONES DEL ANÁLISIS
        </h3>
      </div>

      {/* Lista de razones */}
      <ul>
        {razones.map((razon, indice) => (
          <ItemRazon key={`${razon.factor}-${indice}`} razon={razon} />
        ))}
      </ul>
    </Tarjeta>
  );
}
