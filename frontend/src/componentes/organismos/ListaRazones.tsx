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
// COMPONENTE INTERNO
// ══════════════════════════════════════════════════════════════

function ItemRazon({ razon }: { razon: RazonPrediccion }) {
  const esSube = razon.direccion === 'sube';
  const Icono = esSube ? ArrowUp : ArrowDown;

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
