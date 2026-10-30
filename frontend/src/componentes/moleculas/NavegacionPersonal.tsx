import { NavLink } from 'react-router-dom';

/** Dos tareas del mismo espacio; no mezcla almacenamiento local y registros en BD. */
export function NavegacionPersonal() {
  return <section className="space-y-3" aria-label="Mi espacio personal">
    <nav aria-label="Secciones de Mi espacio" className="flex flex-wrap gap-2">
      {[['/mis-analisis', 'Mis análisis'], ['/seguimiento', 'Seguimiento']].map(([ruta, nombre]) =>
        <NavLink key={ruta} to={ruta} className={({ isActive }) =>
          `rounded-lg border px-4 py-2 text-sm font-semibold ${isActive ? 'border-neon-cyan text-neon-cyan' : 'border-neon-cyan/20 text-texto-secundario'}`}>
          {nombre}
        </NavLink>)}
    </nav>
    <p className="text-sm text-texto-secundario">Mis análisis conserva copias y notas en este navegador. Seguimiento reúne los registros y resultados de la base de datos.</p>
  </section>;
}
