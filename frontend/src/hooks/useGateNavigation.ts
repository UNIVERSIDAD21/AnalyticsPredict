import { useAccessPolicy } from '../contextos/AccessPolicyContext';
import { useAuth } from '../contextos/AuthContext';
import { useToasts } from '../contextos/Toasts';
import { obtenerGateCopy, type Capability } from '../servicios/accessPolicy';

export function useGateNavigation(navegar: (ruta: string) => void) {
  const { can } = useAccessPolicy();
  const { usuario } = useAuth();
  const { agregarToast } = useToasts();

  const navegarConGate = (ruta: string, capability: Capability) => {
    if (can(capability)) {
      navegar(ruta);
      return;
    }

    const autenticado = !!usuario;
    const copy = obtenerGateCopy(capability, autenticado);
    agregarToast({
      tipo: 'info',
      titulo: copy.titulo,
      mensaje: copy.mensaje,
    });

    if (!autenticado) {
      navegar('/login');
      return;
    }

    navegar('/dashboard');
  };

  return { navegarConGate };
}
