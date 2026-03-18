import { clienteAPI, extraerMensajeError } from './api';

export interface ChatItem {
  id: number;
  user_id: number;
  role: 'user' | 'assistant';
  contenido: string;
  created_at: string;
}

export async function enviarMensajeChat(mensaje: string, limiteContexto = 12): Promise<{ reply: string; window_size: number }> {
  try {
    const { data } = await clienteAPI.post('/api/chat/mensaje', {
      mensaje,
      limite_contexto: limiteContexto,
    });
    return {
      reply: String(data?.data?.reply ?? ''),
      window_size: Number(data?.data?.window_size ?? 0),
    };
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function obtenerHistorialChat(limit = 20): Promise<ChatItem[]> {
  try {
    const { data } = await clienteAPI.get('/api/chat/historial', { params: { limit } });
    return (data?.data?.items ?? []) as ChatItem[];
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}

export async function resetChat(motivo?: string): Promise<void> {
  try {
    await clienteAPI.post('/api/chat/reset', { motivo: motivo ?? null });
  } catch (error) {
    throw new Error(extraerMensajeError(error));
  }
}
