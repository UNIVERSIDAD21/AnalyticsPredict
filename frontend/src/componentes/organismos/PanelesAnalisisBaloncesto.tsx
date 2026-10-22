import type { ReactNode } from 'react';
import { Activity, TrendingUp, Target, BarChart3 } from 'lucide-react';

export function EstadoVacio() {
  return (
    <div className="h-full flex flex-col items-center justify-center text-center p-8">
      {/* Icono animado */}
      <div className="relative mb-8">
        <div className="absolute inset-0 bg-neon-cyan/10 blur-3xl rounded-full animate-pulse" />
        <div className="relative w-32 h-32 rounded-2xl border border-neon-cyan/20 bg-futurista-oscuro/50 flex items-center justify-center">
          <BarChart3 className="w-16 h-16 text-neon-cyan/50" />
        </div>
      </div>

      {/* Texto */}
      <h3 className="text-2xl font-futurista text-texto-principal mb-3 tracking-wider">
        ESPERANDO ANÁLISIS
      </h3>
      <p className="text-texto-secundario max-w-md mb-8">
        Configura los parámetros del partido en el panel izquierdo para obtener predicciones
        basadas en análisis estadístico avanzado.
      </p>

      {/* Características */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 w-full max-w-2xl">
        <div className="p-4 rounded-lg border border-neon-cyan/10 bg-futurista-oscuro/30">
          <Activity className="w-6 h-6 text-neon-cyan mb-2 mx-auto" />
          <p className="text-xs text-texto-secundario uppercase tracking-wider">
            Análisis por Cuarto
          </p>
        </div>
        <div className="p-4 rounded-lg border border-neon-verde/10 bg-futurista-oscuro/30">
          <TrendingUp className="w-6 h-6 text-neon-verde mb-2 mx-auto" />
          <p className="text-xs text-texto-secundario uppercase tracking-wider">
            Probabilidades Over/Under
          </p>
        </div>
        <div className="p-4 rounded-lg border border-neon-magenta/10 bg-futurista-oscuro/30">
          <Target className="w-6 h-6 text-neon-magenta mb-2 mx-auto" />
          <p className="text-xs text-texto-secundario uppercase tracking-wider">
            Contexto e historial
          </p>
        </div>
      </div>

      {/* Línea decorativa */}
      <div className="mt-8 w-48 h-[1px] bg-gradient-to-r from-transparent via-neon-cyan/30 to-transparent" />
    </div>
  );
}


/** Layout del analizador original NBA compartido por ambas ligas. */
export function PanelesAnalisisBaloncesto({ formulario, children }: { formulario: ReactNode; children: ReactNode }) {
  return <div className="flex flex-col lg:flex-row gap-6 lg:gap-8 min-h-[calc(100vh-200px)]">
    <div className="w-full lg:w-[400px] xl:w-[450px] flex-shrink-0 min-w-0">
      <div className="lg:sticky lg:top-6">{formulario}</div>
    </div>
    <div className="flex-1 min-w-0" id="resultado-analisis">{children}</div>
  </div>;
}
