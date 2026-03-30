import { useEffect } from 'react';
import { Crown, Layers3 } from 'lucide-react';
import { Boton, Tarjeta } from '../atomos';
import { registrarEventoProducto } from '../../servicios/productAnalytics';

interface PanelDepthPremiumProps {
  modulo: 'nba' | 'futbol' | 'futbol_partido';
  titulo: string;
  descripcion: string;
  bullets: string[];
  activo: boolean;
  onAbrirDepth: () => void;
}

export function PanelDepthPremium({
  modulo,
  titulo,
  descripcion,
  bullets,
  activo,
  onAbrirDepth,
}: PanelDepthPremiumProps) {
  useEffect(() => {
    registrarEventoProducto('premium_layer_interaction', {
      modulo,
      interaction: 'view',
      premiumActive: activo,
    });
  }, [modulo, activo]);
  return (
    <Tarjeta className="p-5 space-y-3 border border-neon-magenta/30">
      <div className="flex items-center gap-2 text-neon-magenta">
        <Crown className="w-4 h-4" />
        <h3 className="text-sm uppercase tracking-wider">{titulo}</h3>
      </div>

      <p className="text-sm text-texto-secundario">{descripcion}</p>

      <ul className="text-sm text-texto-secundario space-y-1">
        {bullets.map((item) => (
          <li key={item}>• {item}</li>
        ))}
      </ul>

      <div className={`rounded-lg border p-3 text-sm ${activo ? 'border-neon-magenta/25 bg-futurista-oscuro/40 text-texto-secundario' : 'border-neon-cyan/20 bg-futurista-oscuro/40 text-texto-secundario'}`}>
        {activo
          ? 'Depth premium activa: comparativas multi-mercado, contexto histórico extendido y priorización operativa avanzada.'
          : 'Plan base activo: flujo operativo completo disponible. Premium añade profundidad adicional dentro de este mismo módulo.'}
      </div>

      <Boton
        variante="secundario"
        onClick={() => {
          registrarEventoProducto('premium_layer_interaction', {
            modulo,
            interaction: 'click_cta',
            premiumActive: activo,
          });
          onAbrirDepth();
        }}
        iconoInicio={<Layers3 className="w-4 h-4" />}
      >
        {activo ? 'Abrir depth premium' : 'Desbloquear capa premium'}
      </Boton>
    </Tarjeta>
  );
}
