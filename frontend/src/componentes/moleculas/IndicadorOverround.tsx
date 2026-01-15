/**
 * IndicadorOverround.tsx — Indicador de overround (vig) en tiempo real
 *
 * Muestra el overround calculado a partir de ambas cuotas.
 * Reglas consistentes con backend:
 * - overround < 1.0  → "Posible arbitraje / anomalía"
 * - overround > 1.10 → "Vig alto, revisar cuotas"
 * - caso normal      → "OK"
 */

import { AlertTriangle, CheckCircle, AlertOctagon, Percent } from 'lucide-react';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsIndicadorOverround {
  /** Cuota Over como string */
  cuotaOver: string;
  /** Cuota Under como string */
  cuotaUnder: string;
}

type EstadoOverround = 'arbitraje' | 'normal' | 'vig_alto';

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

function calcularOverround(cuotaOver: number, cuotaUnder: number): number {
  const pOver = 1 / cuotaOver;
  const pUnder = 1 / cuotaUnder;
  return pOver + pUnder;
}

function obtenerEstado(overround: number): EstadoOverround {
  if (overround < 1.0) return 'arbitraje';
  if (overround > 1.10) return 'vig_alto';
  return 'normal';
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra el overround calculado a partir de ambas cuotas.
 * Solo se renderiza cuando ambas cuotas son válidas (> 1).
 */
export function IndicadorOverround({
  cuotaOver,
  cuotaUnder,
}: PropsIndicadorOverround) {
  // Parsear cuotas
  const over = parseFloat(cuotaOver);
  const under = parseFloat(cuotaUnder);

  // Si alguna cuota es inválida o <= 1, no mostrar nada
  if (
    isNaN(over) ||
    isNaN(under) ||
    !isFinite(over) ||
    !isFinite(under) ||
    over <= 1 ||
    under <= 1
  ) {
    return null;
  }

  // Calcular overround y vig
  const overround = calcularOverround(over, under);
  const vigPorcentaje = (overround - 1) * 100;
  const estado = obtenerEstado(overround);

  // Configuración visual según estado
  const config = {
    arbitraje: {
      icono: AlertOctagon,
      colorFondo: 'bg-neon-magenta/10',
      colorBorde: 'border-neon-magenta/30',
      colorTexto: 'text-neon-magenta',
      colorIcono: 'text-neon-magenta',
      mensaje: 'Posible arbitraje / anomalía',
      descripcion: 'Overround < 100% indica oportunidad de arbitraje o error en cuotas',
    },
    normal: {
      icono: CheckCircle,
      colorFondo: 'bg-neon-verde/10',
      colorBorde: 'border-neon-verde/30',
      colorTexto: 'text-neon-verde',
      colorIcono: 'text-neon-verde',
      mensaje: 'Mercado OK',
      descripcion: 'Overround dentro de rangos normales',
    },
    vig_alto: {
      icono: AlertTriangle,
      colorFondo: 'bg-neon-amarillo/10',
      colorBorde: 'border-neon-amarillo/30',
      colorTexto: 'text-neon-amarillo',
      colorIcono: 'text-neon-amarillo',
      mensaje: 'Vig alto, revisar cuotas',
      descripcion: 'Overround > 110% indica margen excesivo de la casa',
    },
  };

  const { icono: Icono, colorFondo, colorBorde, colorTexto, colorIcono, mensaje, descripcion } =
    config[estado];

  return (
    <div
      className={`p-3 rounded-lg ${colorFondo} border ${colorBorde} transition-all duration-300`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`w-8 h-8 rounded-lg ${colorFondo} flex items-center justify-center flex-shrink-0`}
        >
          <Icono className={`w-5 h-5 ${colorIcono}`} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-1">
            <span className={`text-xs font-bold uppercase tracking-wider ${colorTexto}`}>
              {mensaje}
            </span>
            <div className="flex items-center gap-1">
              <Percent className={`w-3 h-3 ${colorTexto}`} />
              <span className={`text-sm font-mono font-bold ${colorTexto}`}>
                {vigPorcentaje.toFixed(2)}%
              </span>
            </div>
          </div>

          <div className="flex items-center justify-between gap-2">
            <p className="text-xs text-texto-secundario">{descripcion}</p>
            <span className="text-xs font-mono text-texto-terciario">
              OR: {overround.toFixed(4)}
            </span>
          </div>

          {/* Barra visual del overround */}
          <div className="mt-2 h-1.5 rounded-full bg-futurista-oscuro overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                estado === 'arbitraje'
                  ? 'bg-neon-magenta'
                  : estado === 'normal'
                    ? 'bg-neon-verde'
                    : 'bg-neon-amarillo'
              }`}
              style={{
                // Mapear overround a ancho: 0.9 = 0%, 1.0 = 50%, 1.2 = 100%
                width: `${Math.min(100, Math.max(0, ((overround - 0.9) / 0.3) * 100))}%`,
              }}
            />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[10px] text-texto-terciario">0.90</span>
            <span className="text-[10px] text-texto-terciario">1.00</span>
            <span className="text-[10px] text-texto-terciario">1.10</span>
            <span className="text-[10px] text-texto-terciario">1.20</span>
          </div>
        </div>
      </div>
    </div>
  );
}
