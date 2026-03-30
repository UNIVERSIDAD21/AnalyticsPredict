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

export type TipoGate = 'BASE_REQUIRED' | 'PREMIUM_REQUIRED' | 'DISABLED';

export interface CapabilityMeta {
  tierMinimo: TierProducto | null;
  disabled: boolean;
}

export interface AccessPolicy {
  tier: TierProducto;
  capabilities: Record<Capability, boolean>;
}

export interface GateCopy {
  titulo: string;
  mensaje: string;
}

export interface GateConfig {
  tipoGate: TipoGate;
  copy: GateCopy;
  ctaPrincipal: string;
  ctaSecundaria?: string;
  destinoPrincipal: string;
  destinoSecundario?: string;
}

export const COPY_PERMITIDO_BASE = [
  'Crea tu cuenta',
  'Esta función requiere cuenta',
  'Regístrate para desbloquear esta función',
  'Crea tu cuenta para continuar',
] as const;

export const COPY_PERMITIDO_PREMIUM = [
  'Activa Premium',
  'Compra mensualidad',
  'Mejora tu plan',
  'Desbloquea esta capa premium',
] as const;

const CAPABILITY_META: Record<Capability, CapabilityMeta> = {
  'public.shell': { tierMinimo: 'INVITADO', disabled: false },
  'public.center': { tierMinimo: 'INVITADO', disabled: false },
  'public.governance': { tierMinimo: 'INVITADO', disabled: false },
  'dashboard.personal': { tierMinimo: 'BASE', disabled: false },
  'bitacora.personal': { tierMinimo: 'BASE', disabled: false },
  'configuracion.base': { tierMinimo: 'BASE', disabled: false },
  'analisis.nba.base': { tierMinimo: 'BASE', disabled: false },
  'futbol.base': { tierMinimo: 'BASE', disabled: false },
  'premium.depth': { tierMinimo: 'PREMIUM', disabled: false },
  'chat.contextual': { tierMinimo: null, disabled: true },
};

const RANK_TIER: Record<TierProducto, number> = {
  INVITADO: 0,
  BASE: 1,
  PREMIUM: 2,
};

function estaHabilitada(capability: Capability, tier: TierProducto): boolean {
  const meta = CAPABILITY_META[capability];
  if (!meta || meta.disabled || !meta.tierMinimo) return false;
  return RANK_TIER[tier] >= RANK_TIER[meta.tierMinimo];
}

function resolverTipoGate(capability: Capability, tier: TierProducto): TipoGate | null {
  const meta = CAPABILITY_META[capability];
  if (!meta || meta.disabled || !meta.tierMinimo) return 'DISABLED';
  if (estaHabilitada(capability, tier)) return null;
  if (meta.tierMinimo === 'BASE') return 'BASE_REQUIRED';
  if (meta.tierMinimo === 'PREMIUM') return 'PREMIUM_REQUIRED';
  return 'DISABLED';
}

function buildCapabilities(tier: TierProducto): Record<Capability, boolean> {
  return {
    'public.shell': estaHabilitada('public.shell', tier),
    'public.center': estaHabilitada('public.center', tier),
    'public.governance': estaHabilitada('public.governance', tier),
    'dashboard.personal': estaHabilitada('dashboard.personal', tier),
    'bitacora.personal': estaHabilitada('bitacora.personal', tier),
    'configuracion.base': estaHabilitada('configuracion.base', tier),
    'analisis.nba.base': estaHabilitada('analisis.nba.base', tier),
    'futbol.base': estaHabilitada('futbol.base', tier),
    'premium.depth': estaHabilitada('premium.depth', tier),
    'chat.contextual': estaHabilitada('chat.contextual', tier),
  };
}

export function obtenerCapabilityMeta(capability: Capability): CapabilityMeta {
  return CAPABILITY_META[capability];
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

export function obtenerTipoGate(policy: AccessPolicy, capability: Capability): TipoGate | null {
  return resolverTipoGate(capability, policy.tier);
}

export function obtenerGateCopy(capability: Capability, autenticado: boolean): GateCopy {
  if (!autenticado) {
    switch (capability) {
      case 'analisis.nba.base':
      case 'futbol.base':
        return {
          titulo: 'Esta función requiere cuenta',
          mensaje: 'Crea tu cuenta para continuar este análisis con trazabilidad personal.',
        };
      case 'bitacora.personal':
        return {
          titulo: 'Regístrate para desbloquear esta función',
          mensaje: 'Crea tu cuenta para guardar y revisar tus decisiones en tu bitácora personal.',
        };
      case 'dashboard.personal':
        return {
          titulo: 'Crea tu cuenta para continuar',
          mensaje: 'Desbloquea tu dashboard personal para operar con continuidad real.',
        };
      case 'configuracion.base':
        return {
          titulo: 'Esta función requiere cuenta',
          mensaje: 'Crea tu cuenta para guardar bankroll, riesgo y configuración personal.',
        };
      case 'premium.depth':
        return {
          titulo: 'Capa premium visible desde modo visitante',
          mensaje: 'Primero crea tu cuenta para pasar a Base; luego podrás activar Premium para mayor profundidad.',
        };
      default:
        return {
          titulo: 'Esta función requiere cuenta',
          mensaje: 'Crea tu cuenta para continuar.',
        };
    }
  }

  if (capability === 'premium.depth') {
    return {
      titulo: 'Activa Premium',
      mensaje: 'Desbloquea esta capa premium para acceder a comparativas avanzadas y contexto histórico extendido.',
    };
  }

  return {
    titulo: 'Acceso no disponible',
    mensaje: 'Esta sección no está disponible para tu nivel actual.',
  };
}

export function obtenerGateConfig(policy: AccessPolicy, capability: Capability, autenticado: boolean): GateConfig {
  const tipoGate = obtenerTipoGate(policy, capability) ?? 'DISABLED';
  const copy = obtenerGateCopy(capability, autenticado);

  if (tipoGate === 'BASE_REQUIRED') {
    return {
      tipoGate,
      copy,
      ctaPrincipal: 'Crea tu cuenta',
      ctaSecundaria: 'Iniciar sesión',
      destinoPrincipal: '/login',
      destinoSecundario: '/login',
    };
  }

  if (tipoGate === 'PREMIUM_REQUIRED') {
    return {
      tipoGate,
      copy,
      ctaPrincipal: 'Activa Premium',
      ctaSecundaria: 'Mejora tu plan',
      destinoPrincipal: '/configuracion',
      destinoSecundario: '/configuracion',
    };
  }

  return {
    tipoGate: 'DISABLED',
    copy: {
      titulo: 'Capacidad fuera de alcance',
      mensaje: 'Esta función no está disponible en la fase actual del producto.',
    },
    ctaPrincipal: 'Entendido',
    destinoPrincipal: '/',
  };
}
