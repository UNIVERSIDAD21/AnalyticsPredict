import type { TierProducto } from './freemium';

export type Capability =
  | 'public.shell'
  | 'public.center'
  | 'public.governance'
  | 'dashboard.personal'
  | 'bitacora.personal'
  | 'configuracion.base'
  | 'analisis.nba.base'
  | 'futbol.base'
  | 'premium.depth'
  | 'chat.contextual';

export interface AccessPolicy {
  tier: TierProducto;
  capabilities: Record<Capability, boolean>;
}

const CHAT_ENABLED = false;

function buildCapabilities(tier: TierProducto): Record<Capability, boolean> {
  const base: Record<Capability, boolean> = {
    'public.shell': true,
    'public.center': true,
    'public.governance': true,
    'dashboard.personal': tier !== 'INVITADO',
    'bitacora.personal': tier !== 'INVITADO',
    'configuracion.base': tier !== 'INVITADO',
    'analisis.nba.base': tier !== 'INVITADO',
    'futbol.base': tier !== 'INVITADO',
    'premium.depth': tier === 'PREMIUM',
    'chat.contextual': CHAT_ENABLED && tier !== 'INVITADO',
  };

  return base;
}

export function construirAccessPolicy(tier: TierProducto): AccessPolicy {
  return {
    tier,
    capabilities: buildCapabilities(tier),
  };
}

export function puedeAcceder(policy: AccessPolicy, capability: Capability): boolean {
  return !!policy.capabilities[capability];
}
