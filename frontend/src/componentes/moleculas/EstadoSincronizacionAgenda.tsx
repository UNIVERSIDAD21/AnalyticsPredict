import { useEffect, useState } from 'react';
import { clienteAPI, extraerMensajeError } from '../../servicios/api';

interface Estado {
  estado: string;
  fuentes_verificadas_en?: string | null;
  cambio_guardado_en?: string | null;
  detalle?: string;
  cobertura?: { competicion: string; hasta_solicitado: string; futuros_con_hora: number; ultimo_inicio_publicado: string | null; incidencias: number }[];
}
const fecha = (v?: string | null) => v ? new Date(v).toLocaleString('es-CO', { timeZone: 'America/Bogota' }) + ' COT' : 'sin acreditar';

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
  return <details className="min-w-0 rounded-xl border border-white/10 p-3 text-xs text-texto-secundario">
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
      {estado?.cobertura?.map(c => <p key={c.competicion}><strong>{c.competicion}</strong>: {c.futuros_con_hora} encuentros con hora hasta {fecha(c.ultimo_inicio_publicado)}; ventana solicitada hasta {c.hasta_solicitado}; {c.incidencias} incidencias. Publicación íntegra no acreditada.</p>)}
    </div>
  </details>;
}
