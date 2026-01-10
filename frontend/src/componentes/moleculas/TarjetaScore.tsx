/**
 * TarjetaScore.tsx — Muestra el score y la recomendación de la apuesta
 *
 * Explica por qué una apuesta es APTO o NO RECOMENDADO basándose en:
 * - Score total (composición de EV, edge, penalizaciones)
 * - Gates pasados (EV > 0, edge_real > 0, kelly_full > 0)
 * - Componentes individuales con indicadores visuales
 */

import { CheckCircle, XCircle, TrendingUp, AlertTriangle, Zap, Shield, HelpCircle } from 'lucide-react';
import { Tarjeta } from '../atomos';
import { ComponentesScore } from '../../tipos';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsTarjetaScore {
  /** Score total (-1000 si gates fallan) */
  scoreTotal: number | null;

  /** Componentes del score */
  componentes: ComponentesScore | null;

  /** Explicación legible del score */
  explicacion: string | null;

  /** Penalizaciones aplicadas */
  penalizaciones: string[];

  /** Valor esperado (para mostrar contexto) */
  valorEsperado: number | null;
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

/** Determina si los gates pasaron basándose en el score */
function gatesPasados(score: number | null): boolean {
  if (score === null) return false;
  return score > -1000;
}

/** Obtiene texto legible para una penalización */
function obtenerTextoPenalizacion(codigo: string): string {
  const mapeo: Record<string, string> = {
    'RIESGO_ALTO': 'Alta volatilidad detectada',
    'DEVIG_ESTIMADO': 'De-vig estimado (falta cuota)',
    'SIN_DEVIG': 'Sin de-vig aplicado',
  };
  return mapeo[codigo] || codigo;
}

/** Formatea un valor como porcentaje con signo */
function formatearPorcentaje(valor: number | null): string {
  if (valor === null || !isFinite(valor)) return '—';
  const pct = valor * 100;
  const signo = pct >= 0 ? '+' : '';
  return `${signo}${pct.toFixed(2)}%`;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra el score profesional de la apuesta con desglose de componentes.
 */
export function TarjetaScore({
  scoreTotal,
  componentes,
  explicacion,
  penalizaciones,
  valorEsperado,
}: PropsTarjetaScore) {
  const esApto = gatesPasados(scoreTotal);

  // Si no hay score, mostrar estado indeterminado
  if (scoreTotal === null) {
    return (
      <Tarjeta className="animate-deslizar-arriba">
        <div className="text-center py-6">
          <AlertTriangle className="w-12 h-12 mx-auto text-texto-terciario mb-3" />
          <p className="text-sm text-texto-secundario">
            Score no disponible
          </p>
          <p className="text-xs text-texto-terciario mt-1">
            Se requieren más datos para evaluar esta apuesta
          </p>
        </div>
      </Tarjeta>
    );
  }

  return (
    <Tarjeta className="animate-deslizar-arriba">
      {/* Encabezado: APTO / NO RECOMENDADO */}
      <div className={`-m-6 mb-5 p-4 rounded-t-xl border-b ${
        esApto
          ? 'bg-neon-verde/10 border-neon-verde/30'
          : 'bg-neon-rojo/10 border-neon-rojo/30'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
            esApto
              ? 'bg-neon-verde/20 border border-neon-verde/40'
              : 'bg-neon-rojo/20 border border-neon-rojo/40'
          }`}>
            {esApto ? (
              <CheckCircle className="w-6 h-6 text-neon-verde" />
            ) : (
              <XCircle className="w-6 h-6 text-neon-rojo" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h3 className={`text-lg font-futurista font-bold tracking-wider ${
              esApto ? 'text-neon-verde' : 'text-neon-rojo'
            }`}>
              {esApto ? 'APUESTA APTA' : 'NO RECOMENDADO'}
            </h3>
            <p className="text-xs text-texto-secundario mt-0.5">
              {esApto
                ? 'Cumple criterios de valor, edge positivo y sizing viable'
                : 'No cumple los gates mínimos (EV ≤ 0, edge ≤ 0 o Kelly ≤ 0)'
              }
            </p>
          </div>
          {/* Score prominente */}
          <div className="text-right">
            <div className="text-[10px] uppercase tracking-wider text-texto-terciario">
              Score
            </div>
            <div className={`text-2xl font-mono font-bold ${
              esApto ? 'text-neon-verde texto-glow-verde' : 'text-neon-rojo'
            }`}>
              {esApto ? scoreTotal.toFixed(1) : '—'}
            </div>
          </div>
        </div>
      </div>

      {/* Componentes del score (solo si hay datos) */}
      {componentes && (
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <Zap size={14} className="text-neon-cyan" />
            <span className="text-xs font-bold uppercase tracking-wider text-neon-cyan">
              Desglose del Score
            </span>
            <div className="group relative ml-auto">
              <HelpCircle size={14} className="text-texto-terciario cursor-help" />
              <div className="absolute bottom-full right-0 mb-2 w-64 p-3 rounded-lg bg-futurista-oscuro border border-neon-cyan/20 text-xs text-texto-secundario opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                El score combina valor esperado, edge real y penalizaciones para determinar la calidad de la apuesta.
              </div>
            </div>
          </div>

          <div className="space-y-2">
            {/* EV Component */}
            <div className="flex items-center justify-between p-2 rounded-lg bg-futurista-oscuro/30">
              <div className="flex items-center gap-2">
                <TrendingUp size={14} className="text-neon-cyan" />
                <span className="text-xs text-texto-secundario">Valor Esperado (EV)</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-texto-terciario">
                  {formatearPorcentaje(valorEsperado)}
                </span>
                <span className={`text-sm font-mono font-bold ${
                  componentes.ev >= 0 ? 'text-neon-verde' : 'text-neon-rojo'
                }`}>
                  {componentes.ev >= 0 ? '+' : ''}{componentes.ev.toFixed(1)}
                </span>
              </div>
            </div>

            {/* Edge Component */}
            <div className="flex items-center justify-between p-2 rounded-lg bg-futurista-oscuro/30">
              <div className="flex items-center gap-2">
                <TrendingUp size={14} className="text-neon-magenta" />
                <span className="text-xs text-texto-secundario">Edge Real</span>
              </div>
              <span className={`text-sm font-mono font-bold ${
                componentes.edge_real >= 0 ? 'text-neon-verde' : 'text-neon-rojo'
              }`}>
                {componentes.edge_real >= 0 ? '+' : ''}{componentes.edge_real.toFixed(1)}
              </span>
            </div>

            {/* Riesgo/Volatilidad */}
            <div className="flex items-center justify-between p-2 rounded-lg bg-futurista-oscuro/30">
              <div className="flex items-center gap-2">
                <Shield size={14} className="text-neon-amarillo" />
                <span className="text-xs text-texto-secundario">
                  Riesgo (σ = {componentes.riesgo_valor.toFixed(1)})
                </span>
              </div>
              <div className="flex items-center gap-2">
                {componentes.riesgo_normalizado > 1 && (
                  <span className="px-1.5 py-0.5 text-[9px] uppercase font-bold rounded bg-neon-amarillo/20 text-neon-amarillo border border-neon-amarillo/30">
                    Alto
                  </span>
                )}
                <span className={`text-sm font-mono font-bold ${
                  componentes.penalizacion_riesgo < 0 ? 'text-neon-rojo' : 'text-neon-verde'
                }`}>
                  {componentes.penalizacion_riesgo >= 0 ? '+' : ''}{componentes.penalizacion_riesgo.toFixed(1)}
                </span>
              </div>
            </div>

            {/* Penalización De-Vig */}
            {componentes.penalizacion_devig !== 0 && (
              <div className="flex items-center justify-between p-2 rounded-lg bg-futurista-oscuro/30">
                <div className="flex items-center gap-2">
                  <AlertTriangle size={14} className="text-neon-amarillo" />
                  <span className="text-xs text-texto-secundario">Penalización De-Vig</span>
                </div>
                <span className="text-sm font-mono font-bold text-neon-rojo">
                  {componentes.penalizacion_devig.toFixed(1)}
                </span>
              </div>
            )}
          </div>

          {/* Barra visual del score */}
          <div className="mt-4">
            <div className="flex justify-between text-[10px] text-texto-terciario mb-1">
              <span>0</span>
              <span>Score: {esApto ? scoreTotal.toFixed(1) : 'N/A'}</span>
              <span>20+</span>
            </div>
            <div className="h-2 rounded-full bg-futurista-oscuro overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  esApto ? 'bg-gradient-to-r from-neon-verde/70 to-neon-verde' : 'bg-neon-rojo/50'
                }`}
                style={{
                  width: esApto
                    ? `${Math.min(100, Math.max(5, (scoreTotal / 20) * 100))}%`
                    : '0%',
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Penalizaciones aplicadas */}
      {penalizaciones.length > 0 && (
        <div className="mb-4">
          <div className="text-xs font-bold uppercase tracking-wider text-texto-terciario mb-2">
            Penalizaciones Activas
          </div>
          <div className="flex flex-wrap gap-2">
            {penalizaciones.map((p, idx) => (
              <span
                key={idx}
                className="px-2 py-1 text-[10px] uppercase font-bold rounded-full bg-neon-amarillo/15 text-neon-amarillo border border-neon-amarillo/30"
              >
                {obtenerTextoPenalizacion(p)}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Explicación del score */}
      {explicacion && (
        <div className="pt-3 border-t border-neon-cyan/10">
          <p className="text-[10px] font-mono text-texto-terciario">
            {explicacion}
          </p>
        </div>
      )}
    </Tarjeta>
  );
}
