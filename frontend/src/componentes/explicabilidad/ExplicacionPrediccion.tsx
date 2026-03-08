import { useEffect, useMemo, useState } from 'react';
import { ContratoExplicacion } from '../../tipos/explicabilidad';
import { obtenerExplicacion } from '../../servicios/explicabilidad';
import BadgeCalidad from './BadgeCalidad';
import PanelConfianza from './PanelConfianza';
import ListaFactores from './ListaFactores';
import PanelWarnings from './PanelWarnings';
import DisclaimerCalidad from './DisclaimerCalidad';
import BadgeLegacy from './BadgeLegacy';

interface Props {
  predictionId: string;
  fallbackData?: ContratoExplicacion;
}

export default function ExplicacionPrediccion({ predictionId, fallbackData }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<ContratoExplicacion | null>(fallbackData ?? null);

  useEffect(() => {
    let mounted = true;
    const cargar = async () => {
      setLoading(true);
      setError(null);
      try {
        const resp = await obtenerExplicacion(predictionId);
        if (!mounted) return;
        if (resp) setData(resp);
      } catch (e) {
        if (!mounted) return;
        setError(e instanceof Error ? e.message : 'No se pudo cargar la explicación');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    if (!fallbackData) {
      void cargar();
    }

    return () => {
      mounted = false;
    };
  }, [predictionId, fallbackData]);

  const debtFlags = useMemo(() => data?.metadata?.debt_flags ?? [], [data]);

  if (loading) {
    return <div className="rounded-xl border border-cyan-500/30 bg-[#1a1f3a] p-4 text-slate-300">Cargando explicabilidad...</div>;
  }

  if (error) {
    return (
      <div className="rounded-xl border border-[#ff3333]/40 bg-[#1a1f3a] p-4 text-[#ff9fb6]">
        {error}
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-xl border border-slate-600 bg-[#1a1f3a] p-4 text-slate-300">
        Explicabilidad deshabilitada por feature flag o no disponible.
      </div>
    );
  }

  return (
    <article className="space-y-4 rounded-2xl border border-slate-700 bg-[#0a0e27] p-5 text-[#e0e6ed]">
      <header className="flex flex-wrap items-center gap-2">
        <BadgeCalidad level={data.data_quality.level} />
        <BadgeLegacy isLegacy={data.metadata.is_legacy_contract} />
      </header>

      <section className="rounded-xl border border-slate-700 bg-[#1a1f3a] p-4">
        <p className="text-xs text-slate-400">Predicción</p>
        <p className="text-2xl font-bold text-cyan-300">
          {data.prediction.value} {data.prediction.unit}
        </p>
        <p className="text-sm text-slate-300">
          Recomendación: <strong className="uppercase">{data.prediction.recommendation}</strong> {data.prediction.line}
        </p>
      </section>

      <PanelConfianza confidence={data.prediction.confidence} qualityLevel={data.data_quality.level} />

      <ListaFactores factors={data.explanation.top_factors} />

      <PanelWarnings warnings={data.explanation.warnings} />

      <DisclaimerCalidad level={data.data_quality.level} />

      {debtFlags.length > 0 && (
        <aside className="rounded-xl border border-fuchsia-500/30 bg-fuchsia-500/10 p-3 text-xs text-fuchsia-200">
          Deuda residual activa: {debtFlags.join(', ')}
        </aside>
      )}

      <footer className="text-[11px] text-slate-400">
        Esta predicción es solo informativa y no constituye asesoría financiera. Las apuestas deportivas implican riesgo.
      </footer>
    </article>
  );
}
