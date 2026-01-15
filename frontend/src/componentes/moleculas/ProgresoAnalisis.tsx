/**
 * ProgresoAnalisis.tsx — Indicador por pasos del análisis en curso
 */

import { useEffect, useState } from 'react';
import { CheckCircle, Loader2, CircleDot } from 'lucide-react';

const PASOS = [
  'Validando entrada',
  'Ejecutando motor predictivo',
  'Calculando de-vig',
  'Calculando score y sizing',
  'Generando resultado',
];

export function ProgresoAnalisis() {
  const [pasoActual, setPasoActual] = useState(0);
  const [progreso, setProgreso] = useState(10);
  const [tardando, setTardando] = useState(false);

  useEffect(() => {
    setPasoActual(0);
    setProgreso(10);
    setTardando(false);

    const intervaloPasos = window.setInterval(() => {
      setPasoActual((prev) => (prev < PASOS.length - 1 ? prev + 1 : prev));
    }, 1600);

    const intervaloProgreso = window.setInterval(() => {
      setProgreso((prev) => (prev < 95 ? prev + 3 : prev));
    }, 350);

    const timeout = window.setTimeout(() => {
      setTardando(true);
    }, 10000);

    return () => {
      window.clearInterval(intervaloPasos);
      window.clearInterval(intervaloProgreso);
      window.clearTimeout(timeout);
    };
  }, []);

  return (
    <div className="tarjeta h-full min-h-[420px] flex flex-col justify-center px-6 py-8">
      <div className="text-center mb-6">
        <div className="relative inline-block mb-4">
          <div className="absolute inset-0 bg-neon-cyan/20 blur-xl rounded-full animate-pulse" />
          <Loader2 className="w-12 h-12 text-neon-cyan animate-spin relative" />
        </div>
        <p className="text-texto-principal font-futurista tracking-wider text-lg">
          ANALIZANDO PARTIDO
        </p>
        <p className="text-texto-terciario text-sm mt-2 font-mono">
          Preparando resultados estadísticos
        </p>
      </div>

      <div className="space-y-3">
        {PASOS.map((paso, index) => {
          const completado = index < pasoActual;
          const activo = index === pasoActual;

          return (
            <div
              key={paso}
              className={`flex items-center gap-3 p-3 rounded-lg border ${
                activo
                  ? 'border-neon-cyan/40 bg-neon-cyan/10'
                  : completado
                    ? 'border-neon-verde/30 bg-neon-verde/5'
                    : 'border-white/5 bg-futurista-oscuro/40'
              }`}
            >
              {completado ? (
                <CheckCircle className="w-5 h-5 text-neon-verde" />
              ) : activo ? (
                <Loader2 className="w-5 h-5 text-neon-cyan animate-spin" />
              ) : (
                <CircleDot className="w-5 h-5 text-texto-terciario" />
              )}
              <span className={`text-sm ${activo ? 'text-neon-cyan' : completado ? 'text-neon-verde' : 'text-texto-terciario'}`}>
                {paso}
              </span>
            </div>
          );
        })}
      </div>

      <div className="mt-6">
        <div className="h-2 w-full rounded-full bg-white/10 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-neon-cyan via-neon-magenta to-neon-cyan transition-all"
            style={{ width: `${progreso}%` }}
          />
        </div>
        <p className="text-xs text-texto-terciario mt-2 font-mono">
          Progreso estimado: {progreso}%
        </p>
      </div>

      {tardando && (
        <div className="mt-4 rounded-lg border border-advertencia-500/40 bg-advertencia-500/10 px-4 py-3">
          <p className="text-sm text-advertencia-500">
            Está tardando más de lo habitual. Revisa tu conexión o reintenta el análisis.
          </p>
        </div>
      )}
    </div>
  );
}
