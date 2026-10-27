import { useEffect, useRef, useState } from 'react';
import type { Competicion, PartidoFutbolResumen } from '../../tipos/futbol';
import { listarCatalogo, listarCompeticiones, listarTemporadas, resolverPartidoCatalogo, type TemporadaFutbol } from '../../servicios/futbol/catalogo';

interface Props {
  revision: number;
  onInicio: () => void;
  onCargando: (valor: boolean) => void;
  onError: (valor: string | null) => void;
  onDatos: (partidos: PartidoFutbolResumen[]) => void;
  onTemporadas: (ids: string[]) => void;
}

/** El selector cambia las consultas reales, no solo el título de la pantalla. */
export function CatalogoFutbol({ revision, onInicio, onCargando, onError, onDatos, onTemporadas }: Props) {
  const [competiciones, setCompeticiones] = useState<Competicion[]>([]);
  const [competicionId, setCompeticion] = useState('');
  const [temporadas, setTemporadas] = useState<TemporadaFutbol[]>([]);
  const [temporadaId, setTemporada] = useState('');
  const [modo, setModo] = useState<'proximos' | 'historicos'>('proximos');
  const [pagina, setPagina] = useState(1);
  const [total, setTotal] = useState(0);
  const [cargandoTemporadas, setCargandoTemporadas] = useState(false);
  const [recarga, setRecarga] = useState(0);
  const inicioAplicado = useRef(false);

  useEffect(() => {
    const ctl = new AbortController();
    listarCompeticiones(ctl.signal).then(async data => {
      if (ctl.signal.aborted) return;
      let sugerida = '';
      if (!inicioAplicado.current) {
        const query = new URLSearchParams(window.location.search);
        sugerida = query.get('competicionId') || '';
        const pid = query.get('partidoId');
        if (pid && /^[0-9a-f-]{36}$/i.test(pid)) {
          const p = await resolverPartidoCatalogo(pid, ctl.signal).catch(() => null);
          if (ctl.signal.aborted) return;
          if (p) {
            sugerida = p.competicionId;
            setTemporada(p.temporadaId || '');
            setModo(p.estado === 'FINALIZADO' ? 'historicos' : 'proximos');
          }
        } else {
          setModo(query.get('modo') === 'historicos' ? 'historicos' : 'proximos');
          setTemporada(query.get('temporadaId') || '');
        }
        inicioAplicado.current = true;
      }
      setCompeticiones(data);
      setCompeticion(prev => data.some(c => c.id === prev) ? prev : data.find(c => c.id === sugerida)?.id || data[0]?.id || '');
    }).catch(err => { if (!ctl.signal.aborted) { onError(err.message); onCargando(false); } });
    return () => ctl.abort();
  }, [onError, onCargando, revision, recarga]);

  useEffect(() => {
    if (!competicionId) return;
    const ctl = new AbortController();
    setCargandoTemporadas(true);
    listarTemporadas(competicionId, ctl.signal).then(data => {
      if (!ctl.signal.aborted) {
        setTemporadas(data); setTemporada(prev => data.some(t => t.id === prev) ? prev : ''); setCargandoTemporadas(false);
      }
    }).catch(err => {
      if (!ctl.signal.aborted) { onError(err.message); setCargandoTemporadas(false); }
    });
    return () => ctl.abort();
  }, [competicionId, onError, revision, recarga]);

  useEffect(() => {
    if (!competicionId || cargandoTemporadas) return;
    const ctl = new AbortController();
    setTotal(0); onInicio(); onDatos([]); onCargando(true); onError(null);
    listarCatalogo({ competicionId, temporadaId, modo, pagina }, ctl.signal).then(data => {
      if (ctl.signal.aborted) return;
      onDatos(data.partidos); setTotal(data.total); onCargando(false);
    }).catch(err => { if (!ctl.signal.aborted) { onError(err.message); onCargando(false); } });
    return () => ctl.abort();
  }, [competicionId, temporadaId, modo, pagina, revision, recarga, cargandoTemporadas, onInicio, onDatos, onCargando, onError]);

  useEffect(() => {
    onTemporadas(temporadaId ? [temporadaId] : temporadas.map(t => t.id));
  }, [temporadaId, temporadas, onTemporadas]);

  const clases = 'mt-1 w-full min-w-0 rounded border border-neon-cyan/30 bg-futurista-negro px-3 py-2 text-sm text-texto-principal';
  const guardarFiltro = (cid: string, tipo: typeof modo, tid: string) => {
    const url = new URL(window.location.href);
    url.searchParams.delete('partidoId');
    url.searchParams.set('competicionId', cid); url.searchParams.set('modo', tipo);
    if (tid) url.searchParams.set('temporadaId', tid); else url.searchParams.delete('temporadaId');
    window.history.replaceState({}, '', url);
  };
  return <section className="tarjeta space-y-3" aria-label="Catálogo de fútbol">
    <label className="block text-xs text-texto-secundario">Competición
      <select aria-label="Competición" value={competicionId} className={clases} onChange={e => {
        guardarFiltro(e.target.value, modo, '');
        setTemporada(''); setTemporadas([]); setPagina(1); setCompeticion(e.target.value);
      }}>
        {!competiciones.length && <option value="">Cargando competiciones…</option>}
        {competiciones.map(c => <option key={c.id} value={c.id}>{c.nombre} · {c.pais}</option>)}
      </select>
    </label>
    <label className="block text-xs text-texto-secundario">Consultar
      <select aria-label="Tipo de partidos" value={modo} className={clases} onChange={e => { guardarFiltro(competicionId, e.target.value as typeof modo, temporadaId); setModo(e.target.value as typeof modo); setPagina(1); }}>
        <option value="proximos">Próximos — hasta 90 días</option>
        <option value="historicos">Históricos — reconstrucción prepartido</option>
      </select>
    </label>
    <label className="block text-xs text-texto-secundario">Temporada
      <select aria-label="Temporada de fútbol" disabled={cargandoTemporadas} value={temporadaId} className={clases} onChange={e => { guardarFiltro(competicionId, modo, e.target.value); setTemporada(e.target.value); setPagina(1); }}>
        <option value="">Todas las temporadas registradas</option>
        {temporadas.map(t => <option key={t.id} value={t.id}>{t.nombre} · {t.finales} finales</option>)}
      </select>
    </label>
    <p className="text-xs text-texto-secundario">{total} partidos registrados · página {pagina} de {Math.max(1, Math.ceil(total / 50))}. Horas en Colombia (UTC−5).</p>
    <div className="flex flex-wrap gap-3 text-xs text-neon-cyan">
      <button type="button" disabled={pagina <= 1} onClick={() => setPagina(p => p - 1)}>Anterior</button>
      <button type="button" disabled={pagina * 50 >= total} onClick={() => setPagina(p => p + 1)}>Siguiente</button>
      <button type="button" onClick={() => setRecarga(x => x + 1)}>Reintentar carga</button>
    </div>
    {total === 0 && <p className="text-xs text-texto-secundario">No hay partidos en este filtro. Un calendario vacío no certifica que no existan encuentros; puedes consultar el histórico.</p>}
    {modo === 'historicos' && <p className="text-xs text-neon-amarillo">Reconstrucción con datos anteriores al encuentro. No es un pronóstico emitido entonces y no permite guardar apuestas.</p>}
  </section>;
}
