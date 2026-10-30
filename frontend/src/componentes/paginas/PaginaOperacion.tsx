import { useCallback, useEffect, useRef, useState } from 'react';
import { Encabezado } from '../organismos/Encabezado';
import { clienteAPI } from '../../servicios/api';
import { leerEstadoLocal, type EstadoLocal } from '../../servicios/estadoLocal';
import { descargar } from '../../servicios/cuadernoLocal';

type Serie = { n: number; ultimo_final: string | null; por_fase?: { fase: string; n: number; finales_validos: number; ultimo_final: string | null }[] };
type Estado = {
  observado_en: string;
  nba: Serie; futbol: Serie;
  modelo_nba: { estado: string; version?: number; equipos?: number; ultimo_dato?: string };
  capturas_futbol: { lotes: number | null; observado_en: string | null };
  prospectiva: { congeladas: number | null; resueltas: number | null; resueltas_independientes?: number | null; estado: string; por_fase?: { fase: string; congeladas: number; eventos: number; resueltas: number; resueltas_independientes?: number }[] };
  predictor_ml_futbol: { estado: string; motivo: string; familias: Record<string, { estado: string; version_id: number | null }>; carga_en_proceso: { estado: string; familias: Record<string, { estado: string; version_id: number | null }> } };
  notas: string[];
};
const fecha = (valor?: string | null) => !valor ? 'N/D' : /^\d{4}-\d{2}-\d{2}$/.test(valor)
  ? valor : new Date(valor).toLocaleString('es-CO', { timeZone: 'America/Bogota' });
const fase = (valor: string) => ({ PRE: 'Pretemporada', REG: 'Temporada regular', POST: 'Postemporada' }[valor] ?? valor);

