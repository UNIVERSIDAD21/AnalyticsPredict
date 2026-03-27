import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import { useAuth } from './AuthContext';
import { obtenerEstadoPlan } from '../servicios/pagos';
import { construirAccessPolicy, puedeAcceder, type AccessPolicy, type Capability } from '../servicios/accessPolicy';
import type { TierProducto } from '../servicios/freemium';

interface AccessPolicyContextType {
  tier: TierProducto;
  cargandoTier: boolean;
  policy: AccessPolicy;
  can: (capability: Capability) => boolean;
}

const AccessPolicyContext = createContext<AccessPolicyContextType | undefined>(undefined);

export function ProveedorAccessPolicy({ children }: { children: ReactNode }) {
  const { autenticado, cargando } = useAuth();
  const [tier, setTier] = useState<TierProducto>('INVITADO');
  const [cargandoTier, setCargandoTier] = useState(false);

  useEffect(() => {
    const resolverTier = async () => {
      if (cargando) return;

      if (!autenticado) {
        setTier('INVITADO');
        setCargandoTier(false);
        return;
      }

      setCargandoTier(true);
      try {
        const plan = await obtenerEstadoPlan();
        setTier(plan.activo ? 'PREMIUM' : 'BASE');
      } catch {
        setTier('BASE');
      } finally {
        setCargandoTier(false);
      }
    };

    void resolverTier();
  }, [autenticado, cargando]);

  const policy = useMemo(() => construirAccessPolicy(tier), [tier]);

  const value = useMemo<AccessPolicyContextType>(
    () => ({
      tier,
      cargandoTier,
      policy,
      can: (capability: Capability) => puedeAcceder(policy, capability),
    }),
    [tier, cargandoTier, policy]
  );

  return <AccessPolicyContext.Provider value={value}>{children}</AccessPolicyContext.Provider>;
}

export function useAccessPolicy() {
  const ctx = useContext(AccessPolicyContext);
  if (!ctx) {
    throw new Error('useAccessPolicy debe usarse dentro de ProveedorAccessPolicy');
  }
  return ctx;
}
