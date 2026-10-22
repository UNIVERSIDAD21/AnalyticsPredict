import { useId, useState } from 'react';
import { ChevronDown, ChevronUp, History } from 'lucide-react';
import { Tarjeta } from '../atomos';
import type { PartidoContextoEuro, ResumenTemporadaEuro } from '../../servicios/euroliga';

type EquipoContexto = { recientes: PartidoContextoEuro[]; temporada_resumen?: ResumenTemporadaEuro };
type Sede = 'TODOS' | 'LOCAL' | 'VISITANTE';

function equipoContexto(equipos: Record<string, EquipoContexto>, nombre: string): EquipoContexto {
  const clave = Object.keys(equipos).find((k) => k.toLocaleLowerCase() === nombre.toLocaleLowerCase());
  return clave ? equipos[clave] : { recientes: [] };
}

function fechaVisible(fecha: string): string {
  const mediodiaLocal = new Date(`${fecha.slice(0, 10)}T12:00:00`);
  return Number.isNaN(mediodiaLocal.getTime()) ? fecha : mediodiaLocal.toLocaleDateString('es-ES', { day: '2-digit', month: 'short', year: 'numeric' });
}

function balance(partidos: PartidoContextoEuro[]) {
  const v = partidos.filter((p) => p.puntos_regulacion > p.puntos_rival_regulacion).length;
  const e = partidos.filter((p) => p.puntos_regulacion === p.puntos_rival_regulacion).length;
  const d = partidos.filter((p) => p.puntos_regulacion < p.puntos_rival_regulacion).length;
  const n = partidos.length;
  const pf = partidos.reduce((s, p) => s + p.puntos_regulacion, 0);
  const pc = partidos.reduce((s, p) => s + p.puntos_rival_regulacion, 0);
  return { v, e, d, n, pf: n ? pf / n : null, pc: n ? pc / n : null, dif: n ? (pf - pc) / n : null };
}

function ResumenEquipo({ nombre, partidos, temporada }: { nombre: string; partidos: PartidoContextoEuro[]; temporada?: ResumenTemporadaEuro }) {
  const racha = balance(partidos);
  const temp = temporada?.total;
  return <div className="rounded-lg border border-neon-cyan/20 bg-futurista-negro/40 p-3 space-y-2 min-w-0">
    <h4 className="font-semibold truncate">{nombre}</h4>
    <p className="text-xs text-texto-terciario">Ventana mostrada · regulación (V-E-D)</p>
    <p className="font-mono text-sm"><span className="text-neon-verde">{racha.v}</span>-{racha.e}-<span className="text-neon-rojo">{racha.d}</span> <span className="text-texto-terciario">/ {racha.n} juegos</span></p>
    <p className="text-xs text-texto-secundario">PF {racha.pf?.toFixed(1) ?? 'N/D'} · PC {racha.pc?.toFixed(1) ?? 'N/D'} · Balance {racha.dif === null ? 'N/D' : `${racha.dif > 0 ? '+' : ''}${racha.dif.toFixed(1)}`}</p>
    {temporada && <div className="pt-2 border-t border-neon-cyan/10">
      <p className="text-xs text-texto-terciario">{temporada.nombre ?? 'Temporada reciente del modelo'} · {temp?.partidos ?? 0} finales previos</p>
      <p className="text-xs text-texto-secundario">Regulación V-E-D {temp?.victorias_regulacion ?? 0}-{temp?.empates_regulacion ?? 0}-{temp?.derrotas_regulacion ?? 0} · PF {temp?.promedio_favor_regulacion?.toFixed(1) ?? 'N/D'} · PC {temp?.promedio_contra_regulacion?.toFixed(1) ?? 'N/D'}</p>
      <p className="text-[11px] text-texto-terciario">Local {temporada.como_local.victorias_regulacion}-{temporada.como_local.empates_regulacion}-{temporada.como_local.derrotas_regulacion} ({temporada.como_local.partidos}) · visitante {temporada.como_visitante.victorias_regulacion}-{temporada.como_visitante.empates_regulacion}-{temporada.como_visitante.derrotas_regulacion} ({temporada.como_visitante.partidos}) · en regulación</p>
    </div>}
  </div>;
}

