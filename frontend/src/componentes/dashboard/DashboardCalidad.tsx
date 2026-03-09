import { useEffect, useMemo, useState } from 'react';
import BadgeCalidad from '../explicabilidad/BadgeCalidad';
import BadgeLegacy from '../explicabilidad/BadgeLegacy';
import { EstadoSistema, obtenerEstadoSistema } from '../../servicios/estadoSistema';

interface Props {
  refreshMs?: number;
  mockData?: EstadoSistema;
}

function semaforo(nivel?: string) {
  if (nivel === 'A') return { txt: 'verde', cls: 'text-[#00ff88]' };
  if (nivel === 'B') return { txt: 'amarillo', cls: 'text-[#ffaa00]' };
  return { txt: 'rojo', cls: 'text-[#ff3333]' };
}

function faseRollout(flags: Record<string, boolean>): string {
  const sc = !!flags.FEATURE_CALIDAD_SCORECARD;
  const al = !!flags.FEATURE_ALERTAS_CALIDAD;
  const c = !!flags.FEATURE_CONTRATO_EXPLICACION_V1;
  const ui = !!flags.FEATURE_EXPLICABILIDAD_UI;
  if (!sc && !al && !c && !ui) return 'Pre-rollout';
  if (sc && !al && !c && !ui) return 'Fase 1A';
  if (sc && al && !c && !ui) return 'Fase 1B';
  if (sc && al && c && !ui) return 'Fase 2A';
  if (sc && al && c && ui) return 'Fase 2B/3';
  return 'Mixto';
}

function DebtPill({ label, value }: { label: string; value: string }) {
  const isBad = value !== 'RESUELTA';
  return (
    <div className={`rounded border px-3 py-2 text-xs ${isBad ? 'border-[#ff3333]/50 text-[#ff9fb6] bg-[#ff3333]/10' : 'border-[#00ff88]/40 text-[#00ff88] bg-[#00ff88]/10'}`}>
      <div className="font-semibold">{label}</div>
      <div>{value}</div>
    </div>
  );
}

