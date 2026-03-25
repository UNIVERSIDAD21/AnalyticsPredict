import { useCallback, useEffect, useState } from 'react';
import { MessageSquare, RotateCcw, Send } from 'lucide-react';
import { Encabezado } from '../organismos';
import { Boton } from '../atomos';
import { useToasts } from '../../contextos/Toasts';
import { useAuth } from '../../contextos/AuthContext';
import { enviarMensajeChat, obtenerHistorialChat, resetChat, type ChatItem } from '../../servicios/chat';
import {
  consumirMensajeChatFreemium,
  obtenerEstadoFreemium,
  type EstadoFreemium,
} from '../../servicios/freemium';

export function PaginaChat() {
  const { agregarToast } = useToasts();
  const { usuario } = useAuth();
  const [historial, setHistorial] = useState<ChatItem[]>([]);
  const [mensaje, setMensaje] = useState('');
  const [enviando, setEnviando] = useState(false);
  const [cargando, setCargando] = useState(true);
  const [freemium, setFreemium] = useState<EstadoFreemium | null>(null);

  const recargarHistorial = useCallback(async () => {
    try {
      const items = await obtenerHistorialChat(30);
      setHistorial(items);
    } catch (error) {
      agregarToast({
        titulo: 'Error cargando chat',
        mensaje: error instanceof Error ? error.message : 'No se pudo cargar historial.',
        tipo: 'error',
      });
    }
  }, [agregarToast]);

  useEffect(() => {
    const init = async () => {
      await recargarHistorial();
      const estadoFreemium = await obtenerEstadoFreemium(usuario?.id ? String(usuario.id) : null);
      setFreemium(estadoFreemium);
      setCargando(false);
    };
    void init();
  }, [recargarHistorial, usuario?.id]);

  const onEnviar = async () => {
    if (!mensaje.trim() || enviando) return;

    if (freemium && freemium.tier !== 'PREMIUM' && freemium.restantesHoy <= 0) {
      agregarToast({
        titulo: 'Límite diario alcanzado',
        mensaje: 'Llegaste al límite diario del plan base/invitado. Para continuar hoy, necesitas plan premium.',
        tipo: 'warning',
      });
      return;
    }

    try {
      setEnviando(true);
      await enviarMensajeChat(mensaje.trim(), 12);
      setMensaje('');
      await recargarHistorial();
      if (freemium && freemium.tier !== 'PREMIUM') {
        setFreemium(consumirMensajeChatFreemium(freemium));
      }
    } catch (error) {
      agregarToast({
        titulo: 'No se pudo enviar',
        mensaje: error instanceof Error ? error.message : 'Error enviando mensaje.',
        tipo: 'error',
      });
    } finally {
      setEnviando(false);
    }
  };

  const onReset = async () => {
    try {
      await resetChat('reset manual desde UI');
      setHistorial([]);
      agregarToast({
        titulo: 'Chat reiniciado',
        mensaje: 'Se limpió el contexto conversacional.',
        tipo: 'success',
      });
    } catch (error) {
      agregarToast({
        titulo: 'No se pudo reiniciar',
        mensaje: error instanceof Error ? error.message : 'Error reiniciando chat.',
        tipo: 'error',
      });
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Encabezado />

      <main className="flex-1 contenedor py-6 lg:py-8 space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-neon-cyan" />
            <h2 className="text-2xl font-futurista text-texto-principal">Chat contextual</h2>
          </div>
          <Boton variante="secundario" iconoInicio={<RotateCcw size={16} />} onClick={() => void onReset()}>
            Reiniciar contexto
          </Boton>
        </div>

        <div className="tarjeta p-4 text-xs text-texto-secundario border border-neon-cyan/20 space-y-2">
          <p>⚠️ Este asistente ofrece información orientativa y educativa. No garantiza resultados ni constituye asesoría financiera profesional.</p>
          {freemium && (
            <p>
              Plan: <strong>{freemium.tier}</strong> · Mensajes hoy: <strong>{freemium.usadosHoy}/{freemium.limiteMensajesChatDia}</strong>
              {freemium.tier !== 'PREMIUM' && (
                <>
                  {' '}· Restantes: <strong>{freemium.restantesHoy}</strong>
                </>
              )}
              {' '}· Trazabilidad: <code>{freemium.identificadorTrazable}</code>
            </p>
          )}
        </div>

        <div className="tarjeta p-4 min-h-[420px] max-h-[520px] overflow-y-auto space-y-3">
          {cargando ? (
            <p className="text-texto-secundario">Cargando chat…</p>
          ) : historial.length === 0 ? (
            <p className="text-texto-terciario">Sin mensajes aún. Escríbeme y empezamos.</p>
          ) : (
            historial.map((item) => (
              <div
                key={item.id}
                className={`rounded-lg p-3 border ${
                  item.role === 'user'
                    ? 'border-neon-magenta/30 bg-neon-magenta/5'
                    : 'border-neon-cyan/30 bg-neon-cyan/5'
                }`}
              >
                <p className="text-[11px] uppercase tracking-wider text-texto-terciario mb-1">
                  {item.role === 'user' ? 'Tú' : 'Asistente'}
                </p>
                <p className="text-sm text-texto-principal whitespace-pre-wrap">{item.contenido}</p>
              </div>
            ))
          )}
        </div>

        <div className="tarjeta p-4">
          <div className="flex gap-2">
            <textarea
              value={mensaje}
              onChange={(event) => setMensaje(event.target.value)}
              rows={3}
              className="flex-1 rounded-lg px-3 py-2 bg-futurista-oscuro/70 border border-neon-cyan/20 text-texto-principal focus:outline-none focus:border-neon-cyan"
              placeholder="Escribe tu mensaje..."
            />
            <Boton
              variante="primario"
              iconoInicio={<Send size={16} />}
              onClick={() => void onEnviar()}
              disabled={
                enviando ||
                !mensaje.trim() ||
                !!(freemium && freemium.tier !== 'PREMIUM' && freemium.restantesHoy <= 0)
              }
            >
              {enviando ? 'Enviando...' : 'Enviar'}
            </Boton>
          </div>
        </div>
      </main>
    </div>
  );
}
