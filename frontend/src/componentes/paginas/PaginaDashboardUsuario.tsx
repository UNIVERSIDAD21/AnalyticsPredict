import { useEffect, useMemo, useState } from 'react';
import { BarChart3, CheckCircle2, CircleDollarSign, RefreshCw, Radar, Crown } from 'lucide-react';
import { Encabezado } from '../organismos';
import { Boton, Spinner } from '../atomos';
import { useAuth } from '../../contextos/AuthContext';
import {
  obtenerEstadoOnboarding,
  obtenerResumenDashboard,
  obtenerKpisOnboarding,
  registrarEventoOnboarding,
  type ResumenDashboard,
  type KpisOnboarding,
} from '../../servicios/onboarding';
import { obtenerEstadoPlan, type EstadoPlanUsuario } from '../../servicios/pagos';
import { obtenerResumenCalidad1x2, type ResumenCalidad1x2Futbol } from '../../servicios/futbol/metricas';

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

const kpisIniciales: KpisOnboarding = {
  startedUsers: 0,
  completedUsers: 0,
  completionRatePct: 0,
  timeToValueMinutesAvg: null,
  ttvSampleSize: 0,
};

const calidadInicial: ResumenCalidad1x2Futbol = {
  total: 0,
  finalizadas: 0,
  ganadas: 0,
  perdidas: 0,
  push: 0,
  hitRateSinPush: 0,
};

export function PaginaDashboardUsuario() {
  const { usuario } = useAuth();
  const [cargando, setCargando] = useState(true);
  const [resumen, setResumen] = useState<ResumenDashboard>(resumenInicial);
  const [plan, setPlan] = useState<EstadoPlanUsuario>(planInicial);
  const [kpisOnboarding, setKpisOnboarding] = useState<KpisOnboarding>(kpisIniciales);
  const [calidad1x2, setCalidad1x2] = useState<ResumenCalidad1x2Futbol>(calidadInicial);
  const [error, setError] = useState<string | null>(null);

  const estadoOnboarding = useMemo(() => {
    if (!usuario?.id) return null;
    return obtenerEstadoOnboarding(String(usuario.id));
  }, [usuario?.id]);

  const recargar = async () => {
    try {
      setError(null);
      setCargando(true);
      const [resumenData, planData, kpisData, calidadData] = await Promise.all([
        obtenerResumenDashboard(),
        obtenerEstadoPlan(),
        obtenerKpisOnboarding(),
        obtenerResumenCalidad1x2(),
      ]);
      setResumen(resumenData);
      setPlan(planData);
      setKpisOnboarding(kpisData);
      setCalidad1x2(calidadData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo cargar el dashboard.');
    } finally {
      setCargando(false);
    }
  };

  useEffect(() => {
    void recargar();
    void registrarEventoOnboarding('dashboard_viewed');
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
            <Boton variante="primario" onClick={() => navegar('/app')}>
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

            <div className="tarjeta p-6">
              <h3 className="text-lg font-semibold text-texto-principal mb-4">KPIs de activación (reales)</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="rounded-lg border border-neon-cyan/20 bg-futurista-oscuro/40 p-4">
                  <p className="text-xs uppercase tracking-wider text-texto-terciario">Completion rate</p>
                  <p className="text-3xl font-semibold text-neon-cyan mt-1">{kpisOnboarding.completionRatePct.toFixed(1)}%</p>
                  <p className="text-xs text-texto-secundario mt-1">
                    {kpisOnboarding.completedUsers} completados de {kpisOnboarding.startedUsers} iniciados
                  </p>
                </div>

                <div className="rounded-lg border border-neon-verde/20 bg-futurista-oscuro/40 p-4">
                  <p className="text-xs uppercase tracking-wider text-texto-terciario">Time-to-value promedio</p>
                  <p className="text-3xl font-semibold text-neon-verde mt-1">
                    {kpisOnboarding.timeToValueMinutesAvg === null
                      ? 'N/D'
                      : `${kpisOnboarding.timeToValueMinutesAvg.toFixed(1)} min`}
                  </p>
                  <p className="text-xs text-texto-secundario mt-1">
                    muestra: {kpisOnboarding.ttvSampleSize} usuario(s)
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="tarjeta p-6 space-y-3 border border-neon-amarillo/30">
                <div className="flex items-center gap-2 text-neon-amarillo">
                  <Radar className="w-4 h-4" />
                  <h3 className="text-sm uppercase tracking-wider">Ruta fútbol sin maquillaje</h3>
                </div>
                <ul className="text-sm text-texto-secundario space-y-1">
                  <li>• Premier League y LaLiga: seguimiento estable.</li>
                  <li>• Serie A: validación de calibración en curso.</li>
                  <li>• Ligue 1: laboratorio, sin paridad comercial con NBA.</li>
                </ul>
                <p className="text-xs text-texto-terciario">
                  Regla vigente: fútbol gana peso por evidencia real, no por copy promocional.
                </p>
              </div>

              <div className="tarjeta p-6 space-y-3 border border-neon-cyan/30">
                <div className="flex items-center gap-2 text-neon-cyan">
                  <BarChart3 className="w-4 h-4" />
                  <h3 className="text-sm uppercase tracking-wider">Baseline técnico 1X2 (Ola 3)</h3>
                </div>
                <p className="text-sm text-texto-secundario">
                  Hit rate sin push: <span className="font-semibold text-texto-principal">{(calidad1x2.hitRateSinPush * 100).toFixed(1)}%</span>
                  {' '}sobre {calidad1x2.finalizadas} apuestas finalizadas.
                </p>
                <p className="text-xs text-texto-terciario">
                  Este baseline se usa como referencia para validar mejoras de modelo/motor antes de promover cambios.
                </p>
              </div>

              <div className="tarjeta p-6 space-y-3 border border-neon-magenta/30">
                <div className="flex items-center gap-2 text-neon-magenta">
                  <Crown className="w-4 h-4" />
                  <h3 className="text-sm uppercase tracking-wider">Evolución de plan</h3>
                </div>
                <p className="text-sm text-texto-secundario">
                  El plan premium se define como profundidad operativa: mejor seguimiento, más capas analíticas y continuidad de decisiones.
                </p>
                <div className="flex flex-wrap gap-2">
                  {!plan.activo ? (
                    <Boton variante="primario" onClick={() => navegar('/configuracion')}>
                      Ver opciones de suscripción
                    </Boton>
                  ) : (
                    <Boton variante="secundario" onClick={() => navegar('/configuracion')}>
                      Gestionar plan activo
                    </Boton>
                  )}
                </div>
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
