import { useEffect, useState } from 'react';
import { ArrowRight, ShieldCheck, Target, Activity, Crown, UserCheck, Eye } from 'lucide-react';
import { Link } from 'react-router-dom';
import { registrarVistaLanding, type MetricasVisitante } from '../../servicios/visitante';

export function PaginaPublicaProducto() {
  const [metricas, setMetricas] = useState<MetricasVisitante | null>(null);

  useEffect(() => {
    setMetricas(registrarVistaLanding());
  }, []);

  return (
    <div className="min-h-screen bg-futurista-negro text-texto-principal">
      <main className="contenedor py-10 lg:py-14 space-y-8">
        <section className="rounded-2xl border border-neon-cyan/20 bg-futurista-oscuro/50 p-6 lg:p-10">
          <p className="text-xs uppercase tracking-[0.2em] text-neon-cyan">AnalyticsPredict</p>
          <h1 className="text-3xl lg:text-5xl font-futurista mt-3">Análisis deportivo para disciplina operativa, no para humo comercial.</h1>
          <p className="text-texto-secundario mt-4 max-w-3xl">
            Te ayudamos a decidir con trazabilidad, control de riesgo y lectura de señales. Sin promesas de “ganar fácil” y con madurez visible por deporte.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/login" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-neon-cyan text-neon-cyan">
              Crear cuenta
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link to="/centro-analitico" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-neon-magenta/40 text-neon-magenta">
              Ver centro analítico (modo visitante)
            </Link>
          </div>
        </section>

        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="tarjeta p-5">
            <div className="flex items-center gap-2 text-neon-cyan"><ShieldCheck className="w-4 h-4" /> Credibilidad</div>
            <p className="text-sm text-texto-secundario mt-2">No se publicita fútbol como equivalente comercial de NBA mientras no cumpla su madurez operativa.</p>
          </div>
          <div className="tarjeta p-5">
            <div className="flex items-center gap-2 text-neon-verde"><Target className="w-4 h-4" /> Propuesta de valor</div>
            <p className="text-sm text-texto-secundario mt-2">Valor real: consistencia de ejecución, evidencia y trazabilidad de decisiones.</p>
          </div>
          <div className="tarjeta p-5">
            <div className="flex items-center gap-2 text-neon-magenta"><Activity className="w-4 h-4" /> Freemium serio</div>
            <p className="text-sm text-texto-secundario mt-2">Visitante puede explorar superficies públicas. Análisis operativo y guardado personal requieren cuenta.</p>
          </div>
        </section>

        <section className="tarjeta p-5 space-y-4 border border-neon-cyan/20">
          <div className="flex items-center gap-2 text-neon-cyan text-xs uppercase tracking-wider">
            <Eye className="w-4 h-4" /> Qué puedes hacer según tu nivel
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <div className="rounded-lg border border-neon-cyan/20 p-4 bg-futurista-oscuro/40">
              <p className="flex items-center gap-2 font-semibold text-texto-principal"><Eye className="w-4 h-4 text-neon-cyan" /> Visitante</p>
              <ul className="mt-2 text-texto-secundario space-y-1">
                <li>• Ver landing y centro analítico público</li>
                <li>• Revisar madurez por deporte</li>
                <li>• Sin bitácora ni configuración personal</li>
              </ul>
            </div>
            <div className="rounded-lg border border-neon-verde/20 p-4 bg-futurista-oscuro/40">
              <p className="flex items-center gap-2 font-semibold text-texto-principal"><UserCheck className="w-4 h-4 text-neon-verde" /> Registrado</p>
              <ul className="mt-2 text-texto-secundario space-y-1">
                <li>• Acceso a análisis operativo completo</li>
                <li>• Bitácora y continuidad personal</li>
                <li>• Onboarding y configuración base</li>
              </ul>
            </div>
            <div className="rounded-lg border border-neon-magenta/20 p-4 bg-futurista-oscuro/40">
              <p className="flex items-center gap-2 font-semibold text-texto-principal"><Crown className="w-4 h-4 text-neon-magenta" /> Premium</p>
              <ul className="mt-2 text-texto-secundario space-y-1">
                <li>• Mayor profundidad y seguimiento</li>
                <li>• Capas extendidas de lectura operativa</li>
                <li>• Prioridad de herramientas avanzadas</li>
              </ul>
            </div>
          </div>
        </section>

        <section className="rounded-xl border border-neon-cyan/20 bg-futurista-oscuro/30 p-4 text-xs text-texto-secundario">
          <p>
            Visitante ID: <code>{metricas?.visitorId ?? 'cargando...'}</code> · Vistas landing: <strong>{metricas?.vistasLanding ?? 0}</strong>
          </p>
        </section>
      </main>
    </div>
  );
}
