import { useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, ClipboardCopy, Plus, ShieldAlert, Trash2 } from 'lucide-react';
import { Boton, Input, Select, Tarjeta } from '../atomos';
import {
  generarAnalisisNba,
  type NbaMarket,
  type NbaMarketEvaluation,
  type NbaMatchAnalysisRequest,
  type NbaMatchAnalysisResponse,
  type NbaSourceType,
  type NbaStructuredWarning,
} from '../../servicios/nbaMatchAnalysis';

const MERCADOS: Array<{ valor: NbaMarket; etiqueta: string }> = [
  { valor: 'FULL_GAME_TOTAL', etiqueta: 'FULL_GAME_TOTAL' },
  { valor: 'Q1_TOTAL', etiqueta: 'Q1_TOTAL' },
  { valor: 'HOME_TEAM_TOTAL', etiqueta: 'HOME_TEAM_TOTAL' },
  { valor: 'AWAY_TEAM_TOTAL', etiqueta: 'AWAY_TEAM_TOTAL' },
];

const SOURCE_TYPES: Array<{ valor: NbaSourceType; etiqueta: string }> = [
  { valor: 'REAL_MARKET', etiqueta: 'REAL_MARKET' },
  { valor: 'DERIVED_FROM_TOTAL_SPREAD', etiqueta: 'DERIVED_FROM_TOTAL_SPREAD' },
  { valor: 'TECHNICAL_ESTIMATE', etiqueta: 'TECHNICAL_ESTIMATE' },
  { valor: 'MANUAL_INPUT', etiqueta: 'MANUAL_INPUT' },
];

interface MercadoFormulario {
  id: string;
  market: NbaMarket | '';
  line: string;
  over_odds: string;
  under_odds: string;
  source: string;
  source_type: NbaSourceType | '';
  source_url: string;
  notes: string;
}

type ErroresFormulario = Record<string, string>;

const mercadoInicial = (id: string = crypto.randomUUID()): MercadoFormulario => ({
  id,
  market: 'FULL_GAME_TOTAL',
  line: '',
  over_odds: '',
  under_odds: '',
  source: '',
  source_type: 'REAL_MARKET',
  source_url: '',
  notes: '',
});

function esNumero(valor: string): boolean {
  if (!valor.trim()) return false;
  return Number.isFinite(Number(valor));
}

function numeroONull(valor: string): number | null {
  return valor.trim() ? Number(valor) : null;
}

function formatearNumero(valor: unknown, decimales = 2): string {
  return typeof valor === 'number' && Number.isFinite(valor) ? valor.toFixed(decimales) : 'N/D';
}

function warningTexto(warning: NbaStructuredWarning | string): string {
  return typeof warning === 'string' ? warning : `${warning.code}: ${warning.message}`;
}

function contarCalidad(dataQuality: NbaMatchAnalysisResponse['data_quality']) {
  const buckets = Object.values(dataQuality ?? {});
  let candidatas = 0;
  let usadas = 0;
  let excluidas = 0;
  const razones: Record<string, number> = {};

  for (const bucket of buckets) {
    const valid = Array.isArray(bucket.valid) ? bucket.valid.length : Number(bucket.valid_count ?? 0);
    const excluded = Array.isArray(bucket.excluded) ? bucket.excluded.length : Number(bucket.excluded_count ?? 0);
    usadas += Number.isFinite(valid) ? valid : 0;
    excluidas += Number.isFinite(excluded) ? excluded : 0;
    const reasonCounts = bucket.reason_counts;
    if (reasonCounts && typeof reasonCounts === 'object') {
      for (const [razon, total] of Object.entries(reasonCounts)) {
        razones[razon] = (razones[razon] ?? 0) + Number(total ?? 0);
      }
    }
  }

  candidatas = usadas + excluidas;
  const porcentajeExcluido = candidatas > 0 ? (excluidas / candidatas) * 100 : 0;
  return { candidatas, usadas, excluidas, porcentajeExcluido, razones };
}

