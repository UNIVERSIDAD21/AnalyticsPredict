import { useRef, useState } from 'react';
import { Archive, Download, Upload, CheckCircle2 } from 'lucide-react';
import { descargar } from '../../servicios/cuadernoLocal';
import { aplicarRestauracion, crearCopiaRecuperacion, crearRespaldo, LIMITE_ARCHIVO_RESPALDO, prepararRestauracion, type PlanRestauracion } from '../../servicios/respaldoPersonal';

const nombreRespaldo = (prefijo: string) => `${prefijo}-${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
export function RespaldoPersonal() {
  const archivo = useRef<HTMLInputElement>(null), lectura = useRef(0);
  const [plan, setPlan] = useState<PlanRestauracion | null>(null), [texto, setTexto] = useState('');
  const [apariencia, setApariencia] = useState(false), [cargando, setCargando] = useState(false);
  const [error, setError] = useState(''), [mensaje, setMensaje] = useState('');
  const fallo = (e: unknown) => setError(e instanceof Error ? e.message : 'No se pudo completar la operación.');
  const exportar = () => {
    try {
      descargar(nombreRespaldo('respaldo-personal-analyticspredict'), JSON.stringify(crearRespaldo(), null, 2));
      setError(''); setMensaje('Archivo de respaldo preparado. Consérvalo en una carpeta de tu PC.');
    } catch (e) { fallo(e); }
  };
  const leerArchivo = async (file: File | undefined) => {
    const turno = ++lectura.current;
    setError(''); setMensaje(''); setPlan(null); setTexto('');
    if (!file) return;
    setCargando(true);
    try {
      if (file.size > LIMITE_ARCHIVO_RESPALDO) throw new Error('El archivo supera los 12 MB permitidos.');
      const contenido = await file.text();
      if (turno !== lectura.current) return;
      const siguiente = prepararRestauracion(contenido, apariencia);
      setTexto(contenido); setPlan(siguiente);
    } catch (e) { if (turno === lectura.current) fallo(e); }
    finally { if (turno === lectura.current) setCargando(false); }
  };
  const cambiarApariencia = (valor: boolean) => {
    setApariencia(valor); setError('');
    if (texto) { try { setPlan(prepararRestauracion(texto, valor)); } catch (e) { setPlan(null); fallo(e); } }
  };
  const restaurar = () => {
    if (!plan) return;
    try {
      descargar(nombreRespaldo('antes-de-restaurar-analyticspredict'), JSON.stringify(crearRespaldo(), null, 2));
      aplicarRestauracion(plan);
      setMensaje(`Respaldo incorporado: ${plan.nuevas} consultas y ${plan.favoritosNuevos} favoritos nuevos. Tus entradas anteriores se conservaron.`);
      setPlan(null); setTexto(''); setError('');
    } catch (e) { fallo(e); }
  };
  return <section className="cuaderno-respaldo tarjeta" aria-label="Respaldo personal">
    <div className="cuaderno-respaldo-info"><span className="cuaderno-icono"><Archive size={22} aria-hidden="true" /></span><div>
      <h2>Tu trabajo, también fuera del navegador</h2>
      <p>Un archivo para tus consultas, notas, favoritos y apariencia. Puedes recuperarlo en otro navegador de este PC.</p>
    </div></div>
    <div className="cuaderno-acciones">
      <button type="button" className="cuaderno-boton cuaderno-boton-acento" onClick={exportar}><Download size={16} aria-hidden="true" />Crear respaldo</button>
      <button type="button" className="cuaderno-boton" disabled={cargando} onClick={() => archivo.current?.click()}><Upload size={16} aria-hidden="true" />{cargando ? 'Leyendo archivo…' : 'Restaurar archivo'}</button>
      <input ref={archivo} type="file" accept=".json,application/json" className="sr-only" tabIndex={-1} aria-label="Archivo de respaldo personal"
        onChange={e => { const file = e.currentTarget.files?.[0]; e.currentTarget.value = ''; void leerArchivo(file); }} />
    </div>
    {mensaje && <p className="cuaderno-aviso cuaderno-exito" role="status"><CheckCircle2 size={18} aria-hidden="true" />{mensaje}</p>}
    {error && <div className="cuaderno-aviso cuaderno-error" role="alert"><p>{error}</p><button type="button" className="cuaderno-enlace" onClick={() => {
      try { descargar(nombreRespaldo('recuperacion-personal'), JSON.stringify(crearCopiaRecuperacion(), null, 2)); setMensaje('Copia de recuperación preparada. Conserva el archivo original para revisarlo.'); }
      catch (e) { fallo(e); }
    }}>Guardar copia de recuperación de mis datos actuales</button>{texto && <button type="button" className="cuaderno-enlace" onClick={() => {
      try { setPlan(prepararRestauracion(texto, apariencia)); setError(''); } catch (e) { fallo(e); }
    }}>Actualizar vista previa</button>}</div>}
    {plan && <div className="cuaderno-importacion" aria-label="Vista previa de restauración">
      <div><h3>Esto se incorporará a tu espacio</h3><p>{plan.origen}{plan.creadoEn ? ` · ${new Date(plan.creadoEn).toLocaleString('es-CO', { timeZone: 'America/Bogota' })}` : ''}</p></div>
      <dl className="cuaderno-resumen-importacion"><div><dt>Consultas nuevas</dt><dd>{plan.nuevas}</dd></div><div><dt>Favoritos nuevos</dt><dd>{plan.favoritosNuevos}</dd></div><div><dt>Ya presentes</dt><dd>{plan.repetidas}</dd></div><div><dt>Versiones locales conservadas</dt><dd>{plan.conflictos}</dd></div></dl>
      <p>Las consultas con el mismo identificador conservan su versión actual, incluidas sus notas. No se borran entradas ni se recalculan resultados.</p>
      <label className="cuaderno-checkbox"><input type="checkbox" checked={apariencia} onChange={e => cambiarApariencia(e.target.checked)} />Usar también la apariencia del respaldo, si la contiene</label>
      <p className="cuaderno-ayuda">Antes de incorporar, se prepara una descarga con tus datos actuales. Guarda ese archivo para tener una copia adicional.</p>
      <div className="cuaderno-acciones"><button type="button" className="cuaderno-boton cuaderno-boton-acento" onClick={restaurar} disabled={!plan.nuevas && !plan.favoritosNuevos && !plan.aplicarApariencia}>Incorporar respaldo</button>
        <button type="button" className="cuaderno-boton" onClick={() => { lectura.current++; setPlan(null); setTexto(''); setError(''); }}>Cancelar</button></div>
    </div>}
  </section>;
}
