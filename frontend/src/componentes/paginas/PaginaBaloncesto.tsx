/** Una sola pantalla; cada liga monta exclusivamente su motor y su estado. */
import { lazy, Suspense } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Encabezado } from '../organismos/Encabezado';
import { leerLigaBaloncesto } from '../../utilidades/ligasBaloncesto';

const ModuloNBA = lazy(async () => ({ default: (await import('./PaginaPrincipal')).PaginaPrincipal }));
const ModuloWNBA = lazy(async () => ({ default: (await import('./PaginaWnba')).ModuloWnba }));
const ModuloEuroliga = lazy(async () => ({ default: (await import('./PaginaEuroliga')).ModuloEuroliga }));

export function PaginaBaloncesto() {
  const [params, setParams] = useSearchParams();
  const liga = leerLigaBaloncesto(`?${params}`);
  const cambiarLiga = (valor: string) => {
    const siguientes = new URLSearchParams(params);
    siguientes.set('liga', valor);
    siguientes.delete('tab');
    siguientes.delete('equipo');
    siguientes.delete('analisis');
    siguientes.delete('lado');
    setParams(siguientes);
  };

  return <div className="min-h-screen flex flex-col">
    <Encabezado />
    <main className="flex-1 contenedor py-6 lg:py-8 min-w-0">
      <section className="mb-6 tarjeta p-5 flex flex-wrap items-center justify-between gap-4" aria-label="Baloncesto y liga activa">
        <div>
          <h1 className="text-2xl font-futurista text-texto-principal">Baloncesto</h1>
          <p className="text-sm text-texto-secundario mt-2">Una misma pantalla de análisis. Datos y predictor propios para cada liga.</p>
        </div>
        <label className="block text-xs font-semibold uppercase tracking-wider text-texto-secundario w-full sm:w-52">
          Liga
          <select className="input-base mt-2 w-full" value={liga} onChange={e => cambiarLiga(e.target.value)}>
            <option value="nba">NBA</option>
            <option value="euroliga">Euroliga</option>
            <option value="wnba">WNBA</option>
          </select>
        </label>
      </section>
      <Suspense fallback={<p role="status">Cargando {liga === 'nba' ? 'NBA' : liga === 'wnba' ? 'WNBA' : 'Euroliga'}…</p>}>
        {liga === 'nba' ? <ModuloNBA key="nba" /> : liga === 'wnba' ? <ModuloWNBA key="wnba" /> : <ModuloEuroliga key="euroliga" />}
      </Suspense>
    </main>
    <footer className="border-t border-neon-cyan/10 bg-futurista-negro/80">
      <div className="contenedor py-4 flex flex-wrap justify-between gap-2 text-xs text-texto-terciario">
        <p>AnalyticsPredict · Baloncesto · {liga === 'nba' ? 'NBA' : liga === 'wnba' ? 'WNBA' : 'Euroliga'}</p>
        <p>Análisis exploratorio; eficacia no certificada.</p>
      </div>
    </footer>
  </div>;
}
