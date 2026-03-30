import { useAccessPolicy } from '../contextos/AccessPolicyContext';
import { useAuth } from '../contextos/AuthContext';
import { useGatePrompt } from '../contextos/GatePromptContext';
import { obtenerGateConfig, type Capability } from '../servicios/accessPolicy';
import { registrarEventoProducto } from '../servicios/productAnalytics';

export function useGateNavigation(navegar: (ruta: string) => void) {
  const { can, policy } = useAccessPolicy();
  const { usuario } = useAuth();
  const { abrirGatePrompt } = useGatePrompt();

  const navegarConGate = (ruta: string, capability: Capability) => {
    if (can(capability)) {
      registrarEventoProducto('gate_allowed', { capability, ruta });
      navegar(ruta);
      return;
    }

    const autenticado = !!usuario;
    const gate = obtenerGateConfig(policy, capability, autenticado);

    registrarEventoProducto('gate_blocked', {
      capability,
      ruta,
      autenticado,
      gateType: gate.tipoGate,
    });

    const destinoSecundario = gate.destinoSecundario;

    abrirGatePrompt({
      tipoGate: gate.tipoGate,
      titulo: gate.copy.titulo,
      mensaje: gate.copy.mensaje,
      accionPrincipalLabel: gate.ctaPrincipal,
      accionSecundariaLabel: gate.ctaSecundaria,
      onAccionPrincipal: () => navegar(gate.destinoPrincipal),
      onAccionSecundaria: destinoSecundario ? () => navegar(destinoSecundario) : undefined,
    });
  };

  return { navegarConGate };
}