export function PaginaOperacion() {
  const [local, setLocal] = useState<EstadoLocal | null>(null);
  const [estado, setEstado] = useState<Estado | null>(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);
  const consultaInicial = useRef(false);
  const consultando = useRef(false);
  const actualizar = useCallback(async () => {
    if (consultando.current) return;
    consultando.current = true;
    setCargando(true); setError('');
    try {
      const diagnostico = await leerEstadoLocal(); setLocal(diagnostico);
      if (diagnostico.bd.deshabilitada) setEstado(null);
      else setEstado((await clienteAPI.get<Estado>('/api/operacion/estado')).data);
    }
    catch { setError('No se pudo completar la consulta del estado. La ausencia de respuesta no significa que no haya datos.'); }
    finally { consultando.current = false; setCargando(false); }
  }, []);
  useEffect(() => {
    if (consultaInicial.current) return;
    consultaInicial.current = true;
    void actualizar();
  }, [actualizar]);
  return <><Encabezado /><main id="contenido-principal" tabIndex={-1} className="contenedor py-8 space-y-5 text-texto-principal">
    <h1 className="text-2xl font-bold">Estado del sistema</h1>
    <p className="text-amber-300">Uso exploratorio · rendimiento no certificado</p>
    <button type="button" className="border rounded px-4 py-2" disabled={cargando} onClick={() => void actualizar()}>{cargando ? 'Consultando…' : 'Actualizar estado'}</button>
    {error && <p role="alert">{error}</p>}
    {local && <section className="tarjeta space-y-3" aria-label="Disponibilidad local">
      <h2 className="text-xl font-semibold">Disponibilidad local</h2>
      <p>{local.bd.deshabilitada ? 'Modo base local: la BD está deshabilitada en esta ejecución.' : 'Modo con BD configurada: el diagnóstico de artefactos no comprueba la conexión.'}</p>
      <p className="text-sm text-texto-secundario">Observado: {fecha(local.observado_en)}{error ? ' · Última respuesta recibida; puede estar desactualizada.' : ''}</p>
      <div className="grid gap-3 md:grid-cols-3">{Object.entries(local.modelos).map(([liga, m]) => <section key={liga} className="min-w-0 border border-neon-cyan/20 rounded p-3 space-y-1">
        <h3 className="font-semibold">{liga === 'euroliga' ? 'Euroliga' : liga.toUpperCase()}</h3>
        <p>{m.disponible ? `Artefacto disponible · ${m.equipos_disponibles ?? 'N/D'} equipos con soporte` : 'Artefacto N/D'}</p>
        {m.disponible ? <><p className="break-all">Versión: {m.modelo_version ?? 'N/D'}</p><p>Corte del ajuste: {m.corte_modelo ?? 'N/D'}</p><p>Muestra de ajuste: {m.muestra_entrenamiento ?? 'N/D'} · {m.minutos_regulacion ?? 'N/D'} min sin OT · RAW</p></> : <p>{m.motivo}</p>}
      </section>)}</div>
      <p>Base local permite consultar NBA, Euroliga y WNBA cuando su artefacto está disponible. Mis análisis conserva notas, favoritos y copias en este navegador.</p>
      {local.bd.deshabilitada && <p>Agendas, contexto reciente, estadísticas de fútbol y seguimiento en BD: N/D en este modo. No se intenta acceder a Neon.</p>}
      <p className="text-sm text-texto-secundario">{local.limites.join(' ')}</p>
      <div className="flex flex-wrap gap-4 text-sm text-neon-cyan"><a href="/base-local">Abrir Base local</a><a href="/mis-analisis">Abrir Mis análisis</a><button type="button" onClick={() => descargar(`diagnostico-local-${local.observado_en.slice(0, 10)}.json`, JSON.stringify(local, null, 2))}>Descargar diagnóstico local</button></div>
    </section>}
    {estado && <>
      <p className="text-texto-secundario">Consultado: {fecha(estado.observado_en)}{error ? ' · Se conserva la última respuesta; puede estar desactualizada.' : ''}</p>
      <div className="grid gap-4 md:grid-cols-2">
        <section className="border border-neon-cyan/20 rounded p-4"><h2 className="font-bold">NBA</h2><p>{estado.nba.n} partidos · último final: {fecha(estado.nba.ultimo_final)}</p><p>Modelo: {estado.modelo_nba.estado} · versión {estado.modelo_nba.version ?? 'N/D'} · {estado.modelo_nba.equipos ?? 'N/D'} equipos</p><p>Último dato de entrenamiento: {estado.modelo_nba.ultimo_dato ?? 'N/D'}</p>
          <ul aria-label="Datos NBA por fase">{estado.nba.por_fase?.map(s => <li key={s.fase}>{fase(s.fase)}: {s.n} registros · {s.finales_validos} finales válidos · último: {fecha(s.ultimo_final)}</li>)}</ul>
          <p>La pretemporada se conserva y analiza por separado; no acredita rendimiento en temporada regular.</p>
        </section>
        <section className="border border-neon-cyan/20 rounded p-4">
          <h2 className="font-bold">Fútbol</h2>
          <p>{estado.futbol.n} partidos · último final: {fecha(estado.futbol.ultimo_final)}</p>
          <p>Capturas: {estado.capturas_futbol.lotes ?? 'N/D'} · última observación: {fecha(estado.capturas_futbol.observado_en)}</p>
          <p>Modelo ML: {estado.predictor_ml_futbol.estado === 'SIN_VERSION_ACTIVA' ? 'sin versión activa' : 'versiones registradas; comprobar carga por familia'}.</p>
          <p>La carga se actualiza al solicitar un análisis. El análisis estadístico no equivale a un modelo entrenado activo.</p>
          <ul>{Object.entries(estado.predictor_ml_futbol.familias).map(([familia, modelo]) => {
            const carga = estado.predictor_ml_futbol.carga_en_proceso.familias[familia];
            const coincide = modelo.estado === 'VERIFICADA_PARA_CARGA' && modelo.version_id != null && carga?.estado === 'CARGADO' && carga.version_id === modelo.version_id;
            return <li key={familia}>{familia}: {modelo.estado === 'VERIFICADA_PARA_CARGA' ? 'artefacto verificado' : modelo.estado === 'ARTEFACTO_NO_APTO' ? 'artefacto no apto' : 'sin versión activa'} · versión {modelo.version_id ?? 'N/D'} · {coincide ? 'cargado' : 'no cargado'}</li>;
          })}</ul>
        </section>
        <section className="border border-neon-cyan/20 rounded p-4"><h2 className="font-bold">Seguimiento prospectivo</h2><p>{estado.prospectiva.congeladas ?? 'N/D'} predicciones congeladas · {estado.prospectiva.resueltas ?? 'N/D'} resultados registrados</p>
          <p>Resultados con fuente independiente acreditada: {estado.prospectiva.resueltas_independientes ?? 'N/D'}. Registrar un resultado no certifica su independencia ni la calibración.</p>
          <p>{estado.prospectiva.estado === 'ALMACEN_NO_INSTALADO' ? 'Seguimiento aún no instalado' : estado.prospectiva.estado === 'ESPERANDO_OUTCOMES' ? 'Esperando resultados posteriores' : estado.prospectiva.estado === 'SIN_CAPTURAS' ? 'Sin predicciones congeladas' : 'Evaluación pendiente'}</p>
          <ul aria-label="Seguimiento NBA por fase">{estado.prospectiva.por_fase?.map(s => <li key={s.fase}>{fase(s.fase)}: {s.eventos} eventos · {s.congeladas} predicciones · {s.resueltas} resultados</li>)}</ul>
        </section>
      </div>
      <ul className="list-disc pl-5 text-texto-secundario">{estado.notas.map(nota => <li key={nota}>{nota}</li>)}</ul>
    </>}
  </main></>;
}
