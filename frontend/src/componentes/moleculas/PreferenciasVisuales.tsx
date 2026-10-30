import { useState } from 'react';
type Preferencias = { tema: 'oscuro' | 'claro'; densidad: 'comoda' | 'compacta'; texto: 'normal' | 'grande' };
const CLAVE = 'analyticspredict-visual-v1';
function iniciales(): Preferencias {
  try { const p = JSON.parse(localStorage.getItem(CLAVE) ?? '{}'); return {
    tema: p.tema === 'claro' ? 'claro' : 'oscuro', densidad: p.densidad === 'compacta' ? 'compacta' : 'comoda', texto: p.texto === 'grande' ? 'grande' : 'normal' }; }
  catch { return { tema: 'oscuro', densidad: 'comoda', texto: 'normal' }; }
}
export function PreferenciasVisuales() {
  const [p, setP] = useState(iniciales);
  const [error, setError] = useState('');
  const cambiar = (c: Partial<Preferencias>) => {
    const n = { ...p, ...c }; setP(n);
    Object.assign(document.documentElement.dataset, n);
    try { localStorage.setItem(CLAVE, JSON.stringify(n)); setError(''); }
    catch { setError('La preferencia se aplica solo a esta sesión.'); }
  };
  return <details className="text-sm preferencias-visuales"><summary className="cursor-pointer">Apariencia</summary><div className="flex flex-wrap gap-3 py-3">
    <label>Tema<select aria-label="Tema" className="input-base" value={p.tema} onChange={e => cambiar({ tema: e.target.value as Preferencias['tema'] })}><option value="oscuro">Oscuro</option><option value="claro">Claro</option></select></label>
    <label>Densidad<select aria-label="Densidad" className="input-base" value={p.densidad} onChange={e => cambiar({ densidad: e.target.value as Preferencias['densidad'] })}><option value="comoda">Cómoda</option><option value="compacta">Compacta</option></select></label>
    <label>Texto<select aria-label="Texto" className="input-base" value={p.texto} onChange={e => cambiar({ texto: e.target.value as Preferencias['texto'] })}><option value="normal">Normal</option><option value="grande">Grande</option></select></label>
    {error && <p role="status">{error}</p>}
  </div></details>;
}
