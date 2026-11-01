import { useState } from 'react';
import { Link } from 'react-router-dom';
import { descargar, csvSnapshot, type LigaCuaderno } from '../../servicios/cuadernoLocal';
import { guardarConsultaDuradera } from '../../servicios/almacenPersonal';

export function HerramientasConsulta({ titulo, liga, snapshot, tipo = 'resultado' }: {
  titulo: string; liga: LigaCuaderno; snapshot: unknown; tipo?: 'base' | 'resultado';
}) {
  const [estado, setEstado] = useState('');
  const clave = JSON.stringify({ titulo, liga, snapshot, tipo });
  const [guardada, setGuardada] = useState<{ id: string; clave: string } | null>(null);
  const yaGuardada = guardada?.clave === clave;
  const [ocupado, setOcupado] = useState(false);
  const ejecutar = (accion: () => void) => { try { accion(); } catch (e) { setEstado(e instanceof Error ? e.message : 'No se pudo completar.'); } };
  return <section className="herramientas-consulta flex flex-wrap gap-3 items-center text-sm" aria-label="Conservar consulta">
    <button type="button" className="boton-secundario" disabled={ocupado || yaGuardada} onClick={() => {
      setOcupado(true); setEstado('Confirmando el guardado en este PC…');
      void guardarConsultaDuradera({ titulo, liga, snapshot, tipo }).then(entrada => { setGuardada({ id: entrada.id, clave }); setEstado('Copia guardada y verificada en Mis análisis de este PC. No se registró una apuesta.'); })
        .catch(e => setEstado(e instanceof Error ? e.message : 'No se confirmó el guardado. Conserva el resultado con Exportar JSON.')).finally(() => setOcupado(false));
    }}>{ocupado ? 'Guardando…' : 'Guardar consulta'}</button>
    {guardada && yaGuardada && <Link className="text-neon-cyan underline" to={`/mis-analisis?entrada=${encodeURIComponent(guardada.id)}`}>Abrir en mis análisis →</Link>}
    <button type="button" onClick={() => ejecutar(() => descargar('consulta-analyticspredict.json', JSON.stringify({ formato: 'consulta-exportada-v1', titulo, liga, tipo, snapshot }, null, 2)))}>Exportar JSON</button>
    <button type="button" onClick={() => ejecutar(() => descargar('consulta-analyticspredict.csv', csvSnapshot({ titulo, liga, tipo, snapshot }), 'text/csv'))}>Exportar CSV</button>
    <button type="button" onClick={() => window.print()}>Imprimir</button>
    <p role="status" className="w-full text-texto-secundario">{estado}</p>
  </section>;
}