function BadgePolicy({ activo, texto }: { activo: boolean; texto: string }) {
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-semibold ${activo ? 'border-green-400/40 bg-green-400/10 text-green-300' : 'border-red-400/40 bg-red-400/10 text-red-300'}`}>
      <CheckCircle2 size={14} /> {texto}
    </span>
  );
}

function WarningCard({ warning }: { warning: NbaStructuredWarning }) {
  return (
    <div className="rounded-lg border border-amber-400/30 bg-amber-400/10 p-3 text-sm">
      <div className="flex flex-wrap items-center gap-2 font-semibold text-amber-200">
        <AlertTriangle size={16} />
        <span>{warning.code}</span>
        <span className="rounded-full bg-amber-500/20 px-2 py-0.5 text-xs">{warning.severity}</span>
        <span className="rounded-full bg-futurista-medio px-2 py-0.5 text-xs">{warning.scope}</span>
      </div>
      <p className="mt-2 text-texto-principal">{warning.message}</p>
      <div className="mt-2 flex flex-wrap gap-2 text-xs text-texto-secundario">
        {warning.market && <span>Market: {warning.market}</span>}
        {warning.team && <span>Team: {warning.team}</span>}
      </div>
    </div>
  );
}

function EvaluacionMercado({ evaluacion }: { evaluacion: NbaMarketEvaluation & { clasificacion?: string } }) {
  const input = evaluacion.input;
  const sourceType = evaluacion.source_type ?? input?.source_type;
  const line = input?.line ?? 'N/D';
  const warnings = evaluacion.advertencias ?? [];

  return (
    <Tarjeta variante="borde" padding="md" className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-texto-principal">{evaluacion.market}</h3>
          <p className="text-sm text-texto-secundario">Fuente: {evaluacion.source ?? input?.source ?? 'N/D'}</p>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold ${sourceType === 'REAL_MARKET' ? 'bg-green-400/10 text-green-300' : 'bg-amber-400/10 text-amber-200'}`}>
          {sourceType ?? 'SOURCE_TYPE N/D'}
        </span>
      </div>

      {sourceType && sourceType !== 'REAL_MARKET' && (
        <div className="rounded-lg border border-amber-400/30 bg-amber-400/10 p-3 text-sm text-amber-100">
          Esta línea no proviene de mercado real.
        </div>
      )}

      <div className="grid gap-3 md:grid-cols-4">
        <Dato etiqueta="Línea" valor={String(line)} />
        <Dato etiqueta="Clasificación" valor={evaluacion.clasificacion ?? evaluacion.clasificacion_tecnica ?? 'N/D'} />
        <Dato etiqueta="Dif. vs promedio" valor={formatearNumero(evaluacion.diferencia_contra_linea)} />
        <Dato etiqueta="Volatilidad" valor={formatearNumero(evaluacion.volatilidad)} />
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-lg bg-futurista-oscuro/60 p-3">
          <p className="mb-2 text-xs uppercase tracking-wide text-texto-secundario">Cumplimiento Over</p>
          <Cumplimientos datos={evaluacion.porcentaje_cumplimiento_over} />
        </div>
        <div className="rounded-lg bg-futurista-oscuro/60 p-3">
          <p className="mb-2 text-xs uppercase tracking-wide text-texto-secundario">Cumplimiento Under</p>
          <Cumplimientos datos={evaluacion.porcentaje_cumplimiento_under} />
        </div>
      </div>

      {warnings.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-semibold text-amber-200">Advertencias específicas</p>
          {warnings.map((warning, index) => (
            <div key={`${evaluacion.market}-warning-${index}`} className="rounded border border-amber-400/20 bg-amber-400/5 p-2 text-sm text-amber-100">
              {warningTexto(warning)}
            </div>
          ))}
        </div>
      )}
    </Tarjeta>
  );
}

function Cumplimientos({ datos }: { datos?: Record<string, number> }) {
  if (!datos || Object.keys(datos).length === 0) return <p className="text-sm text-texto-secundario">N/D</p>;
  return (
    <div className="grid grid-cols-4 gap-2 text-sm">
      {['5', '10', '20', '30'].map((ventana) => (
        <div key={ventana} className="rounded bg-futurista-medio/70 p-2 text-center">
          <p className="text-xs text-texto-secundario">{ventana}</p>
          <p className="font-semibold text-texto-principal">{formatearNumero(datos[ventana], 1)}%</p>
        </div>
      ))}
    </div>
  );
}

function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="rounded-lg bg-futurista-oscuro/60 p-3">
      <p className="text-xs uppercase tracking-wide text-texto-secundario">{etiqueta}</p>
      <p className="mt-1 font-semibold text-texto-principal">{valor}</p>
    </div>
  );
}

