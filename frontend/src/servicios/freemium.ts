import { obtenerEstadoPlan } from './pagos';

const KEY_INVITADO_ID = 'freemium.invitado_id';
const KEY_CHAT_DIARIO = 'freemium.chat.diario';

export type TierProducto = 'INVITADO' | 'BASE' | 'PREMIUM';

export interface EstadoFreemium {
  tier: TierProducto;
  identificadorTrazable: string;
  limiteMensajesChatDia: number;
  usadosHoy: number;
  restantesHoy: number;
  fechaDia: string;
}

interface ConsumoChatDiario {
  fecha: string;
  usados: number;
}

function hoyIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function getOrCreateInvitadoId(): string {
  if (typeof window === 'undefined') return 'invitado-servidor';

  const existente = window.localStorage.getItem(KEY_INVITADO_ID);
  if (existente && existente.trim().length > 0) return existente;

  const nuevo = `inv_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  window.localStorage.setItem(KEY_INVITADO_ID, nuevo);
  return nuevo;
}

function leerConsumoChatDiario(identificador: string): ConsumoChatDiario {
  if (typeof window === 'undefined') return { fecha: hoyIso(), usados: 0 };

  const key = `${KEY_CHAT_DIARIO}.${identificador}`;
  const raw = window.localStorage.getItem(key);
  const hoy = hoyIso();
  if (!raw) return { fecha: hoy, usados: 0 };

  try {
    const parsed = JSON.parse(raw) as ConsumoChatDiario;
    if (parsed.fecha !== hoy) return { fecha: hoy, usados: 0 };
    return {
      fecha: parsed.fecha,
      usados: Number.isFinite(parsed.usados) ? Math.max(0, parsed.usados) : 0,
    };
  } catch {
    return { fecha: hoy, usados: 0 };
  }
}

function guardarConsumoChatDiario(identificador: string, data: ConsumoChatDiario): void {
  if (typeof window === 'undefined') return;
  const key = `${KEY_CHAT_DIARIO}.${identificador}`;
  window.localStorage.setItem(key, JSON.stringify(data));
}

export async function obtenerEstadoFreemium(usuarioId: string | null): Promise<EstadoFreemium> {
  const invitadoId = getOrCreateInvitadoId();
  const identificadorTrazable = usuarioId ? `usr_${usuarioId}` : invitadoId;

  let tier: TierProducto = usuarioId ? 'BASE' : 'INVITADO';

  if (usuarioId) {
    try {
      const plan = await obtenerEstadoPlan();
      if (plan.activo) tier = 'PREMIUM';
    } catch {
      tier = 'BASE';
    }
  }

  const limiteMensajesChatDia = tier === 'PREMIUM' ? 9999 : 20;
  const consumo = leerConsumoChatDiario(identificadorTrazable);
  const restantesHoy = Math.max(0, limiteMensajesChatDia - consumo.usados);

  return {
    tier,
    identificadorTrazable,
    limiteMensajesChatDia,
    usadosHoy: consumo.usados,
    restantesHoy,
    fechaDia: consumo.fecha,
  };
}

export function consumirMensajeChatFreemium(estado: EstadoFreemium): EstadoFreemium {
  if (estado.tier === 'PREMIUM') return estado;

  const siguienteUso = Math.min(estado.limiteMensajesChatDia, estado.usadosHoy + 1);
  const nuevoEstado: EstadoFreemium = {
    ...estado,
    usadosHoy: siguienteUso,
    restantesHoy: Math.max(0, estado.limiteMensajesChatDia - siguienteUso),
  };

  guardarConsumoChatDiario(estado.identificadorTrazable, {
    fecha: estado.fechaDia,
    usados: siguienteUso,
  });

  return nuevoEstado;
}
