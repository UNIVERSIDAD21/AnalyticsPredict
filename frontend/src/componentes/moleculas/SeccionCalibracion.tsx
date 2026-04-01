/**
 * SeccionCalibracion.tsx — Muestra la calibración de probabilidades
 *
 * Muestra la diferencia entre p_raw (probabilidad cruda del modelo)
 * y p_calibrada (probabilidad ajustada por el calibrador).
 * Si no hay calibrador, muestra advertencia informativa.
 */

import { Activity, AlertTriangle, HelpCircle, ArrowRight, Lock, Crown } from 'lucide-react';
import { useAccessPolicy } from '../../contextos/AccessPolicyContext';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface PropsSeccionCalibracion {
  /** Probabilidad cruda del modelo */
  pRaw: number | null;

  /** Probabilidad calibrada */
  pCalibrada: number | null;

  /** Nombre del calibrador usado */
  calibradorUsado: string | null;
}

// ══════════════════════════════════════════════════════════════
// HELPERS
// ══════════════════════════════════════════════════════════════

function formatearProbabilidad(valor: number | null): string {
  if (valor === null || !isFinite(valor)) return '—';
  return `${(valor * 100).toFixed(2)}%`;
}

function calcularDelta(pRaw: number | null, pCalibrada: number | null): string {
  if (pRaw === null || pCalibrada === null || !isFinite(pRaw) || !isFinite(pCalibrada)) {
    return '—';
  }
  const delta = (pCalibrada - pRaw) * 100;
  const signo = delta >= 0 ? '+' : '';
  return `${signo}${delta.toFixed(2)} pts`;
}

function obtenerNombreCalibrador(calibrador: string | null): string {
  if (!calibrador) return 'Auto';
  const nombres: Record<string, string> = {
    platt: 'Platt Scaling',
    isotonic: 'Isotonic Regression',
    temperature: 'Temperature Scaling',
    none: 'Sin calibrador',
  };
  return nombres[calibrador.toLowerCase()] || calibrador;
}

