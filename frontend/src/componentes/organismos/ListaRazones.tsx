/**
 * ListaRazones.tsx — Lista de razones que explican la predicción
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
// COMPONENTE INTERNO
// ══════════════════════════════════════════════════════════════

function ItemRazon({ razon }: { razon: RazonPrediccion }) {
  const esSube = razon.direccion === 'sube';
  const Icono = esSube ? ArrowUp : ArrowDown;

  return (
    <li className="flex items-start gap-3 py-3 border-b border-nba-gris-100 last:border-0">
      {/* Indicador de dirección */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          esSube ? 'bg-over-claro text-over-oscuro' : 'bg-under-claro text-under-oscuro'
        }`}
      >
        <Icono size={16} />
      </div>

      {/* Contenido */}
      <div className="flex-1 min-w-0">
        <p className="text-sm text-nba-gris-900">
          {razon.descripcion}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-nba-gris-500">
            Factor: {razon.factor}
          </span>
          <span className={`text-xs font-medium ${esSube ? 'text-over-oscuro' : 'text-under-oscuro'}`}>
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
      <div className="flex items-center gap-2 mb-4">
        <Info className="text-nba-azul" size={20} />
        <h3 className="text-lg font-semibold text-nba-gris-900">
          Razones del Análisis
        </h3>
      </div>

      {/* Lista de razones */}
      <ul className="divide-y divide-nba-gris-100">
        {razones.map((razon, indice) => (
          <ItemRazon key={`${razon.factor}-${indice}`} razon={razon} />
        ))}
      </ul>
    </Tarjeta>
  );
}
