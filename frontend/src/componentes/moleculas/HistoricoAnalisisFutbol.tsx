import { useEffect, useState } from 'react';
import { listarTemporadas, type TemporadaFutbol } from '../../servicios/futbol/catalogo';
import type { PartidoFutbolResumen } from '../../tipos/futbol';

interface Props {
  partido: PartidoFutbolResumen;
  seleccion: string[];
  onCambiar: (competicion: string, ids: string[]) => void;
}

export function HistoricoAnalisisFutbol({ partido, seleccion, onCambiar }: Props) {
  const [temporadas, setTemporadas] = useState<TemporadaFutbol[]>([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const ctl = new AbortController();
    setCargando(true); setError(false);
    listarTemporadas(partido.competicion, ctl.signal).then(data => {
      if (!ctl.signal.aborted) setTemporadas(data.filter(t => t.anio_inicio <= new Date(partido.fechaPartido).getUTCFullYear()));
    }).catch(() => { if (!ctl.signal.aborted) setError(true); })
      .finally(() => { if (!ctl.signal.aborted) setCargando(false); });
    return () => ctl.abort();
  }, [partido.competicion, partido.fechaPartido, revision]);
  return <details className="tarjeta !p-4">
    <summary className="cursor-pointer text-sm font-semibold text-texto-principal">Histórico para calcular <span className="mt-1 block text-xs font-normal text-texto-secundario">{seleccion.length === 1 ? '1 temporada seleccionada' : seleccion.length ? `${seleccion.length} temporadas seleccionadas` : 'Automático · temporada del corte y anterior'}</span></summary>
    <div className="mt-4 space-y-3">
      <p className="text-xs leading-relaxed text-texto-secundario">Solo partidos de {partido.competicionNombre}, anteriores al encuentro y al momento de la consulta. Elegir la fecha en la agenda no cambia estas temporadas.</p>
      <button type="button" aria-pressed={!seleccion.length} onClick={() => onCambiar(partido.competicion, [])} className="text-xs text-neon-cyan">Usar selección automática</button>
      {cargando && <p className="text-xs text-texto-secundario" role="status">Cargando temporadas…</p>}
      {error && <p role="alert" className="text-xs text-neon-amarillo">No se pudieron cargar las temporadas. Se mantiene el modo automático. <button type="button" className="underline" onClick={() => setRevision(n => n + 1)}>Reintentar temporadas</button></p>}
      {!cargando && !error && <fieldset className="space-y-2"><legend className="mb-2 text-xs text-texto-secundario">Temporadas utilizadas para el análisis</legend>
        {temporadas.map(t => <label key={t.id} className="flex items-center justify-between gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm text-texto-principal"><span className="flex items-center gap-2"><input type="checkbox" checked={seleccion.includes(t.id)} onChange={e => onCambiar(partido.competicion, e.target.checked ? [...seleccion, t.id] : seleccion.filter(id => id !== t.id))} />{t.nombre}</span><span className="text-xs text-texto-terciario">{t.finales} finales</span></label>)}
        {temporadas.length > 0 && <button type="button" onClick={() => onCambiar(partido.competicion, temporadas.map(t => t.id))} className="pt-1 text-xs text-neon-cyan">Usar todas las temporadas disponibles</button>}
      </fieldset>}
      {partido.estado === 'FINALIZADO' && <p className="text-xs text-neon-amarillo">Reconstrucción histórica con corte anterior al partido; no es un pronóstico emitido entonces.</p>}
    </div>
  </details>;
}
