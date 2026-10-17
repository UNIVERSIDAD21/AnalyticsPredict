import { useEffect, useState } from 'react';
import { Encabezado } from '../organismos/Encabezado';
import { clienteAPI } from '../../servicios/api';

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
  ? valor : new Date(valor).toLocaleString('es-CO');
const fase = (valor: string) => ({ PRE: 'Pretemporada', REG: 'Temporada regular', POST: 'Postemporada' }[valor] ?? valor);

export function PaginaOperacion() {
  const [estado, setEstado] = useState<Estado | null>(null);
  const [error, setError] = useState('');
  const [cargando, setCargando] = useState(false);
  const actualizar = async () => {
    setCargando(true); setError('');
    try { setEstado((await clienteAPI.get<Estado>('/api/operacion/estado')).data); }
    catch { setError('No se pudo consultar el estado. La ausencia de respuesta no significa que no haya datos.'); }
    finally { setCargando(false); }
  };
  useEffect(() => { void actualizar(); }, []);
  return <><Encabezado /><main className="contenedor py-8 space-y-5 text-texto-principal">
    <h1 className="text-2xl font-bold">Estado del sistema</h1>
    <p className="text-amber-300">Uso exploratorio · rendimiento no certificado</p>
    <button type="button" className="border rounded px-4 py-2" disabled={cargando} onClick={() => void actualizar()}>{cargando ? 'Consultando…' : 'Actualizar estado'}</button>
    {error && <p role="alert">{error}</p>}
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