export default function DashboardCalidad({ refreshMs = 60000, mockData }: Props) {
  const [data, setData] = useState<EstadoSistema | null>(mockData ?? null);
  const [loading, setLoading] = useState(!mockData);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (mockData) return;
    let alive = true;

    const cargar = async () => {
      try {
        setLoading(true);
        const estado = await obtenerEstadoSistema();
        if (alive) setData(estado);
      } catch (e) {
        if (alive) setError(e instanceof Error ? e.message : 'Error cargando estado');
      } finally {
        if (alive) setLoading(false);
      }
    };

    void cargar();
    const id = setInterval(() => {
      void cargar();
    }, refreshMs);

    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [refreshMs, mockData]);

  const fase = useMemo(() => faseRollout(data?.feature_flags ?? {}), [data?.feature_flags]);

  if (loading) return <div className="rounded-xl border border-cyan-400/30 bg-[#1a1f3a] p-4 text-slate-300">Cargando estado operativo...</div>;
  if (error) return <div className="rounded-xl border border-[#ff3333]/40 bg-[#1a1f3a] p-4 text-[#ff9fb6]">{error}</div>;
  if (!data) return <div className="rounded-xl border border-slate-700 bg-[#1a1f3a] p-4 text-slate-300">Sin datos de estado.</div>;

  const nba = data.scorecard_actual.NBA;
  const fut = data.scorecard_actual.FUTBOL;

  return (
    <section className="space-y-4 rounded-2xl border border-slate-700 bg-[#0a0e27] p-5 text-[#e0e6ed]">
      <h2 className="text-lg font-bold text-cyan-300">Dashboard Operativo de Calidad</h2>

      {/* 1. Estado de calidad por dominio */}
      <div className="grid gap-3 md:grid-cols-2">
        {[
          { dom: 'NBA', sc: nba },
          { dom: 'FUTBOL', sc: fut },
        ].map(({ dom, sc }) => {
          const nivel = (sc?.nivel ?? 'UNKNOWN') as 'A' | 'B' | 'C' | 'UNKNOWN';
          const sf = semaforo(sc?.nivel);
          return (
            <div key={dom} className="rounded-xl border border-cyan-500/20 bg-[#1a1f3a] p-4">
              <div className="mb-2 flex items-center justify-between">
                <h3 className="font-semibold">{dom}</h3>
                {nivel === 'A' || nivel === 'B' || nivel === 'C' ? <BadgeCalidad level={nivel} /> : <span className="text-xs text-slate-400">SIN SCORECARD</span>}
              </div>
              <p className="text-sm text-slate-300">Score: {sc?.score_final ?? 'N/A'}</p>
              <p className={`text-xs ${sf.cls}`}>Semáforo: {sf.txt}</p>
            </div>
          );
        })}
      </div>

      {/* 2. Alertas activas */}
      <div className="rounded-xl border border-[#ffaa00]/30 bg-[#1a1f3a] p-4">
        <h3 className="mb-2 font-semibold text-[#ffaa00]">Alertas activas</h3>
        <div className="grid gap-2 md:grid-cols-3 text-sm">
          <div>CRÍTICAS NBA: {data.alertas_criticas_activas.NBA}</div>
          <div>CRÍTICAS FUTBOL: {data.alertas_criticas_activas.FUTBOL}</div>
          <div>Total críticas: {data.alertas_criticas_activas.NBA + data.alertas_criticas_activas.FUTBOL}</div>
        </div>
        <p className="mt-2 text-xs text-slate-400">Últimas críticas (top 3): consultar panel de alertas detallado (incident_key/timestamp).</p>
      </div>

      {/* 3. Feature flags */}
      <div className="rounded-xl border border-fuchsia-500/30 bg-[#1a1f3a] p-4">
        <h3 className="mb-2 font-semibold text-fuchsia-300">Feature Flags</h3>
        <div className="grid gap-2 md:grid-cols-2 text-sm">
          {Object.entries(data.feature_flags).map(([k, v]) => (
            <div key={k} className="flex items-center justify-between rounded border border-slate-700 px-2 py-1">
              <span title="Estado real desde /api/calidad/estado-sistema">{k}</span>
              <span className={v ? 'text-[#00ff88]' : 'text-[#ff3333]'}>{v ? 'ON' : 'OFF'}</span>
            </div>
          ))}
        </div>
        <p className="mt-2 text-xs text-slate-400">Fase activa: {fase}</p>
      </div>

      {/* 4. Deuda residual B05 (siempre visible) */}
      <div className="rounded-xl border border-[#ff3333]/40 bg-[#1a1f3a] p-4">
        <h3 className="mb-2 font-semibold text-[#ff9fb6]">Deuda Residual B05 (siempre visible)</h3>
        <div className="grid gap-2 md:grid-cols-3">
          <DebtPill label="confidence_parcial" value={String(data.deuda_residual_b05.confidence_parcial)} />
          <DebtPill label="contratos_legacy" value={String(data.deuda_residual_b05.contratos_legacy_coexistentes)} />
          <DebtPill label="drift_futbol" value={String(data.deuda_residual_b05.drift_futbol_parcial_alto)} />
        </div>
      </div>

      {/* 5. Contrato explicación */}
      <div className="rounded-xl border border-cyan-500/30 bg-[#1a1f3a] p-4">
        <h3 className="mb-2 font-semibold text-cyan-300">Contrato de explicación</h3>
        <div className="flex items-center gap-2 text-sm">
          <span>Versión activa: {data.version_contrato}</span>
          <BadgeLegacy isLegacy={data.version_contrato === 'legacy'} />
        </div>
        <p className="mt-2 text-xs text-slate-400">Uso v1/legacy: visible cuando telemetría de contrato se agregue al endpoint.</p>
      </div>
    </section>
  );
}

// Demo rápido para 3 escenarios (verde/degradado/crítico)
export const mockEstadoVerde: EstadoSistema = {
  exito: true,
  feature_flags: {
    FEATURE_CALIDAD_SCORECARD: true,
    FEATURE_ALERTAS_CALIDAD: true,
    FEATURE_CONTRATO_EXPLICACION_V1: true,
    FEATURE_EXPLICABILIDAD_UI: true,
  },
  scorecard_actual: {
    NBA: { score_final: 93, nivel: 'A' },
    FUTBOL: { score_final: 88, nivel: 'B' },
  },
  alertas_criticas_activas: { NBA: 0, FUTBOL: 0 },
  version_contrato: '1.0.0',
  deuda_residual_b05: {
    confidence_parcial: 'EN_PROCESO',
    contratos_legacy_coexistentes: 'EN_MIGRACION',
    drift_futbol_parcial_alto: 'ACTIVO',
  },
};

export const mockEstadoDegradado: EstadoSistema = {
  ...mockEstadoVerde,
  scorecard_actual: {
    NBA: { score_final: 78, nivel: 'B' },
    FUTBOL: { score_final: 69, nivel: 'C' },
  },
  alertas_criticas_activas: { NBA: 0, FUTBOL: 1 },
};

export const mockEstadoCritico: EstadoSistema = {
  ...mockEstadoVerde,
  scorecard_actual: {
    NBA: { score_final: 62, nivel: 'C' },
    FUTBOL: { score_final: 55, nivel: 'C' },
  },
  alertas_criticas_activas: { NBA: 1, FUTBOL: 2 },
  version_contrato: 'legacy',
};
