import { useEffect, useState } from 'react';
import { clienteAPI, extraerMensajeError } from '../../servicios/api';

interface Estado {
  estado: string;
  fuentes_verificadas_en?: string | null;
  cambio_guardado_en?: string | null;
  detalle?: string;
  error_actualizacion?: string;
  actualizacion_ligas?: {
    ultimo_ciclo_agendas: { terminado_en: string; estado: string } | null;
    ultimo_ciclo_integral: { terminado_en: string; estado: string } | null;
    ultima_completa_en: string | null;
    ligas: { codigo: string; nombre: string; deporte: string; cambio_en: string | null;
      resultados_hasta: string | null; estadisticas_hasta: string | null;
      verificacion_agenda_en: string | null; estado_agenda: string;
      estadisticas: { estado: string; verificado_en?: string; detalle?: string } }[];
  } | null;
  cobertura?: { competicion: string; hasta_solicitado: string; futuros_con_hora: number; ultimo_inicio_publicado: string | null; incidencias: number }[];
}
const fecha = (v?: string | null) => v ? new Date(v).toLocaleString('es-CO', { timeZone: 'America/Bogota' }) + ' COT' : 'sin acreditar';
const corte = (v: string | null) => !v ? 'N/D' : /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : fecha(v);

export function EstadoSincronizacionAgenda() {
  const [estado, setEstado] = useState<Estado | null>(null);
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    const ctl = new AbortController();
    clienteAPI.get<Estado>('/api/agendas/sincronizacion', { signal: ctl.signal })
      .then(r => { if (!ctl.signal.aborted) setEstado(r.data); })
      .catch(e => { if (!ctl.signal.aborted) setError(extraerMensajeError(e)); });
    return () => ctl.abort();
  }, [revision]);
  const sincronizar = async () => {
    setOcupado(true); setError('');
    try {
      const { data } = await clienteAPI.post<Estado>('/api/agendas/sincronizar');
      setEstado(prev => ({ ...prev, ...data }));
    } catch (e) { setError(extraerMensajeError(e)); }
    finally { setOcupado(false); }
  };
  const actualizacion = estado?.actualizacion_ligas;
  const integral = actualizacion?.ultimo_ciclo_integral;
  const agenda = actualizacion?.ultimo_ciclo_agendas;
  const ultimo = integral && (!agenda || integral.terminado_en >= agenda.terminado_en) ? integral : agenda;
  return <section aria-label="Actualización de ligas" className="min-w-0 rounded-xl border border-white/10 p-3 text-xs text-texto-secundario">
    <p className="break-words"><strong>Última actualización completa de todas las ligas:</strong> {fecha(actualizacion?.ultima_completa_en)}.</p>
    {ultimo && <p className="mt-1 break-words">Última revisión general: {fecha(ultimo.terminado_en)} · {ultimo.estado.replace(/_/g, ' ')}. {ultimo.estado !== 'COMPLETO' && 'Hay ligas o estadísticas pendientes; consulta el detalle.'}</p>}
    {estado?.error_actualizacion && <p role="status">{estado.error_actualizacion}</p>}
    <details className="mt-2">
    <summary className="cursor-pointer">Fuentes y sincronización · {estado?.estado.replace(/_/g, ' ') ?? 'sin consultar'}</summary>
    <div className="mt-3 space-y-3 break-words">
      <p>Última verificación de fuentes: {fecha(estado?.fuentes_verificadas_en)}. Cambios guardados en el último ciclo: {fecha(estado?.cambio_guardado_en)}.</p>
      <p>Actualizar agenda sólo relee la BD. Sincronizar fuentes verifica calendarios y resultados; puede tardar varios minutos. No actualiza modelos.</p>
      <div className="flex flex-wrap gap-4">
        <button type="button" disabled={ocupado || estado?.estado === 'EN_CURSO'} className="text-neon-cyan disabled:opacity-40" onClick={() => void sincronizar()}>Sincronizar fuentes</button>
        <button type="button" className="text-neon-cyan" onClick={() => { setError(''); setRevision(n => n + 1); }}>Consultar estado</button>
      </div>
      {estado?.detalle && <p role="status">{estado.detalle}</p>}
      {error && <p role="alert">{error}</p>}
      {actualizacion && <>
        <p>Último ciclo de calendarios y marcadores: {fecha(actualizacion.ultimo_ciclo_agendas?.terminado_en)}. Las fechas de partidos son cortes guardados, no certifican que estén todos. Sincronizar fuentes no completa todas las estadísticas.</p>
        <ul className="space-y-3" aria-label="Frescura por liga">
          {actualizacion.ligas.map(liga => <li key={`${liga.deporte}:${liga.codigo}`} className="border-t border-white/10 pt-2">
            <strong>{liga.nombre}</strong>
            <p>Agenda verificada: {fecha(liga.verificacion_agenda_en)} · {liga.estado_agenda.replace(/_/g, ' ')}.</p>
            <p>Resultados hasta: {corte(liga.resultados_hasta)}. Estadísticas hasta: {corte(liga.estadisticas_hasta)}.</p>
            <p>Último cambio de datos: {fecha(liga.cambio_en)}. Revisión de estadísticas: {liga.estadisticas.estado.replace(/_/g, ' ')}{liga.estadisticas.verificado_en ? ` · ${fecha(liga.estadisticas.verificado_en)}` : ''}.</p>
            {liga.estadisticas.detalle && <p>{liga.estadisticas.detalle}</p>}
          </li>)}
        </ul>
      </>}
      {estado?.cobertura?.map(c => <p key={c.competicion}><strong>{c.competicion}</strong>: {c.futuros_con_hora} encuentros con hora hasta {fecha(c.ultimo_inicio_publicado)}; ventana solicitada hasta {c.hasta_solicitado}; {c.incidencias} incidencias. Publicación íntegra no acreditada.</p>)}
    </div>
    </details>
  </section>;
}
