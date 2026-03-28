import { useAccessPolicy } from '../contextos/AccessPolicyContext';
import { useAuth } from '../contextos/AuthContext';
import { useGatePrompt } from '../contextos/GatePromptContext';
import { obtenerGateCopy, type Capability } from '../servicios/accessPolicy';

export function useGateNavigation(navegar: (ruta: string) => void) {
  const { can } = useAccessPolicy();
  const { usuario } = useAuth();
  const { abrirGatePrompt } = useGatePrompt();

  const navegarConGate = (ruta: string, capability: Capability) => {
    if (can(capability)) {
      navegar(ruta);
      return;
    }

    const autenticado = !!usuario;
    const copy = obtenerGateCopy(capability, autenticado);

    if (!autenticado) {
      abrirGatePrompt({
        titulo: copy.titulo,
        mensaje: copy.mensaje,
        accionPrincipalLabel: 'Crear cuenta',
        accionSecundariaLabel: 'Iniciar sesión',
        onAccionPrincipal: () => navegar('/login'),
        onAccionSecundaria: () => navegar('/login'),
      });
      return;
    }

    const primaryLabel = capability === 'premium.depth'
      ? 'Ver opciones premium'
      : 'Ir a dashboard';

    abrirGatePrompt({
      titulo: copy.titulo,
      mensaje: copy.mensaje,
      accionPrincipalLabel: primaryLabel,
      accionSecundariaLabel: 'Quedarme aquí',
      onAccionPrincipal: () => navegar(capability === 'premium.depth' ? '/configuracion' : '/dashboard'),
      onAccionSecundaria: () => {},
    });
  };

  return { navegarConGate };
}
