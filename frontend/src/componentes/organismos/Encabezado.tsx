/**
 * Encabezado.tsx — Header de la aplicación
 */

import { Activity } from 'lucide-react';

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Encabezado principal de la aplicación
 */
export function Encabezado() {
  return (
    <header className="bg-nba-azul text-white shadow-lg">
      <div className="contenedor py-6">
        <div className="flex items-center gap-3">
          {/* Logo */}
          <div className="w-12 h-12 bg-white/10 rounded-xl flex items-center justify-center">
            <Activity size={28} />
          </div>

          {/* Título */}
          <div>
            <h1 className="text-2xl font-bold">
              Analizador NBA
            </h1>
            <p className="text-white/70 text-sm">
              Análisis de apuestas por cuarto y juego completo
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