export function PaginaAnalisisNbaAdmin() {
  const [home, setHome] = useState('San Antonio Spurs');
  const [away, setAway] = useState('Minnesota Timberwolves');
  const [date, setDate] = useState('2026-05-05');
  const [mercados, setMercados] = useState<MercadoFormulario[]>([
    {
      ...mercadoInicial('market-real'),
      line: '218.5',
      over_odds: '1.91',
      under_odds: '1.91',
      source: 'ESPN/DraftKings close',
      source_url: 'https://www.espn.com/nba/game/_/gameId/401871152',
    },
  ]);
  const [errores, setErrores] = useState<ErroresFormulario>({});
  const [resultado, setResultado] = useState<NbaMatchAnalysisResponse | null>(null);
  const [requestEnviado, setRequestEnviado] = useState<NbaMatchAnalysisRequest | null>(null);
  const [errorBackend, setErrorBackend] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [copiado, setCopiado] = useState(false);

  const calidad = useMemo(() => (resultado ? contarCalidad(resultado.data_quality) : null), [resultado]);

  const actualizarMercado = (id: string, campo: keyof MercadoFormulario, valor: string) => {
    setMercados((actuales) => actuales.map((m) => (m.id === id ? { ...m, [campo]: valor } : m)));
  };

  const agregarMercado = () => setMercados((actuales) => [...actuales, mercadoInicial()]);
  const eliminarMercado = (id: string) => setMercados((actuales) => actuales.length > 1 ? actuales.filter((m) => m.id !== id) : actuales);

  const validar = (): NbaMatchAnalysisRequest | null => {
    const nuevosErrores: ErroresFormulario = {};
    if (!home.trim()) nuevosErrores.home = 'Equipo local obligatorio.';
    if (!away.trim()) nuevosErrores.away = 'Equipo visitante obligatorio.';
    if (!date.trim()) nuevosErrores.date = 'Fecha obligatoria.';

    mercados.forEach((m, index) => {
      const prefijo = `markets.${index}`;
      if (!m.market) nuevosErrores[`${prefijo}.market`] = 'Market obligatorio.';
      if (!m.source_type) nuevosErrores[`${prefijo}.source_type`] = 'source_type obligatorio.';
      if (!esNumero(m.line)) nuevosErrores[`${prefijo}.line`] = 'line obligatorio y numérico.';
      if (!m.source.trim()) nuevosErrores[`${prefijo}.source`] = 'source obligatorio.';
      if (m.over_odds.trim() && !esNumero(m.over_odds)) nuevosErrores[`${prefijo}.over_odds`] = 'over_odds debe ser numérico o vacío.';
      if (m.under_odds.trim() && !esNumero(m.under_odds)) nuevosErrores[`${prefijo}.under_odds`] = 'under_odds debe ser numérico o vacío.';
      if (m.source_type && m.source_type !== 'REAL_MARKET' && !m.notes.trim()) {
        nuevosErrores[`${prefijo}.notes`] = 'notes obligatorio si source_type no es REAL_MARKET.';
      }
    });

    setErrores(nuevosErrores);
    if (Object.keys(nuevosErrores).length > 0) return null;

    return {
      home: home.trim(),
      away: away.trim(),
      date,
      markets: mercados.map((m) => ({
        market: m.market as NbaMarket,
        line: Number(m.line),
        over_odds: numeroONull(m.over_odds),
        under_odds: numeroONull(m.under_odds),
        source: m.source.trim(),
        source_type: m.source_type as NbaSourceType,
        source_url: m.source_url.trim() || null,
        notes: m.notes.trim() || null,
      })),
    };
  };

  const enviar = async () => {
    const payload = validar();
    if (!payload) return;
    setCargando(true);
    setErrorBackend(null);
    setResultado(null);
    setRequestEnviado(payload);

    try {
      const data = await generarAnalisisNba(payload);
      setResultado(data);
    } catch (error) {
      setErrorBackend(error instanceof Error ? error.message : 'Error inesperado al generar análisis.');
    } finally {
      setCargando(false);
    }
  };

  const copiarResumen = async () => {
    if (!resultado?.external_summary) return;
    await navigator.clipboard.writeText(resultado.external_summary);
    setCopiado(true);
    window.setTimeout(() => setCopiado(false), 1800);
  };

  return (
    <main className="min-h-screen bg-futurista-negro px-4 py-8 text-texto-principal md:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="space-y-3">
          <p className="text-sm uppercase tracking-[0.3em] text-neon-cyan">Admin interno</p>
          <h1 className="text-3xl font-bold md:text-4xl">Análisis NBA</h1>
          <div className="rounded-xl border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">
            <div className="flex gap-2 font-semibold"><ShieldAlert size={18} /> Herramienta interna, no pública.</div>
            <p className="mt-2">Este módulo genera análisis estadístico/deportivo. No genera picks, no calcula stake y no representa recomendación de apuesta.</p>
          </div>
        </header>

        <Tarjeta padding="lg" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-3">
            <Input etiqueta="Equipo local" value={home} onChange={(e) => setHome(e.target.value)} error={errores.home} />
            <Input etiqueta="Equipo visitante" value={away} onChange={(e) => setAway(e.target.value)} error={errores.away} />
            <Input etiqueta="Fecha" type="date" value={date} onChange={(e) => setDate(e.target.value)} error={errores.date} />
          </div>

          <section className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold">Mercados a evaluar</h2>
                <p className="text-sm text-texto-secundario">El frontend solo valida contrato y envía datos; las métricas las calcula el backend.</p>
              </div>
              <Boton type="button" variante="secundario" iconoInicio={<Plus size={16} />} onClick={agregarMercado}>Agregar mercado</Boton>
            </div>

            {mercados.map((mercado, index) => {
              const prefijo = `markets.${index}`;
              const noReal = mercado.source_type && mercado.source_type !== 'REAL_MARKET';
              return (
                <div key={mercado.id} className="rounded-xl border border-neon-cyan/15 bg-futurista-oscuro/50 p-4 space-y-4">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="font-semibold">Mercado #{index + 1}</h3>
                    <Boton type="button" variante="fantasma" tamano="sm" iconoInicio={<Trash2 size={15} />} onClick={() => eliminarMercado(mercado.id)} disabled={mercados.length === 1}>Eliminar</Boton>
                  </div>

                  <div className="grid gap-4 md:grid-cols-4">
                    <Select etiqueta="market" value={mercado.market} opciones={MERCADOS} onChange={(e) => actualizarMercado(mercado.id, 'market', e.target.value)} error={errores[`${prefijo}.market`]} />
                    <Input etiqueta="line" inputMode="decimal" value={mercado.line} onChange={(e) => actualizarMercado(mercado.id, 'line', e.target.value)} error={errores[`${prefijo}.line`]} />
                    <Input etiqueta="over_odds" inputMode="decimal" value={mercado.over_odds} onChange={(e) => actualizarMercado(mercado.id, 'over_odds', e.target.value)} textoAyuda="Puede quedar vacío" error={errores[`${prefijo}.over_odds`]} />
                    <Input etiqueta="under_odds" inputMode="decimal" value={mercado.under_odds} onChange={(e) => actualizarMercado(mercado.id, 'under_odds', e.target.value)} textoAyuda="Puede quedar vacío" error={errores[`${prefijo}.under_odds`]} />
                  </div>

                  <div className="grid gap-4 md:grid-cols-2">
                    <Input etiqueta="source" value={mercado.source} onChange={(e) => actualizarMercado(mercado.id, 'source', e.target.value)} error={errores[`${prefijo}.source`]} />
                    <Select etiqueta="source_type" value={mercado.source_type} opciones={SOURCE_TYPES} onChange={(e) => actualizarMercado(mercado.id, 'source_type', e.target.value)} error={errores[`${prefijo}.source_type`]} />
                  </div>

                  {noReal && <div className="rounded-lg border border-amber-400/30 bg-amber-400/10 p-3 text-sm text-amber-100">Esta línea no proviene de mercado real.</div>}

                  <div className="grid gap-4 md:grid-cols-2">
                    <Input etiqueta="source_url opcional" value={mercado.source_url} onChange={(e) => actualizarMercado(mercado.id, 'source_url', e.target.value)} />
                    <Input etiqueta="notes" value={mercado.notes} onChange={(e) => actualizarMercado(mercado.id, 'notes', e.target.value)} error={errores[`${prefijo}.notes`]} textoAyuda="Obligatorio si source_type no es REAL_MARKET" />
                  </div>
                </div>
              );
            })}
          </section>

          {errorBackend && <div className="rounded-xl border border-red-400/40 bg-red-500/10 p-4 text-red-200">{errorBackend}</div>}

          <Boton type="button" tamano="lg" cargando={cargando} textoCargando="Generando análisis..." onClick={enviar}>
            Generar análisis
          </Boton>
        </Tarjeta>

        {resultado && calidad && (
          <section className="space-y-6">
            <Tarjeta padding="md" className="space-y-3">
              <h2 className="text-xl font-semibold">Policy</h2>
              <div className="flex flex-wrap gap-2">
                <BadgePolicy activo={resultado.policy.no_picks} texto="No picks" />
                <BadgePolicy activo={resultado.policy.no_stake} texto="No stake" />
                <BadgePolicy activo={resultado.policy.no_betting_recommendations} texto="No recomendaciones" />
              </div>
            </Tarjeta>

            <Tarjeta padding="md" className="space-y-4">
              <h2 className="text-xl font-semibold">Resumen del partido</h2>
              <div className="grid gap-3 md:grid-cols-4">
                <Dato etiqueta="Local" valor={resultado.teams.equipo_local?.nombre ?? requestEnviado?.home ?? 'N/D'} />
                <Dato etiqueta="Visitante" valor={resultado.teams.equipo_visitante?.nombre ?? requestEnviado?.away ?? 'N/D'} />
                <Dato etiqueta="Fecha" valor={resultado.teams.fecha ?? requestEnviado?.date ?? 'N/D'} />
                <Dato etiqueta="Máxima BD" valor={resultado.teams.fecha_maxima_disponible_bd ?? String(resultado.metadata.fecha_maxima_disponible_bd ?? 'N/D')} />
              </div>
            </Tarjeta>

            <Tarjeta padding="md" className="space-y-4">
              <h2 className="text-xl font-semibold">Calidad de datos</h2>
              {calidad.excluidas > 0 && <div className="rounded-lg border border-amber-400/30 bg-amber-400/10 p-3 text-amber-100">Hay apariciones excluidas. Revisar razones antes de usar el análisis.</div>}
              <div className="grid gap-3 md:grid-cols-4">
                <Dato etiqueta="Candidatas" valor={String(calidad.candidatas)} />
                <Dato etiqueta="Usadas" valor={String(calidad.usadas)} />
                <Dato etiqueta="Excluidas" valor={String(calidad.excluidas)} />
                <Dato etiqueta="% excluido" valor={`${formatearNumero(calidad.porcentajeExcluido)}%`} />
              </div>
              <div className="rounded-lg bg-futurista-oscuro/60 p-3">
                <p className="mb-2 text-sm font-semibold">Razones de exclusión</p>
                {Object.keys(calidad.razones).length === 0 ? <p className="text-sm text-texto-secundario">Sin razones agregadas reportadas.</p> : (
                  <ul className="space-y-1 text-sm text-texto-secundario">
                    {Object.entries(calidad.razones).map(([razon, total]) => <li key={razon}>- {razon}: {total}</li>)}
                  </ul>
                )}
              </div>
            </Tarjeta>

            <Tarjeta padding="md" className="space-y-4">
              <h2 className="text-xl font-semibold">Métricas combinadas</h2>
              <div className="grid gap-3 md:grid-cols-5">
                {['q1', 'q2', 'q3', 'q4', 'total'].map((clave) => (
                  <Dato key={clave} etiqueta={clave.toUpperCase()} valor={typeof resultado.combined_metrics[clave] === 'number' ? formatearNumero(resultado.combined_metrics[clave]) : 'Ver evaluación por mercado'} />
                ))}
              </div>
            </Tarjeta>

            <section className="space-y-4">
              <h2 className="text-xl font-semibold">Evaluación de mercados</h2>
              {resultado.market_evaluations.map((evaluacion, index) => <EvaluacionMercado key={`${evaluacion.market}-${index}`} evaluacion={evaluacion} />)}
            </section>

            <Tarjeta padding="md" className="space-y-4">
              <h2 className="text-xl font-semibold">Warnings</h2>
              {resultado.warnings.length === 0 ? <p className="text-sm text-texto-secundario">Sin warnings generales.</p> : (
                <div className="space-y-3">{resultado.warnings.map((warning, index) => <WarningCard key={`${warning.code}-${index}`} warning={warning} />)}</div>
              )}
            </Tarjeta>

            <Tarjeta padding="md" className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="text-xl font-semibold">Resumen para análisis externo</h2>
                <Boton type="button" variante="secundario" iconoInicio={<ClipboardCopy size={16} />} onClick={copiarResumen}>{copiado ? 'Copiado' : 'Copiar resumen externo'}</Boton>
              </div>
              <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-xl bg-futurista-oscuro p-4 text-sm text-texto-principal">{resultado.external_summary}</pre>
            </Tarjeta>
          </section>
        )}
      </div>
    </main>
  );
}
