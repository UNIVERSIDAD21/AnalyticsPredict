/** Una sola pantalla; cada liga monta exclusivamente su motor y su estado. */
import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Encabezado } from '../organismos/Encabezado';
import { leerLigaBaloncesto } from '../../utilidades/ligasBaloncesto';
import { AgendaBaloncesto } from '../moleculas/AgendaBaloncesto';
import type { PartidoAgendaBaloncesto } from '../../servicios/agendaBaloncesto';

const ModuloNBA = lazy(async () => ({ default: (await import('./PaginaPrincipal')).PaginaPrincipal }));
const ModuloWNBA = lazy(async () => ({ default: (await import('./PaginaWnba')).ModuloWnba }));
const ModuloEuroliga = lazy(async () => ({ default: (await import('./PaginaEuroliga')).ModuloEuroliga }));

export function PaginaBaloncesto() {
  const [params, setParams] = useSearchParams();
  const liga = leerLigaBaloncesto(`?${params}`);
  const [reloj, setReloj] = useState(Date.now);
  useEffect(() => { const id = setInterval(() => setReloj(Date.now()), 15000); return () => clearInterval(id); }, []);
  const [seleccionado, setSeleccionado] = useState<PartidoAgendaBaloncesto | null>(null);
  const seleccionar = useCallback((p: PartidoAgendaBaloncesto) => {
    setSeleccionado(p);
    if (params.get('partidoId') === p.id && params.get('liga') === p.liga && params.get('fecha') === p.fecha_partido) return;
    setParams(prev => {
      const n = new URLSearchParams(prev); n.set('liga', p.liga); n.set('fecha', p.fecha_partido); n.set('partidoId', p.id);
      ['tab','equipo','analisis','lado'].forEach(k => n.delete(k)); return n;
    });
  }, [params, setParams]);
  const limpiarSeleccion = useCallback(() => {
    setSeleccionado(null);
    setParams(prev => { if (!prev.has('partidoId')) return prev; const n = new URLSearchParams(prev); n.delete('partidoId'); return n; }, { replace: true });
  }, [setParams]);
  const partidoId = params.get('partidoId');
  const partido = useMemo(() => {
    if (seleccionado?.liga !== liga || seleccionado.id !== partidoId) return null;
    const reconstruccion = !seleccionado.inicio_utc || seleccionado.estado !== 'PROGRAMADO' || Date.parse(seleccionado.inicio_utc) <= reloj;
    return { ...seleccionado, reconstruccion };
  }, [seleccionado, liga, partidoId, reloj]);
  const idSeleccionado = partido?.id;
  useEffect(() => { if (idSeleccionado) document.getElementById('configurar-baloncesto')?.scrollIntoView?.({ behavior: 'smooth', block: 'start' }); }, [idSeleccionado]);
  const cambiarLiga = (valor: string) => {
    setSeleccionado(null);
    const siguientes = new URLSearchParams(params);
    siguientes.set('liga', valor);
    siguientes.delete('tab');
    siguientes.delete('equipo');
    siguientes.delete('analisis');
    siguientes.delete('lado');
    siguientes.delete('partidoId');
    setParams(siguientes);
  };

  return <div className="min-h-screen flex flex-col">
    <Encabezado />
    <main id="contenido-principal" tabIndex={-1} className="flex-1 contenedor py-6 lg:py-8 min-w-0">
      {partido && <div className="flex flex-wrap justify-between gap-3 mb-5"><h1 className="text-2xl font-semibold">Ficha del partido</h1><button className="text-neon-cyan" onClick={limpiarSeleccion}>Cambiar partido</button></div>}
      <details open={!partido} className="mb-5"><summary className="text-sm text-texto-secundario cursor-pointer mb-3">{partido ? 'Ver agenda y otros encuentros' : 'Agenda de baloncesto'}</summary>
        <AgendaBaloncesto seleccionado={partido} onSeleccionar={seleccionar} onCambiar={limpiarSeleccion} />
      </details>
      <section id="configurar-baloncesto" className="mb-6 tarjeta p-5 flex flex-wrap items-center justify-between gap-4" aria-label="Baloncesto y liga activa">
        <div>
          <h2 className="text-xl font-futurista text-texto-principal">Baloncesto · {partido ? 'Configurar análisis' : 'Análisis manual y estadísticas'}</h2>
          <p className="text-sm text-texto-secundario mt-2">{partido ? `${partido.equipo_local_nombre} — ${partido.equipo_visitante_nombre}` : 'Selecciona un partido en la agenda o abre el análisis manual de una liga.'}</p>
          {!partido && <button type="button" className="mt-3 text-sm text-neon-cyan" onClick={() => cambiarLiga(liga)}>Abrir análisis manual</button>}
        </div>
        {!partido && <label className="block text-xs font-semibold uppercase tracking-wider text-texto-secundario w-full sm:w-52">
          Liga
          <select className="input-base mt-2 w-full" value={liga} onChange={e => cambiarLiga(e.target.value)}>
            <option value="nba">NBA</option>
            <option value="euroliga">Euroliga</option>
            <option value="wnba">WNBA</option>
          </select>
        </label>}
        {partido && <p className="text-sm text-neon-cyan">Liga: {liga.toUpperCase()} · Localía del encuentro seleccionado</p>}
      </section>
      {(partido || params.has('liga') || params.has('tab')) && <Suspense fallback={<p role="status">Cargando {liga === 'nba' ? 'NBA' : liga === 'wnba' ? 'WNBA' : 'Euroliga'}…</p>}>
        {liga === 'nba' ? <ModuloNBA key={`nba-${partido?.id ?? 'manual'}`} partidoAgenda={partido} /> : liga === 'wnba' ? <ModuloWNBA key={`wnba-${partido?.id ?? 'manual'}`} partidoAgenda={partido} /> : <ModuloEuroliga key={`euroliga-${partido?.id ?? 'manual'}`} partidoAgenda={partido} />}
      </Suspense>}
    </main>
    <footer className="border-t border-neon-cyan/10 bg-futurista-negro/80">
      <div className="contenedor py-4 flex flex-wrap justify-between gap-2 text-xs text-texto-terciario">
        <p>AnalyticsPredict · Baloncesto · {liga === 'nba' ? 'NBA' : liga === 'wnba' ? 'WNBA' : 'Euroliga'}</p>
        <p>Análisis exploratorio; eficacia no certificada.</p>
      </div>
    </footer>
  </div>;
}
