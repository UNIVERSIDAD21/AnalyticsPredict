import { useEffect, useState } from 'react';
import { aplicarPreferencias, CLAVE_VISUAL, leerPreferencias, type PreferenciasVisualesLocal as Preferencias } from '../../servicios/preferenciasVisuales';
export function PreferenciasVisuales() {
  const [p, setP] = useState(leerPreferencias);
  const [error, setError] = useState('');
  const cambiar = (c: Partial<Preferencias>) => {
    const n = { ...p, ...c }; setP(n);
    aplicarPreferencias(n);
    try { localStorage.setItem(CLAVE_VISUAL, JSON.stringify(n)); setError(''); window.dispatchEvent(new Event('preferencias-visuales-actualizadas')); }
    catch { setError('La preferencia se aplica solo a esta sesión.'); }
  };
  useEffect(() => {
    const actualizar = () => { const actuales = leerPreferencias(); setP(actuales); aplicarPreferencias(actuales); };
    window.addEventListener('preferencias-visuales-actualizadas', actualizar);
    window.addEventListener('storage', actualizar);
    return () => { window.removeEventListener('preferencias-visuales-actualizadas', actualizar); window.removeEventListener('storage', actualizar); };
  }, []);
  return <details className="text-sm preferencias-visuales"><summary className="cursor-pointer">Apariencia</summary><div className="flex flex-wrap gap-3 py-3">
    <label>Tema<select aria-label="Tema" className="input-base" value={p.tema} onChange={e => cambiar({ tema: e.target.value as Preferencias['tema'] })}><option value="oscuro">Oscuro</option><option value="claro">Claro</option></select></label>
    <label>Densidad<select aria-label="Densidad" className="input-base" value={p.densidad} onChange={e => cambiar({ densidad: e.target.value as Preferencias['densidad'] })}><option value="comoda">Cómoda</option><option value="compacta">Compacta</option></select></label>
    <label>Texto<select aria-label="Texto" className="input-base" value={p.texto} onChange={e => cambiar({ texto: e.target.value as Preferencias['texto'] })}><option value="normal">Normal</option><option value="grande">Grande</option></select></label>
    {error && <p role="status">{error}</p>}
  </div></details>;
}
