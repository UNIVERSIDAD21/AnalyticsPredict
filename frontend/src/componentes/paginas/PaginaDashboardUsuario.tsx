import { useEffect, useMemo, useState } from 'react';
import { BarChart3, CheckCircle2, CircleDollarSign, RefreshCw } from 'lucide-react';
import { Encabezado } from '../organismos';
import { Boton, Spinner } from '../atomos';
import { useAuth } from '../../contextos/AuthContext';
import { obtenerEstadoOnboarding, obtenerResumenDashboard, type ResumenDashboard } from '../../servicios/onboarding';
import { obtenerEstadoPlan, type EstadoPlanUsuario } from '../../servicios/pagos';

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

const resumenInicial: ResumenDashboard = {
  apuestasTotales: 0,
  apuestasResueltas: 0,
  ganadas: 0,
  perdidas: 0,
  push: 0,
  winRate: 0,
};

const planInicial: EstadoPlanUsuario = {
  activo: false,
  planId: null,
  estado: null,
  actualizadoEn: null,
};

export function PaginaDashboardUsuario() {
  const { usuario } = useAuth();
  const [cargando, setCargando] = useState(true);
  const [resumen, setResumen] = useState<ResumenDashboard>(resumenInicial);
  const [plan, setPlan] = useState<EstadoPlanUsuario>(planInicial);
  const [error, setError] = useState<string | null>(null);

  const estadoOnboarding = useMemo(() => {
    if (!usuario?.id) return null;
    return obtenerEstadoOnboarding(String(usuario.id));
  }, [usuario?.id]);

  const recargar = async () => {
    try {
      setError(null);
      setCargando(true);
      const [resumenData, planData] = await Promise.all([
        obtenerResumenDashboard(),
        obtenerEstadoPlan(),
      ]);
      setResumen(resumenData);
      setPlan(planData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el dashboard.');
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    void recargar();
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-2xl font-futurista text-texto-principal">Dashboard de usuario</h2>
            <p className="text-sm text-texto-secundario">
              Vista rápida de onboarding, desempeño reciente y estado de plan.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Boton variante="secundario" iconoInicio={<RefreshCw size={16} />} onClick={() => void recargar()}>
              Recargar
            </Boton>
            <Boton variante="primario" onClick={() => navegar('/')}>
              Ir al análisis
            </Boton>
          </div>
        </div>

        {cargando && (
          <div className="tarjeta min-h-[240px] flex items-center justify-center">
            <Spinner tamano="lg" texto="Cargando dashboard..." centrado />
          </div>
        )}

        {!cargando && error && (
          <div className="tarjeta p-4 border border-neon-rojo/40 text-neon-rojo">
            {error}
          </div>
        )}

        {!cargando && !error && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="tarjeta p-5 space-y-2">
                <div className="flex items-center gap-2 text-neon-cyan">
                  <CheckCircle2 className="w-4 h-4" />
                  <p className="text-xs uppercase tracking-widest">Onboarding</p>
                </div>
                <p className="text-xl font-semibold text-texto-principal">
                  {estadoOnboarding?.completado ? 'Completado' : 'Pendiente'}
                </p>
                <p className="text-xs text-texto-secundario">
                  {estadoOnboarding?.perfil?.nombre
                    ? `Perfil: ${estadoOnboarding.perfil.nombre}`
                    : 'Aún no hay perfil personalizado.'}
                </p>
              </div>

              <div className="tarjeta p-5 space-y-2">
                <div className="flex items-center gap-2 text-neon-verde">
                  <CircleDollarSign className="w-4 h-4" />
                  <p className="text-xs uppercase tracking-widest">Plan</p>
                </div>
                <p className="text-xl font-semibold text-texto-principal">
                  {plan.activo ? 'Activo' : 'Sin suscripción activa'}
                </p>
                <p className="text-xs text-texto-secundario">
                  {plan.planId ? `Plan ${plan.planId}` : 'Actualmente en modo base.'}
                </p>
              </div>

              <div className="tarjeta p-5 space-y-2">
                <div className="flex items-center gap-2 text-neon-magenta">
                  <BarChart3 className="w-4 h-4" />
                  <p className="text-xs uppercase tracking-widest">Win Rate</p>
                </div>
                <p className="text-xl font-semibold text-texto-principal">{resumen.winRate.toFixed(1)}%</p>
                <p className="text-xs text-texto-secundario">{resumen.apuestasResueltas} apuestas resueltas</p>
              </div>
            </div>

            <div className="tarjeta p-6">
              <h3 className="text-lg font-semibold text-texto-principal mb-4">Rendimiento reciente</h3>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-center">
                <Kpi label="Totales" valor={resumen.apuestasTotales} />
                <Kpi label="Resueltas" valor={resumen.apuestasResueltas} />
                <Kpi label="Ganadas" valor={resumen.ganadas} />
                <Kpi label="Perdidas" valor={resumen.perdidas} />
                <Kpi label="Push" valor={resumen.push} />
              </div>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function Kpi({ label, valor }: { label: string; valor: number }) {
  return (
    <div className="rounded-lg border border-neon-cyan/20 bg-futurista-oscuro/40 p-3">
      <p className="text-xs uppercase tracking-wider text-texto-terciario">{label}</p>
      <p className="text-2xl font-semibold text-texto-principal mt-1">{valor}</p>
    </div>
  );
}
