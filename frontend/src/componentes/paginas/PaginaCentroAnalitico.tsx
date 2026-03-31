import { useEffect } from 'react';
import { Crown, Layers3, LineChart, NotebookPen, Settings2, ShieldCheck, Sparkles, Target } from 'lucide-react';
import { Encabezado } from '../organismos';
import { Boton, Tarjeta } from '../atomos';
import { SelectorDeporte } from '../atomos/SelectorDeporte';
import { useDeporte } from '../../contextos/DeporteContext';
import { useAuth } from '../../contextos/AuthContext';
import { useAccessPolicy } from '../../contextos/AccessPolicyContext';
import { useGateNavigation } from '../../hooks/useGateNavigation';
import { registrarIngresoCentro } from '../../servicios/visitante';
import { registrarEventoProducto } from '../../servicios/productAnalytics';

const navegar = (ruta: string) => {
  if (window.location.pathname === ruta) return;
  window.history.pushState({}, '', ruta);
  window.dispatchEvent(new PopStateEvent('popstate'));
};

export function PaginaCentroAnalitico() {
  const { deporteActivo, esNBA } = useDeporte();
  const { autenticado } = useAuth();
  const { can } = useAccessPolicy();
  const { navegarConGate } = useGateNavigation(navegar);

  useEffect(() => {
    const payloadCentro = {
      autenticado,
      deporteActivo,
      tierHint: can('premium.depth') ? 'PREMIUM' : (autenticado ? 'BASE' : 'INVITADO'),
    };

    registrarEventoProducto('public_center_view', payloadCentro);
    registrarEventoProducto('public_center_viewed', payloadCentro);

    if (!autenticado) {
      registrarIngresoCentro();
    }
  }, [autenticado, deporteActivo, can]);

  const rutaAnalisisPrincipal = esNBA ? '/app' : '/futbol';

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-6">
        <section className="border border-neon-cyan/25 rounded-xl p-6 lg:p-8 bg-futurista-oscuro/40 space-y-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs uppercase tracking-[0.2em] text-neon-cyan">Centro analítico</p>
            <SelectorDeporte
              tamaño="md"
              onChangeDeporte={(deporte) => {
                const rutaDestino = deporte === 'NBA' ? '/app' : '/futbol';
                const cap = deporte === 'NBA' ? 'analisis.nba.base' : 'futbol.base';
                navegarConGate(rutaDestino, cap);
              }}
            />
          </div>

          <h1 className="text-3xl lg:text-4xl font-futurista text-texto-principal leading-tight">
            Analiza partidos con trazabilidad, contexto y profundidad operativa.
          </h1>

          <p className="text-sm lg:text-base text-texto-secundario max-w-3xl">
            AnalyticsPredict está diseñado para personas que toman decisiones con criterio.
            Explora el sistema, entiende su estructura y avanza por la progresión visitante → base → premium
            según el nivel de profundidad que necesites.
          </p>

          <div className="flex flex-wrap gap-2">
            <Boton variante="primario" onClick={() => navegarConGate(rutaAnalisisPrincipal, esNBA ? 'analisis.nba.base' : 'futbol.base')}>
              Explorar análisis
            </Boton>
            <Boton variante="secundario" onClick={() => navegar('/login')}>
              Crear cuenta
            </Boton>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-futurista text-texto-principal">Qué puedes hacer en el sistema</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <Tarjeta className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-neon-cyan"><Target className="w-4 h-4" /> Análisis de partidos</div>
              <p className="text-sm text-texto-secundario">Evalúa escenarios con una lectura estructurada para operar con mayor claridad.</p>
              <p className="text-xs text-texto-terciario">Tier: Base</p>
            </Tarjeta>
            <Tarjeta className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-neon-cyan"><NotebookPen className="w-4 h-4" /> Bitácora personal</div>
              <p className="text-sm text-texto-secundario">Guarda tus decisiones y mantén continuidad real de tu proceso operativo.</p>
              <p className="text-xs text-texto-terciario">Tier: Base</p>
            </Tarjeta>
            <Tarjeta className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-neon-cyan"><LineChart className="w-4 h-4" /> Dashboard personal</div>
              <p className="text-sm text-texto-secundario">Sigue tu evolución y revisa tu desempeño desde un panel de seguimiento.</p>
              <p className="text-xs text-texto-terciario">Tier: Base</p>
            </Tarjeta>
            <Tarjeta className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-neon-cyan"><Layers3 className="w-4 h-4" /> Comparar lecturas</div>
              <p className="text-sm text-texto-secundario">Contrasta enfoques entre módulos y contextos para enriquecer decisiones.</p>
              <p className="text-xs text-texto-terciario">Tier: Base / Premium</p>
            </Tarjeta>
            <Tarjeta className="p-4 space-y-2">
              <div className="flex items-center gap-2 text-neon-cyan"><Settings2 className="w-4 h-4" /> Configuración operativa</div>
              <p className="text-sm text-texto-secundario">Ajusta preferencias del sistema y adapta el entorno a tu método de trabajo.</p>
              <p className="text-xs text-texto-terciario">Tier: Base</p>
            </Tarjeta>
            <Tarjeta className="p-4 space-y-2 border border-neon-magenta/30">
              <div className="flex items-center gap-2 text-neon-magenta"><Sparkles className="w-4 h-4" /> Profundidad avanzada</div>
              <p className="text-sm text-texto-secundario">Activa una capa superior para operar con comparativas y contexto extendido.</p>
              <p className="text-xs text-texto-terciario">Tier: Premium</p>
            </Tarjeta>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-futurista text-texto-principal">Progresión de cuenta</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Tarjeta className="p-4 space-y-2 border border-neon-cyan/20">
              <p className="text-xs uppercase tracking-wider text-neon-cyan">Visitante</p>
              <p className="text-sm text-texto-secundario">Explora el sistema, entiende la estructura y valida si encaja contigo.</p>
            </Tarjeta>
            <Tarjeta className="p-4 space-y-2 border border-neon-verde/20">
              <p className="text-xs uppercase tracking-wider text-neon-verde">Base</p>
              <p className="text-sm text-texto-secundario">Accede al análisis, bitácora, dashboard y configuración para operar con continuidad.</p>
            </Tarjeta>
            <Tarjeta className="p-4 space-y-2 border border-neon-magenta/20">
              <p className="text-xs uppercase tracking-wider text-neon-magenta">Premium</p>
              <p className="text-sm text-texto-secundario">Suma comparativas avanzadas, contexto histórico extendido y priorización operativa.</p>
            </Tarjeta>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-xl font-futurista text-texto-principal">Cómo se organiza el producto</h2>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-3 text-sm">
            {[
              ['Centro analítico', 'Explorar y entender el sistema'],
              ['Análisis', 'Operar con lectura estructurada'],
              ['Bitácora', 'Registrar decisiones y contexto'],
              ['Dashboard', 'Seguir desempeño personal'],
              ['Configuración', 'Ajustar tu entorno operativo'],
            ].map(([titulo, descripcion]) => (
              <Tarjeta key={titulo} className="p-4 space-y-1">
                <p className="font-semibold text-texto-principal">{titulo}</p>
                <p className="text-texto-secundario">{descripcion}</p>
              </Tarjeta>
            ))}
          </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Tarjeta className="p-5 space-y-3 border border-neon-magenta/30">
            <div className="flex items-center gap-2 text-neon-magenta">
              <Crown className="w-4 h-4" />
              <h3 className="text-sm uppercase tracking-wider">Capa Premium</h3>
            </div>
            <p className="text-sm text-texto-secundario">
              Premium no reemplaza el producto base: lo lleva a un nivel de profundidad superior.
            </p>
            <ul className="text-sm text-texto-secundario space-y-1">
              <li>• Comparativas multi-mercado.</li>
              <li>• Contexto histórico extendido.</li>
              <li>• Priorización operativa avanzada.</li>
            </ul>
            <Boton variante="secundario" onClick={() => navegarConGate('/dashboard', 'premium.depth')}>
              {can('premium.depth') ? 'Abrir capa Premium' : 'Activa Premium'}
            </Boton>
          </Tarjeta>

          <Tarjeta className="p-5 space-y-3 border border-neon-cyan/25">
            <div className="flex items-center gap-2 text-neon-cyan">
              <ShieldCheck className="w-4 h-4" />
              <h3 className="text-sm uppercase tracking-wider">Siguiente paso</h3>
            </div>
            <p className="text-sm text-texto-secundario">
              Empieza explorando el sistema y activa tu cuenta cuando quieras continuidad personal.
            </p>
            <div className="flex flex-wrap gap-2">
              <Boton variante="primario" onClick={() => navegar('/login')}>
                Crear cuenta
              </Boton>
              <Boton variante="secundario" onClick={() => navegarConGate(rutaAnalisisPrincipal, esNBA ? 'analisis.nba.base' : 'futbol.base')}>
                Ver cómo funciona
              </Boton>
            </div>
          </Tarjeta>
        </section>
      </main>
    </div>
  );
}
