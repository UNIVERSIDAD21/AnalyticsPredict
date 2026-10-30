import { useState } from 'react';
import { guardarConsulta, descargar, csvSnapshot, type LigaCuaderno } from '../../servicios/cuadernoLocal';

export function HerramientasConsulta({ titulo, liga, snapshot, tipo = 'resultado' }: {
  titulo: string; liga: LigaCuaderno; snapshot: unknown; tipo?: 'base' | 'resultado';
}) {
  const [estado, setEstado] = useState('');
  const ejecutar = (accion: () => void) => { try { accion(); } catch (e) { setEstado(e instanceof Error ? e.message : 'No se pudo completar.'); } };
  return <section className="herramientas-consulta flex flex-wrap gap-3 items-center text-sm" aria-label="Conservar consulta">
    <button type="button" className="boton-secundario" onClick={() => ejecutar(() => { guardarConsulta({ titulo, liga, snapshot, tipo }); setEstado('Copia guardada en Mi cuaderno de este navegador. No se registró una apuesta.'); })}>Guardar consulta</button>
    <button type="button" onClick={() => ejecutar(() => descargar('consulta-analyticspredict.json', JSON.stringify({ formato: 'consulta-exportada-v1', titulo, liga, tipo, snapshot }, null, 2)))}>Exportar JSON</button>
    <button type="button" onClick={() => ejecutar(() => descargar('consulta-analyticspredict.csv', csvSnapshot({ titulo, liga, tipo, snapshot }), 'text/csv'))}>Exportar CSV</button>
    <button type="button" onClick={() => window.print()}>Imprimir</button>
    <p role="status" className="w-full text-texto-secundario">{estado}</p>
  </section>;
}
