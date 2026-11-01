import { useEffect, useState } from 'react';
import { cargarPersonal, importarNavegador, prepararImportacionNavegador, recuperarPersonal, respaldarPersonal, type PlanNavegador } from '../../servicios/almacenPersonal';
import { cachePersonal } from '../../servicios/personalCache';
import { descargar } from '../../servicios/cuadernoLocal';
import { crearCopiaRecuperacion, crearRespaldo } from '../../servicios/respaldoPersonal';

export function AlmacenPersonal() {
  const [, setRevision] = useState(0), [error, setError] = useState(''), [mensaje, setMensaje] = useState('');
  const [ocupado, setOcupado] = useState(false), [plan, setPlan] = useState<PlanNavegador | null>(null);
  const fallo = (e: unknown) => setError(e instanceof Error ? e.message : 'Almacén no disponible. Tus originales se conservan.');
  useEffect(() => {
    const actualizar = () => setRevision(n => n + 1);
    const leer = () => { void cargarPersonal().then(() => setError('')).catch(fallo); };
    leer(); window.addEventListener('focus', leer); window.addEventListener('personal-actualizado', actualizar);
    return () => { window.removeEventListener('focus', leer); window.removeEventListener('personal-actualizado', actualizar); };
  }, []);
  const ejecutar = async (fn: () => Promise<unknown>) => {
    setOcupado(true); setError(''); setMensaje('');
    try { await fn(); } catch (e) { fallo(e); } finally { setOcupado(false); }
  };
  const current = cachePersonal();
  return <section className="tarjeta space-y-3" aria-label="Almacén de este PC">
    <h2 className="text-xl font-semibold">Mis análisis en este PC</h2>
    <p>Las nuevas copias se conservan fuera del navegador y de las versiones de la aplicación. No dependen de la BD deportiva ni se mezclan con Seguimiento.</p>
    {current ? <p role="status">{current.existe ? `${current.datos.cuaderno.length} consultas en el PC · revisión ${current.revision}` : 'Aún no hay consultas en el almacén del PC.'} Las copias anteriores del navegador permanecen sin borrar; puedes incorporarlas abajo.</p> : <p role="status">Comprobando el almacén del PC…</p>}
    <div className="cuaderno-acciones"><button type="button" className="cuaderno-boton" disabled={ocupado} onClick={() => void ejecutar(async () => { setPlan(await prepararImportacionNavegador()); })}>Revisar copias de este navegador</button>
      <button type="button" className="cuaderno-boton" disabled={ocupado || !current?.existe} onClick={() => void ejecutar(async () => { const r = await respaldarPersonal(); setMensaje(`Respaldo privado verificado de la revisión ${r.revision}. Corte: ${r.creadoEn}. Conserva también una copia en otro soporte.`); })}>Respaldar almacén del PC</button>
      <button type="button" className="cuaderno-enlace" disabled={ocupado} onClick={() => void ejecutar(async () => { await cargarPersonal(); setMensaje('Almacén recargado. Revisa cualquier nota que estuviera sin guardar.'); })}>Recargar almacén</button></div>
    {plan && <div className="cuaderno-aviso"><h3>Vista previa del navegador</h3><p>{plan.nuevas} consultas nuevas · {plan.favoritosNuevos} favoritos nuevos · {plan.conflictos} conflictos. Cada ID existente conserva su versión del PC.</p><p>Se prepara una copia de recuperación antes de incorporar. No se borran ni modifican las claves originales del navegador.</p>
      <div className="cuaderno-acciones"><button type="button" className="cuaderno-boton" disabled={ocupado || (plan.nuevas === 0 && plan.favoritosNuevos === 0)} onClick={() => void ejecutar(async () => {
        descargar('antes-de-incorporar-navegador.json', JSON.stringify(crearCopiaRecuperacion(), null, 2));
        descargar('antes-de-incorporar-almacen.json', JSON.stringify(crearRespaldo(), null, 2));
        await importarNavegador(plan); setPlan(null); setMensaje('Copias incorporadas y releídas del almacén del PC. Los originales del navegador se conservaron.');
      })}>Conservar estas copias en el PC</button><button type="button" className="cuaderno-enlace" disabled={ocupado} onClick={() => setPlan(null)}>Cancelar</button></div></div>}
    {mensaje && <p role="status" className="cuaderno-exito">{mensaje}</p>}
    {error && <div role="alert" className="cuaderno-error"><p>{error}</p><button type="button" className="cuaderno-enlace" disabled={ocupado} onClick={() => void ejecutar(async () => { await recuperarPersonal(); setMensaje('Almacén recuperado y contenido verificado.'); })}>Recuperar almacén tras un cierre abrupto</button></div>}
  </section>;
}
