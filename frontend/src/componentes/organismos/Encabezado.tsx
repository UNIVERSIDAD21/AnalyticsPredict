/** Navegación directa de la plataforma personal. */
import { Activity, BarChart3, BookOpen, Settings, Target } from 'lucide-react';
import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDeporte } from '../../contextos/DeporteContext';
import { SelectorDeporte } from '../atomos/SelectorDeporte';
import { leerLigaBaloncesto, rutaBaloncesto } from '../../utilidades/ligasBaloncesto';

const enlaces = [
  { ruta: '/dashboard', etiqueta: 'Dashboard', Icono: BarChart3 },
  { ruta: '/baloncesto', etiqueta: 'Baloncesto', Icono: Target },
  { ruta: '/futbol', etiqueta: 'Fútbol', Icono: Activity },
  { ruta: '/bitacora', etiqueta: 'Bitácora', Icono: BookOpen },
  { ruta: '/configuracion', etiqueta: 'Configuración', Icono: Settings },
  { ruta: '/operacion', etiqueta: 'Estado', Icono: Activity },
];

export function Encabezado() {
  const navegar = useNavigate();
  const { pathname, search } = useLocation();
  const { deporteActivo, cambiarDeporte } = useDeporte();
  useEffect(() => {
    if (pathname === '/baloncesto') cambiarDeporte(leerLigaBaloncesto(search).toUpperCase() as 'NBA' | 'WNBA' | 'EUROLIGA', false);
    else if (pathname.startsWith('/euroliga')) cambiarDeporte('EUROLIGA', false);
    else if (pathname.startsWith('/futbol')) cambiarDeporte('FUTBOL', false);
    else if (pathname === '/app' || pathname.startsWith('/admin/nba')) cambiarDeporte('NBA', false);
  }, [pathname, search, cambiarDeporte]);

  return (
    <header className="border-b border-neon-cyan/20 bg-futurista-oscuro">
      <div className="contenedor py-4 flex flex-wrap items-center justify-between gap-4">
        <button type="button" onClick={() => navegar('/dashboard')} className="flex items-center gap-3 text-texto-principal" aria-label="AnalyticsPredict, ir al dashboard">
          <Activity className="w-8 h-8 text-neon-cyan" />
          <span className="font-futurista text-xl font-bold tracking-wider">AnalyticsPredict</span>
        </button>
        <nav aria-label="Navegación principal" className="flex flex-wrap items-center gap-2">
          {enlaces.map(({ ruta, etiqueta, Icono }) => (
            <button key={ruta} type="button" onClick={() => navegar(ruta === '/baloncesto' ? rutaBaloncesto(deporteActivo === 'EUROLIGA' ? 'euroliga' : deporteActivo === 'WNBA' ? 'wnba' : 'nba') : ruta)} aria-current={pathname === ruta ? 'page' : undefined} className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold border ${pathname === ruta ? 'border-neon-cyan text-neon-cyan' : 'border-neon-cyan/20 text-texto-secundario'}`}>
              <Icono className="w-4 h-4" />{etiqueta}
            </button>
          ))}
          <SelectorDeporte tamaño="sm" className="hidden sm:flex" onChangeDeporte={(deporte) => navegar(deporte === 'FUTBOL' ? '/futbol' : rutaBaloncesto(deporte === 'EUROLIGA' ? 'euroliga' : deporte === 'WNBA' ? 'wnba' : 'nba'))} />
        </nav>
        <span className="sr-only">Deporte actual: {deporteActivo}</span>
      </div>
    </header>
  );
}
