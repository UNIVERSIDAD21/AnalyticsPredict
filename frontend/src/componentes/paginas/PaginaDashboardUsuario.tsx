/** Dashboard personal de NBA y fútbol, sin indicadores de cuenta o plan. */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Encabezado } from '../organismos';
import { Boton, Spinner } from '../atomos';
import { obtenerResumenApuestas } from '../../servicios/bitacora';
import { obtenerResumenCalidad1x2, type ResumenCalidad1x2Futbol } from '../../servicios/futbol/metricas';

type Segmento = { deporte: string; total: number; pendientes: number; ganadas: number; perdidas: number; winrate: number | null; roi: number | null; n_pnl_no_evaluable_nba?: number };

export function PaginaDashboardUsuario() {
  const navegar = useNavigate();
  const [segmentos, setSegmentos] = useState<Segmento[]>([]);
  const [calidad, setCalidad] = useState<ResumenCalidad1x2Futbol | null>(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let vigente = true;
    Promise.allSettled([obtenerResumenApuestas(), obtenerResumenCalidad1x2()]).then(([resumen, calidadFutbol]) => {
      if (!vigente) return;
      if (resumen.status === 'fulfilled') {
        const porDeporte = resumen.value.resumen.por_deporte;
        setSegmentos(Array.isArray(porDeporte) ? porDeporte as Segmento[] : []);
      } else {
        setError('No se pudo cargar el resumen de la bitácora.');
      }
      if (calidadFutbol.status === 'fulfilled') setCalidad(calidadFutbol.value);
      setCargando(false);
    });
    return () => { vigente = false; };
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />
      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-futurista text-texto-principal">Dashboard analítico</h1>
          <p className="text-sm text-texto-secundario">Histórico preservado y calidad observada por deporte.</p>
        </div>
        {cargando ? <Spinner /> : <>
          {error && <p role="alert" className="text-neon-amarillo">{error}</p>}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-4" aria-label="Histórico por deporte">
            {segmentos.length ? segmentos.map((dato) => (
              <div key={dato.deporte} className="tarjeta p-6 space-y-2">
                <h2 className="text-lg font-semibold text-texto-principal">{dato.deporte}</h2>
                <p className="text-sm text-texto-secundario">{dato.total} registros · {dato.pendientes} pendientes · {dato.ganadas} ganadas · {dato.perdidas} perdidas</p>
                <p className="text-sm text-texto-secundario">Win rate registrado: {dato.winrate == null ? 'N/D' : `${dato.winrate.toFixed(1)}%`} · ROI conciliable: {dato.roi == null ? 'N/D' : `${dato.roi.toFixed(1)}%`}</p>
                {dato.n_pnl_no_evaluable_nba ? <p className="text-xs text-neon-amarillo">{dato.n_pnl_no_evaluable_nba} registros NBA excluidos del ROI.</p> : null}
              </div>
            )) : <p className="text-texto-secundario">No hay resumen segmentado disponible.</p>}
          </section>
          <p className="text-xs text-neon-amarillo">ROI y ganancia históricos no certificados: hay resultados que no concilian con stake y cuota. No representan rendimiento futuro.</p>
          <section className="tarjeta p-6 space-y-2" aria-label="Calidad fútbol">
            <h2 className="text-lg font-semibold text-texto-principal">Calidad 1X2 fútbol</h2>
            <p className="text-sm text-texto-secundario">{calidad ? `${calidad.finalizadas} finalizadas de ${calidad.total}; ${calidad.ganadas} ganadas y ${calidad.perdidas} perdidas.` : 'Sin medición disponible.'}</p>
            <p className="text-sm text-texto-secundario">Hit rate sin push: {calidad?.hitRateSinPush == null ? 'N/D' : `${calidad.hitRateSinPush.toFixed(2)}%`}</p>
            <p className="text-xs text-texto-terciario">La madurez de fútbol se evalúa por mercado y evidencia; esta tarjeta no implica promoción.</p>
          </section>
        </>}
        <div className="flex flex-wrap gap-3">
          <Boton variante="primario" onClick={() => navegar('/app')}>Análisis NBA</Boton>
          <Boton variante="secundario" onClick={() => navegar('/futbol')}>Fútbol</Boton>
          <Boton variante="secundario" onClick={() => navegar('/bitacora')}>Bitácora</Boton>
          <Boton variante="secundario" onClick={() => navegar('/admin/nba-analysis')}>Análisis NBA interno</Boton>
        </div>
      </main>
    </div>
  );
}