function TablaEquipo({ partidos }: { partidos: PartidoContextoEuro[] }) {
  if (!partidos.length) return <p className="text-sm text-texto-secundario">Sin finales previos para este filtro.</p>;
  return <div className="overflow-x-auto rounded-lg border border-neon-cyan/10">
    <table className="w-full min-w-[790px] text-xs text-left">
      <thead><tr className="bg-futurista-medio/40 text-texto-terciario uppercase tracking-wide">
        <th className="p-2">Fecha</th><th className="p-2">Sede / rival</th><th className="p-2">Regulación</th><th className="p-2">Q1 · Q2 · Q3 · Q4</th><th className="p-2">OT</th><th className="p-2">Final</th>
      </tr></thead>
      <tbody>{partidos.map((p) => {
        const resultado = p.resultado_regulacion ?? (p.puntos_regulacion > p.puntos_rival_regulacion ? 'V' : p.puntos_regulacion < p.puntos_rival_regulacion ? 'D' : 'E');
        const cuartos = p.cuartos?.length === 4 ? p.cuartos.map((q) => `${q.equipo}-${q.rival}`).join(' · ') : 'N/D';
        const ot = p.puntos_ot !== undefined && p.puntos_rival_ot !== undefined
          ? (p.puntos_ot || p.puntos_rival_ot ? `${p.puntos_ot}-${p.puntos_rival_ot}` : '—') : 'N/D';
        const final = p.puntos_finales !== undefined && p.puntos_rival_finales !== undefined ? `${p.puntos_finales}-${p.puntos_rival_finales}` : 'N/D';
        return <tr key={p.id} className="border-t border-futurista-medio/50">
          <td className="p-2 whitespace-nowrap">{fechaVisible(p.fecha)}</td>
          <td className="p-2"><span className="text-texto-terciario">{p.como_local ? 'Local' : 'Visitante'} vs.</span> {p.rival}</td>
          <td className="p-2 whitespace-nowrap"><span className={resultado === 'V' ? 'text-neon-verde' : resultado === 'D' ? 'text-neon-rojo' : 'text-texto-principal'}>{p.puntos_regulacion}-{p.puntos_rival_regulacion} ({resultado})</span></td>
          <td className="p-2 whitespace-nowrap font-mono">{cuartos}</td><td className="p-2 font-mono">{ot}</td><td className="p-2 font-mono">{final}</td>
        </tr>;
      })}</tbody>
    </table>
  </div>;
}

export function SeccionHistorialEuroliga({
  equipos, local, visitante, corte,
}: { equipos: Record<string, EquipoContexto>; local: string; visitante: string; corte?: string | null }) {
  const [expandido, setExpandido] = useState(true);
  const [cantidad, setCantidad] = useState(10);
  const [sede, setSede] = useState<Sede>('TODOS');
  const id = useId();
  const contextoLocal = equipoContexto(equipos, local);
  const contextoVisitante = equipoContexto(equipos, visitante);
  const filtrar = (datos: PartidoContextoEuro[]) => datos
    .filter((p) => sede === 'TODOS' || p.como_local === (sede === 'LOCAL'))
    .slice(0, cantidad);
  const recientesLocal = filtrar(contextoLocal.recientes);
  const recientesVisitante = filtrar(contextoVisitante.recientes);

  return <Tarjeta className="space-y-4" padding="md">
    <button type="button" onClick={() => setExpandido((v) => !v)} className="w-full flex items-center justify-between gap-3 text-left" aria-expanded={expandido} aria-controls={id}>
      <span className="flex items-center gap-2 min-w-0"><History className="w-5 h-5 text-neon-cyan shrink-0" /><span><h3 className="text-lg font-futurista">Historial detallado Euroliga</h3><span className="block text-xs text-texto-terciario">Regulación, cuartos y OT por separado · corte {corte ?? 'N/D'}</span></span></span>
      {expandido ? <ChevronUp className="w-5 h-5 shrink-0" /> : <ChevronDown className="w-5 h-5 shrink-0" />}
    </button>
    {expandido && <div id={id} className="space-y-4">
      <p className="text-xs text-texto-secundario">Finales Euroliga estrictamente anteriores a la fecha del partido. Los filtros y promedios son descriptivos; no se convierten en probabilidades ni se contrastan con la línea. La regulación puede empatar; el marcador final puede diferir por prórroga.</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <ResumenEquipo nombre={local} partidos={recientesLocal} temporada={contextoLocal.temporada_resumen} />
        <ResumenEquipo nombre={visitante} partidos={recientesVisitante} temporada={contextoVisitante.temporada_resumen} />
      </div>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <label className="flex items-center gap-2">Mostrar <select aria-label="Cantidad de partidos" className="bg-futurista-negro border border-neon-cyan/30 rounded px-2 py-1" value={cantidad} onChange={(e) => setCantidad(Number(e.target.value))}><option value={10}>10</option><option value={25}>25</option><option value={50}>50</option></select></label>
        <label className="flex items-center gap-2">Sede <select aria-label="Sede del equipo" className="bg-futurista-negro border border-neon-cyan/30 rounded px-2 py-1" value={sede} onChange={(e) => setSede(e.target.value as Sede)}><option value="TODOS">Todas</option><option value="LOCAL">Equipo local</option><option value="VISITANTE">Equipo visitante</option></select></label>
        <span className="text-xs text-texto-terciario">Disponibles: {contextoLocal.recientes.length} / {contextoVisitante.recientes.length} (máximo 50 por equipo)</span>
      </div>
      <div className="space-y-5"><section className="space-y-2"><h4 className="font-semibold">{local} <span className="text-xs font-normal text-texto-terciario">({recientesLocal.length} partidos)</span></h4><TablaEquipo partidos={recientesLocal} /></section>
        <section className="space-y-2"><h4 className="font-semibold">{visitante} <span className="text-xs font-normal text-texto-terciario">({recientesVisitante.length} partidos)</span></h4><TablaEquipo partidos={recientesVisitante} /></section></div>
    </div>}
  </Tarjeta>;
}
