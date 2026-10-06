/** Navegación directa de la plataforma personal. */
import { Activity, BarChart3, BookOpen, Settings, Target } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useDeporte } from '../../contextos/DeporteContext';
import { SelectorDeporte } from '../atomos/SelectorDeporte';

const enlaces = [
  { ruta: '/dashboard', etiqueta: 'Dashboard', Icono: BarChart3 },
  { ruta: '/app', etiqueta: 'NBA', Icono: Target },
  { ruta: '/futbol', etiqueta: 'Fútbol', Icono: Activity },
  { ruta: '/bitacora', etiqueta: 'Bitácora', Icono: BookOpen },
  { ruta: '/configuracion', etiqueta: 'Configuración', Icono: Settings },
];

export function Encabezado() {
  const navegar = useNavigate();
  const { pathname } = useLocation();
  const { esFutbol } = useDeporte();

  return (
    <header className="border-b border-neon-cyan/20 bg-futurista-oscuro">
      <div className="contenedor py-4 flex flex-wrap items-center justify-between gap-4">
        <button type="button" onClick={() => navegar('/dashboard')} className="flex items-center gap-3 text-texto-principal" aria-label="AnalyticsPredict, ir al dashboard">
          <Activity className="w-8 h-8 text-neon-cyan" />
          <span className="font-futurista text-xl font-bold tracking-wider">AnalyticsPredict</span>
        </button>
        <nav aria-label="Navegación principal" className="flex flex-wrap items-center gap-2">
          {enlaces.map(({ ruta, etiqueta, Icono }) => (
            <button key={ruta} type="button" onClick={() => navegar(ruta)} className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-semibold border ${pathname === ruta ? 'border-neon-cyan text-neon-cyan' : 'border-neon-cyan/20 text-texto-secundario'}`}>
              <Icono className="w-4 h-4" />{etiqueta}
            </button>
          ))}
          <SelectorDeporte tamaño="sm" className="hidden sm:flex" onChangeDeporte={(deporte) => navegar(deporte === 'NBA' ? '/app' : '/futbol')} />
        </nav>
        <span className="sr-only">Deporte actual: {esFutbol ? 'Fútbol' : 'NBA'}</span>
      </div>
    </header>
  );
}
