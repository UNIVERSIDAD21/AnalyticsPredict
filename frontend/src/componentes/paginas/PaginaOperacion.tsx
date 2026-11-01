import { useCallback, useEffect, useRef, useState } from 'react';
import { Encabezado } from '../organismos/Encabezado';
import { clienteAPI } from '../../servicios/api';
import { InventarioElegibilidad } from '../moleculas/ElegibilidadFutbol';
import type { InventarioElegibilidadFutbol } from '../../tipos/futbol';
import { leerEstadoLocal, type EstadoLocal } from '../../servicios/estadoLocal';
import { descargar } from '../../servicios/cuadernoLocal';

type Serie = { n: number; ultimo_final: string | null; por_fase?: { fase: string; n: number; finales_validos: number; ultimo_final: string | null }[] };
type Inventario = {
  elegibilidad?: InventarioElegibilidadFutbol;
  codigo: string; nombre: string; registros: number; finales_con_marcador: number;
  ultimo_final: string | null; invalidados: number; faltantes_por_campo: Record<string, number>;
  calendario: { estado: string; proximos: number | null; completo_acreditado: boolean; condicionales?: number;
    ultima_comprobacion?: { desde: string; hasta: string; comprobado_utc: string } | null };
  modelo?: { estado: string; version?: string; ultimo_dato?: string; partidos?: number; calibracion: string; alcance?: string };
};
type Estado = {
  frescura_modelo_nba?: { estado: string; motivo?: string; ultimo_dato_artefacto?: string;
    finales_elegibles_nuevos?: number; pretemporada_excluida?: number; criterio?: string };
  competiciones?: { baloncesto: Record<string, Inventario>; futbol: Inventario[];
    ventana_calendario: { desde: string; hasta: string; zona: string }; criterio: string };
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
const campoLegible = (campo: string) => {
  const [lado, ...partes] = campo.split('_');
  const nombres: Record<string, string> = { q1: 'Q1', q2: 'Q2', q3: 'Q3', q4: 'Q4', ot: 'prórroga', total: 'puntos totales', goles_total: 'goles', corners_total: 'córners', disparos_arco: 'tiros al arco' };
  return `${lado === 'local' ? 'Local' : 'Visitante'} · ${nombres[partes.join('_')] ?? partes.join(' ')}`;
};

function DatosCompeticion({ datos }: { datos?: Inventario }) {
  if (!datos) return <p>Inventario: N/D. Actualiza el servicio para consultar esta competición.</p>;
  const faltantes = Object.entries(datos.faltantes_por_campo);
  return <div className="min-w-0 max-w-full mt-3 space-y-2 text-sm">
    <p>{datos.registros} registros · {datos.finales_con_marcador} finales con marcador · {datos.invalidados} invalidados</p>
    <p>Último final registrado: {fecha(datos.ultimo_final)}</p>
    <p>Calendario en BD, próximos tres meses: {datos.calendario.proximos ?? 'N/D'} · cobertura completa no acreditada</p>
    {datos.calendario.condicionales != null && <p>Encuentros condicionales incluidos: {datos.calendario.condicionales}. Solo se disputan si son necesarios.</p>}
    {datos.calendario.ultima_comprobacion && <p>Última comprobación: {fecha(datos.calendario.ultima_comprobacion.comprobado_utc)} · ventana {datos.calendario.ultima_comprobacion.desde} a {datos.calendario.ultima_comprobacion.hasta}</p>}
    <details><summary className="cursor-pointer">Campos faltantes en finales ({datos.finales_con_marcador} registros)</summary>
      {datos.finales_con_marcador === 0 && <p>Sin muestra de finales; cero faltantes no acredita cobertura.</p>}
      <ul className="break-words">{faltantes.map(([campo, n]) => <li key={campo}>{campoLegible(campo)}: {n}</li>)}</ul>
    </details>
    {datos.elegibilidad && <InventarioElegibilidad datos={datos.elegibilidad} />}
    {datos.modelo && <>
      <p>Modelo: {datos.modelo.estado} · versión <span className="break-all">{datos.modelo.version ?? 'N/D'}</span></p>
      <p>Último dato de entrenamiento: {datos.modelo.ultimo_dato ?? 'N/D'} · {datos.modelo.partidos ?? 'N/D'} partidos</p>
      <p>Calibración: {datos.modelo.calibracion === 'SIN_CALIBRAR' ? 'RAW / sin calibrar' : 'no verificada'}</p>
      {datos.modelo.alcance && <p>{datos.modelo.alcance}</p>}
    </>}
  </div>;
}

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
      <div className="grid gap-3 md:grid-cols-3">{Object.entries(local.modelos).map(([liga, m]) => <div key={liga} className="min-w-0 rounded border border-neon-cyan/20 p-3 text-sm space-y-1">
        <h3 className="font-semibold">{liga === 'euroliga' ? 'Euroliga' : liga.toUpperCase()}</h3>
        <p>{m.disponible ? `Artefacto disponible · ${m.equipos_disponibles ?? 'N/D'} equipos con soporte` : `N/D · ${m.motivo ?? 'Artefacto no disponible'}`}</p>
        {m.disponible && <><p className="break-all">Versión: {m.modelo_version}</p><p>Corte del ajuste: {m.corte_modelo ?? 'N/D'}</p><p>Muestra de ajuste: {m.muestra_entrenamiento ?? 'N/D'} · {m.minutos_regulacion ?? (liga === 'nba' ? 48 : 40)} min sin OT · RAW</p></>}
      </div>)}</div>
      <p>Base local permite consultar NBA, Euroliga y WNBA cuando su artefacto está disponible. Mis análisis conserva notas, favoritos y copias en el almacén privado de este PC.</p>
      {local.bd.deshabilitada && <p>Agendas, contexto reciente, estadísticas de fútbol y seguimiento en BD: N/D en este modo. No se intenta acceder a Neon.</p>}
      <p className="text-sm text-texto-secundario">{local.limites.join(' ')}</p>
      <div className="flex flex-wrap gap-4 text-sm text-neon-cyan"><a href="/base-local">Abrir Base local</a><a href="/mis-analisis">Abrir Mis análisis</a><button type="button" onClick={() => descargar(`diagnostico-local-${local.observado_en.slice(0, 10)}.json`, JSON.stringify(local, null, 2))}>Descargar diagnóstico local</button></div>
    </section>}
    {estado && <>
      <p className="text-texto-secundario">Consultado: {fecha(estado.observado_en)}{error ? ' · Se conserva la última respuesta; puede estar desactualizada.' : ''}</p>
      {estado.competiciones && <p className="text-sm text-texto-secundario">Calendario local: {fecha(estado.competiciones.ventana_calendario.desde)} a {fecha(estado.competiciones.ventana_calendario.hasta)} ({estado.competiciones.ventana_calendario.zona}). Consultar este panel no descarga datos ni entrena modelos.</p>}
      <div className="grid gap-4 md:grid-cols-2">
        <section className="min-w-0 border border-neon-cyan/20 rounded p-4"><h2 className="font-bold">NBA</h2><p>{estado.nba.n} partidos · último final: {fecha(estado.nba.ultimo_final)}</p><p>Modelo: {estado.modelo_nba.estado} · versión {estado.modelo_nba.version ?? 'N/D'} · {estado.modelo_nba.equipos ?? 'N/D'} equipos</p><p>Último dato de entrenamiento: {estado.modelo_nba.ultimo_dato ?? 'N/D'}</p>
          <ul aria-label="Datos NBA por fase">{estado.nba.por_fase?.map(s => <li key={s.fase}>{fase(s.fase)}: {s.n} registros · {s.finales_validos} finales válidos · último: {fecha(s.ultimo_final)}</li>)}</ul>
          <p>La pretemporada se conserva y analiza por separado; no acredita rendimiento en temporada regular.</p>
          {estado.frescura_modelo_nba && <div className="mt-2 text-sm" aria-label="Frescura del artefacto NBA">
            {estado.frescura_modelo_nba.estado === 'NO_VERIFICABLE'
              ? <p>Frescura del artefacto: N/D. {estado.frescura_modelo_nba.motivo}</p>
              : <><p>Finales posteriores al corte del artefacto, dentro de su alcance: <strong>{estado.frescura_modelo_nba.finales_elegibles_nuevos}</strong>.</p>
                  <p>Pretemporada posterior excluida por diseño: {estado.frescura_modelo_nba.pretemporada_excluida}.</p>
                  <p>{estado.frescura_modelo_nba.criterio}</p></>}
          </div>}
          <DatosCompeticion datos={estado.competiciones?.baloncesto.nba} />
          <p>Calibración: no verificada en esta consulta.</p>
        </section>
        <section className="min-w-0 border border-neon-cyan/20 rounded p-4"><h2 className="font-bold">WNBA</h2>
          <DatosCompeticion datos={estado.competiciones?.baloncesto.wnba} />
        </section>
        <section className="min-w-0 border border-neon-cyan/20 rounded p-4"><h2 className="font-bold">Euroliga</h2>
          <DatosCompeticion datos={estado.competiciones?.baloncesto.euroleague} />
        </section>
        <section className="min-w-0 border border-neon-cyan/20 rounded p-4">
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
          <p>Calibración: no verificada en esta consulta.</p>
          {estado.competiciones && <details className="mt-3"><summary className="cursor-pointer">Datos por competición de fútbol ({estado.competiciones.futbol.length})</summary>
            {estado.competiciones.futbol.map(datos => <section key={datos.codigo} className="mt-3 border-t border-neon-cyan/20 pt-3"><h3 className="font-semibold">{datos.nombre} ({datos.codigo})</h3><DatosCompeticion datos={datos} /></section>)}
          </details>}
        </section>
        <section className="min-w-0 border border-neon-cyan/20 rounded p-4"><h2 className="font-bold">Seguimiento prospectivo</h2><p>{estado.prospectiva.congeladas ?? 'N/D'} predicciones congeladas · {estado.prospectiva.resueltas ?? 'N/D'} resultados registrados</p>
          <p>Resultados con fuente independiente acreditada: {estado.prospectiva.resueltas_independientes ?? 'N/D'}. Registrar un resultado no certifica su independencia ni la calibración.</p>
          <p>{estado.prospectiva.estado === 'ALMACEN_NO_INSTALADO' ? 'Seguimiento aún no instalado' : estado.prospectiva.estado === 'ESPERANDO_OUTCOMES' ? 'Esperando resultados posteriores' : estado.prospectiva.estado === 'SIN_CAPTURAS' ? 'Sin predicciones congeladas' : 'Evaluación pendiente'}</p>
          <ul aria-label="Seguimiento NBA por fase">{estado.prospectiva.por_fase?.map(s => <li key={s.fase}>{fase(s.fase)}: {s.eventos} eventos · {s.congeladas} predicciones · {s.resueltas} resultados</li>)}</ul>
        </section>
      </div>
      {estado.competiciones && <p className="text-sm text-texto-secundario">{estado.competiciones.criterio}</p>}
      <ul className="list-disc pl-5 text-texto-secundario">{estado.notas.map(nota => <li key={nota}>{nota}</li>)}</ul>
    </>}
  </main></>;
}