function construirExplicacionProfesional(
  pRaw: number | null,
  pCalibrada: number | null,
  calibradorUsado: string | null
): { resumen: string; tecnico: string; lecturaRiesgo: string } {
  if (pRaw === null || pCalibrada === null || !isFinite(pRaw) || !isFinite(pCalibrada)) {
    return {
      resumen: 'No hay suficientes datos para justificar técnicamente un ajuste de calibración en este evento.',
      tecnico: 'Sin probabilidad calibrada válida no se puede calcular gap de calibración ni evaluar sesgo histórico del modelo.',
      lecturaRiesgo: 'Operativamente se debe interpretar con cautela: usar probabilidad raw implica mayor incertidumbre de confiabilidad.',
    };
  }

  const deltaPts = (pCalibrada - pRaw) * 100;
  const absDelta = Math.abs(deltaPts);
  const direccion = deltaPts < 0 ? 'a la baja' : deltaPts > 0 ? 'al alza' : 'sin cambio';
  const metodo = obtenerNombreCalibrador(calibradorUsado);

  const severidad = absDelta >= 4
    ? 'ajuste fuerte'
    : absDelta >= 2
      ? 'ajuste moderado'
      : 'ajuste fino';

  return {
    resumen: `El calibrador aplicó un ${severidad} (${direccion}) de ${absDelta.toFixed(2)} pts sobre la probabilidad del modelo para alinear la confianza con evidencia histórica comparable.`,
    tecnico: `Método activo: ${metodo}. Se transformó P(raw)=${(pRaw * 100).toFixed(2)}% a P(calibrada)=${(pCalibrada * 100).toFixed(2)}%. Este ajuste corrige sesgo de sobre/sub-confianza observado en validación histórica del mercado.`,
    lecturaRiesgo: `Para decisión operativa, la referencia correcta es la probabilidad calibrada. Un ajuste ${direccion} indica que la certeza inicial del modelo era más optimista/pesimista que el comportamiento real histórico.`,
  };
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE
// ══════════════════════════════════════════════════════════════

/**
 * Muestra la calibración de probabilidades: p_raw vs p_calibrada
 */
export function SeccionCalibracion({
  pRaw,
  pCalibrada,
  calibradorUsado,
}: PropsSeccionCalibracion) {
  const { can } = useAccessPolicy();
  const tienePremium = can('premium.depth');
  const tieneCalibrador =
    pCalibrada !== null &&
    (calibradorUsado === null || calibradorUsado.toLowerCase() !== 'none');
  const delta = calcularDelta(pRaw, pCalibrada);
  const explicacion = construirExplicacionProfesional(pRaw, pCalibrada, calibradorUsado);

  const bloqueExplicacion = (
    <div className="mt-4 pt-4 border-t border-neon-cyan/10">
      <div className="flex items-center gap-2 mb-3">
        <Crown className="w-4 h-4 text-neon-magenta" />
        <span className="text-xs font-bold uppercase tracking-wider text-neon-magenta">
          Explicación Técnica del Ajuste
        </span>
      </div>

      {tienePremium ? (
        <div className="space-y-2 text-xs text-texto-secundario leading-relaxed">
          <p>{explicacion.resumen}</p>
          <p>{explicacion.tecnico}</p>
          <p>{explicacion.lecturaRiesgo}</p>
        </div>
      ) : (
        <div className="relative rounded-lg border border-neon-magenta/30 bg-neon-magenta/5 p-3 overflow-hidden">
          <div className="space-y-2 text-xs text-texto-secundario/60 blur-[2px] select-none pointer-events-none">
            <p>{explicacion.resumen}</p>
            <p>{explicacion.tecnico}</p>
            <p>{explicacion.lecturaRiesgo}</p>
          </div>
          <div className="absolute inset-0 bg-futurista-oscuro/40 flex items-center justify-center">
            <div className="px-3 py-2 rounded-lg border border-neon-magenta/40 bg-futurista-oscuro/90 flex items-center gap-2">
              <Lock className="w-4 h-4 text-neon-magenta" />
              <span className="text-xs font-semibold text-neon-magenta">
                Explicación premium bloqueada en plan base
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  // Sin calibrador activo
  if (!tieneCalibrador) {
    return (
      <div className="p-4 rounded-lg bg-neon-amarillo/5 border border-neon-amarillo/20">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-lg bg-neon-amarillo/10 flex items-center justify-center flex-shrink-0 border border-neon-amarillo/30">
            <AlertTriangle className="w-4 h-4 text-neon-amarillo" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-bold uppercase tracking-wider text-neon-amarillo">
                Sin Calibración
              </span>
              <div className="group relative">
                <HelpCircle size={12} className="text-texto-terciario cursor-help" />
                <div className="absolute bottom-full left-0 mb-2 w-56 p-2 rounded-lg bg-futurista-oscuro border border-neon-cyan/20 text-[10px] text-texto-secundario opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
                  La calibración ajusta las probabilidades del modelo para que reflejen mejor la realidad histórica.
                </div>
              </div>
            </div>
            <p className="text-xs text-texto-secundario">
              Se usa la probabilidad raw del modelo ({formatearProbabilidad(pRaw)}).
              Sin calibración, las probabilidades pueden estar sobre/sub-estimadas.
            </p>
          </div>
        </div>

        {bloqueExplicacion}
      </div>
    );
  }

  // Con calibrador activo
  return (
    <div className="p-4 rounded-lg bg-neon-cyan/5 border border-neon-cyan/20">
      <div className="flex items-center gap-2 mb-3">
        <Activity size={14} className="text-neon-cyan" />
        <span className="text-xs font-bold uppercase tracking-wider text-neon-cyan">
          Calibración Aplicada
        </span>
        <div className="group relative ml-auto">
          <HelpCircle size={12} className="text-texto-terciario cursor-help" />
          <div className="absolute bottom-full right-0 mb-2 w-56 p-2 rounded-lg bg-futurista-oscuro border border-neon-cyan/20 text-[10px] text-texto-secundario opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10">
            <strong className="text-neon-cyan">Calibración</strong> ajusta las probabilidades del modelo basándose en resultados históricos para mejorar la precisión.
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between gap-4">
        {/* P Raw */}
        <div className="text-center flex-1">
          <div className="text-[10px] uppercase tracking-wider text-texto-terciario mb-1">
            P. Raw
          </div>
          <div className="text-xl font-mono font-bold text-texto-principal">
            {formatearProbabilidad(pRaw)}
          </div>
          <div className="text-[10px] text-texto-terciario">
            Del modelo
          </div>
        </div>

        {/* Flecha y delta */}
        <div className="flex flex-col items-center">
          <ArrowRight size={20} className="text-neon-cyan" />
          <div className={`text-sm font-mono font-bold mt-1 ${
            pCalibrada !== null && pRaw !== null && pCalibrada > pRaw
              ? 'text-neon-verde'
              : pCalibrada !== null && pRaw !== null && pCalibrada < pRaw
                ? 'text-neon-rojo'
                : 'text-texto-secundario'
          }`}>
            {delta}
          </div>
        </div>

        {/* P Calibrada */}
        <div className="text-center flex-1">
          <div className="text-[10px] uppercase tracking-wider text-texto-terciario mb-1">
            P. Calibrada
          </div>
          <div className="text-xl font-mono font-bold text-neon-verde texto-glow-verde">
            {formatearProbabilidad(pCalibrada)}
          </div>
          <div className="text-[10px] text-texto-terciario">
            Ajustada
          </div>
        </div>
      </div>

      {/* Calibrador usado */}
      <div className="mt-3 pt-3 border-t border-neon-cyan/10 flex items-center justify-between">
        <span className="text-[10px] text-texto-terciario">
          Calibrador:
        </span>
        <span className="text-xs font-mono text-neon-cyan">
          {obtenerNombreCalibrador(calibradorUsado)}
        </span>
      </div>

      {bloqueExplicacion}
    </div>
  );
}
