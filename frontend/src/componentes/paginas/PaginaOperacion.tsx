import { useEffect, useState } from 'react';
import { Encabezado } from '../organismos/Encabezado';
import { clienteAPI } from '../../servicios/api';

type Serie = { n: number; ultimo_final: string | null };
type Estado = {
  observado_en: string;
  nba: Serie; futbol: Serie;
  modelo_nba: { estado: string; version?: number; equipos?: number; ultimo_dato?: string };
  capturas_futbol: { lotes: number | null; observado_en: string | null };
  prospectiva: { congeladas: number | null; resueltas: number | null; estado: string };
  predictor_ml_futbol: { estado: string; motivo: string };
  notas: string[];
};
const fecha = (valor?: string | null) => !valor ? 'N/D' : /^\d{4}-\d{2}-\d{2}$/.test(valor)
  ? valor : new Date(valor).toLocaleString('es-CO');

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
        <section className="border border-neon-cyan/20 rounded p-4"><h2 className="font-bold">NBA</h2><p>{estado.nba.n} partidos · último final: {fecha(estado.nba.ultimo_final)}</p><p>Modelo: {estado.modelo_nba.estado} · versión {estado.modelo_nba.version ?? 'N/D'} · {estado.modelo_nba.equipos ?? 'N/D'} equipos</p><p>Último dato de entrenamiento: {estado.modelo_nba.ultimo_dato ?? 'N/D'}</p></section>
        <section className="border border-neon-cyan/20 rounded p-4"><h2 className="font-bold">Fútbol</h2><p>{estado.futbol.n} partidos · último final: {fecha(estado.futbol.ultimo_final)}</p><p>Capturas: {estado.capturas_futbol.lotes ?? 'N/D'} · última observación: {fecha(estado.capturas_futbol.observado_en)}</p><p>Modelo ML: no cargado desde BD. El análisis estadístico no equivale a un modelo entrenado activo.</p></section>
        <section className="border border-neon-cyan/20 rounded p-4"><h2 className="font-bold">Seguimiento prospectivo</h2><p>{estado.prospectiva.congeladas ?? 'N/D'} predicciones congeladas · {estado.prospectiva.resueltas ?? 'N/D'} resultados acreditados</p><p>{estado.prospectiva.estado === 'ALMACEN_NO_INSTALADO' ? 'Seguimiento aún no instalado' : estado.prospectiva.estado === 'ESPERANDO_OUTCOMES' ? 'Esperando resultados posteriores' : estado.prospectiva.estado === 'SIN_CAPTURAS' ? 'Sin predicciones congeladas' : 'Evaluación pendiente'}</p></section>
      </div>
      <ul className="list-disc pl-5 text-texto-secundario">{estado.notas.map(nota => <li key={nota}>{nota}</li>)}</ul>
    </>}
  </main></>;
}
