import { useEffect, useRef, useState } from 'react';
import { RefreshCw, Database } from 'lucide-react';
import { clienteAPI, extraerMensajeError } from '../../servicios/api';
import type { EstadoActualizacion } from '../../tipos/actualizacionLigas';
import { ResumenActualizacion, TableroActualizacionLigas } from './TableroActualizacionLigas';
import { fechaActualizacion, estadoActualizacionLegible } from '../../utilidades/actualizacionLigas';
import './actualizacionLigas.css';

export function EstadoSincronizacionAgenda({ vista = 'resumen' }: { vista?: 'resumen' | 'tablero' }) {
  const solicitando = useRef(false);
  const [estado, setEstado] = useState<EstadoActualizacion | null>(null);
  const [error, setError] = useState('');
  const [ocupado, setOcupado] = useState(false);
  const [revision, setRevision] = useState(0);
  const pendiente = useRef<{ anterior?: string; desde: number } | null>(null);
  useEffect(() => {
    const ctl = new AbortController();
    clienteAPI.get<EstadoActualizacion>('/api/agendas/sincronizacion', { signal: ctl.signal })
      .then(r => {
        if (ctl.signal.aborted) return;
        if (pendiente.current && r.data.iniciado_en === pendiente.current.anterior && r.data.estado !== 'EN_CURSO' && r.data.estado !== 'SOLICITADA') {
          if (Date.now() - pendiente.current.desde < 60_000) return;
          pendiente.current = null;
          setError('No se confirmó el inicio. Consulta el estado antes de volver a solicitar la actualización.');
          setEstado(r.data);
          return;
        }
        pendiente.current = null;
        setError('');
        setEstado(r.data);
      })
      .catch(e => { if (!ctl.signal.aborted) setError(extraerMensajeError(e)); });
    return () => ctl.abort();
  }, [revision]);
  const ejecutando = estado?.estado === 'EN_CURSO' || estado?.estado === 'SOLICITADA';
  const pausada = estado?.estado === 'PAUSADA_CALIDAD';
  useEffect(() => {
    if (!ejecutando) return;
    const timer = window.setInterval(() => setRevision(n => n + 1), 3000);
    return () => window.clearInterval(timer);
  }, [ejecutando]);
  const sincronizar = async () => {
    if (solicitando.current) return;
    solicitando.current = true;
    setOcupado(true); setError('');
    try {
      pendiente.current = { anterior: estado?.iniciado_en, desde: Date.now() };
      const { data } = await clienteAPI.post<EstadoActualizacion>('/api/agendas/sincronizar');
      setEstado(prev => ({ ...prev, ...data }));
    } catch (e) { pendiente.current = null; setError(extraerMensajeError(e)); }
    finally { solicitando.current = false; setOcupado(false); }
  };
  const etapa = { AGENDA: 'Agenda', RESULTADOS: 'Resultados', ESTADISTICAS: 'Estadísticas', COBERTURA: 'Cobertura' }[estado?.etapa ?? ''];
  const activo = ocupado || ejecutando;
  return <section aria-label="Actualización de ligas" className={`actualizacion-panel ${vista === 'resumen' ? 'actualizacion-compacto' : ''}`}>
    <div className="actualizacion-cabecera">
      <div>
        <p className="actualizacion-eyebrow"><Database size={14} aria-hidden="true" /> Centro de datos · operación manual</p>
        {vista === 'tablero' ? <h1>Actualización de ligas</h1> : <h2>Estado de tus datos</h2>}
        <p className="actualizacion-subtitulo">Agenda, resultados y estadísticas, con sus pendientes a la vista.</p>
      </div>
      <div className="actualizacion-acciones">
        <button type="button" disabled={activo || pausada || !estado} onClick={() => void sincronizar()} className="actualizacion-boton actualizacion-boton-principal">
          <RefreshCw size={15} aria-hidden="true" />{ocupado ? 'Solicitando actualización…' : 'Actualizar todas las ligas'}
        </button>
        <button type="button" disabled={ocupado} className="actualizacion-boton" onClick={() => { setError(''); setRevision(n => n + 1); }}>Consultar estado</button>
      </div>
    </div>
    {error && <p role="alert" className="actualizacion-aviso actualizacion-error">{error}{estado && ' Se conserva el último estado leído; no es una verificación nueva.'}</p>}
    {estado?.error_actualizacion && <p role="status" className="actualizacion-aviso">{estado.error_actualizacion}</p>}
    {!estado && !error && <p role="status" className="actualizacion-aviso">Consultando el estado guardado…</p>}
    {ejecutando && <div role="status" className="actualizacion-aviso actualizacion-en-curso">
      <p><strong>{etapa ? `${etapa} · ` : ''}</strong>{estado?.detalle ?? 'Solicitando actualización…'}{estado?.progreso && ` · ${estado.progreso.ligas_revisadas}/${estado.progreso.ligas_total} competiciones revisadas.`}</p>
      {estado?.progreso && estado.progreso.ligas_total > 0 && <progress aria-label="Competiciones revisadas en el ciclo" value={estado.progreso.ligas_revisadas} max={estado.progreso.ligas_total} />}
      <p>La ejecución aún no acredita una actualización completa.</p>
    </div>}
    {pausada && <p role="status" className="actualizacion-aviso">La actualización está pausada mientras se verifica la calidad de los datos.</p>}
    {(estado?.estado === 'ERROR' || estado?.estado === 'INTERRUMPIDA') && <p role="alert" className="actualizacion-aviso actualizacion-error">{estado.detalle ?? 'La ejecución se interrumpió. Revisa el estado antes de reintentar.'}</p>}
    {estado?.correccion_calidad && <p className="actualizacion-aviso">Corrección estadística · {estado.correccion_calidad.campos_escritos} campos escritos en el ciclo original, {estado.correccion_calidad.campos_acreditados} pasaron el control de coherencia y {estado.correccion_calidad.campos_no_acreditados} quedaron en cuarentena en {estado.correccion_calidad.partidos_en_cuarentena} partidos.</p>}
    <div className="actualizacion-corte">
      <span className={`actualizacion-insignia ${estado?.estado === 'PARCIAL' || pausada ? 'aviso' : ''}`}>{estado ? estadoActualizacionLegible(estado.estado) : 'Sin lectura confirmada'}</span>
      <p>Última revisión general: {fechaActualizacion(estado?.fuentes_verificadas_en ?? estado?.actualizacion_ligas?.ultimo_ciclo_integral?.terminado_en ?? estado?.actualizacion_ligas?.ultimo_ciclo_agendas?.terminado_en)}.</p>
      {(estado?.estado === 'COMPLETO' || estado?.estado === 'PARCIAL') && estado.terminado_en && <p>Ejecución terminada · {fechaActualizacion(estado.terminado_en)}.</p>}
    </div>
    <ResumenActualizacion estado={estado} />
    {vista === 'tablero' ? <TableroActualizacionLigas estado={estado} /> : <a className="actualizacion-enlace" href="/actualizaciones">Abrir tablero de actualización <span aria-hidden="true">↗</span></a>}
  </section>;
}
