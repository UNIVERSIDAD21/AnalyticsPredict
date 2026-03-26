import { FormEvent, useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Crown, Radar, ShieldCheck } from 'lucide-react';
import { useAuth } from '../../contextos/AuthContext';
import { restablecerPassword, solicitarRecuperacion } from '../../servicios/auth';

type ModoAuth = 'login' | 'register' | 'forgot' | 'reset';
const LEGAL_VERSION = '2026-03-18';

export function PaginaLogin() {
  const { autenticado, login, register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [modo, setModo] = useState<ModoAuth>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [tokenReset, setTokenReset] = useState('');
  const [acceptedLegal, setAcceptedLegal] = useState(false);
  const [mensaje, setMensaje] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  if (autenticado) {
    return <Navigate to="/" replace />;
  }

  const destino = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || '/app';

  const limpiarMensajes = () => {
    setError(null);
    setMensaje(null);
  };

  const onSubmitLogin = async (e: FormEvent) => {
    e.preventDefault();
    limpiarMensajes();
    setCargando(true);
    try {
      await login(email, password);
      navigate(destino, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo iniciar sesión');
    } finally {
      setCargando(false);
    }
  };

  const onSubmitRegister = async (e: FormEvent) => {
    e.preventDefault();
    limpiarMensajes();

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    if (!acceptedLegal) {
      setError('Debes aceptar Términos, Privacidad y Disclaimer para continuar.');
      return;
    }

    setCargando(true);
    try {
      await register(email, password, LEGAL_VERSION, acceptedLegal);
      navigate(destino, { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo registrar la cuenta');
    } finally {
      setCargando(false);
    }
  };

  const onSubmitForgot = async (e: FormEvent) => {
    e.preventDefault();
    limpiarMensajes();
    setCargando(true);
    try {
      const resp = await solicitarRecuperacion(email);
      setMensaje(resp.message);
      if (resp.reset_token_dev) {
        setTokenReset(resp.reset_token_dev);
        setModo('reset');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo iniciar recuperación');
    } finally {
      setCargando(false);
    }
  };

  const onSubmitReset = async (e: FormEvent) => {
    e.preventDefault();
    limpiarMensajes();

    if (password !== confirmPassword) {
      setError('Las contraseñas no coinciden.');
      return;
    }

    setCargando(true);
    try {
      const resp = await restablecerPassword(tokenReset, password);
      setMensaje(resp.message);
      setModo('login');
      setPassword('');
      setConfirmPassword('');
      setTokenReset('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo restablecer la contraseña');
    } finally {
      setCargando(false);
    }
  };

  const titulo =
    modo === 'login'
      ? 'Iniciar sesión'
      : modo === 'register'
      ? 'Crear cuenta'
      : modo === 'forgot'
      ? 'Recuperar contraseña'
      : 'Restablecer contraseña';

  return (
    <div className="min-h-screen bg-futurista-negro flex items-center justify-center p-4">
      <div className="w-full max-w-md rounded-xl border border-neon-cyan/20 bg-futurista-oscuro/60 p-6 space-y-4">
        <h1 className="text-2xl font-bold text-neon-cyan">{titulo}</h1>
        <p className="text-texto-secundario text-sm">Accede para usar AnalyticsPredict con trazabilidad personal y gestión completa.</p>
        <p className="text-xs text-texto-terciario">
          ¿Aún no quieres registrarte? Puedes explorar el
          {' '}<Link to="/centro-analitico" className="text-neon-cyan hover:underline">centro analítico en modo visitante</Link>
          {' '}con acceso limitado y sin funciones premium.
        </p>

        <div className="rounded-lg border border-neon-cyan/20 bg-futurista-negro/40 p-3 space-y-2 text-xs">
          <p className="flex items-center gap-2 text-neon-cyan uppercase tracking-wider"><ShieldCheck className="w-4 h-4" /> Credibilidad operativa</p>
          <p className="text-texto-secundario">Sin narrativa de “ganar fácil”. NBA es frente principal; fútbol crece por evidencia y madurez.</p>
          <p className="flex items-center gap-2 text-neon-amarillo uppercase tracking-wider"><Radar className="w-4 h-4" /> Fútbol sin maquillaje</p>
          <p className="text-texto-secundario">Estados por competición: estable, en validación o laboratorio.</p>
          <p className="flex items-center gap-2 text-neon-magenta uppercase tracking-wider"><Crown className="w-4 h-4" /> Premium</p>
          <p className="text-texto-secundario">Premium = profundidad de seguimiento y análisis extendido, no solo desbloqueo.</p>
        </div>

        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => {
              limpiarMensajes();
              setModo('login');
            }}
            className={`py-2 rounded border text-sm ${
              modo === 'login' ? 'border-neon-cyan text-neon-cyan' : 'border-neon-cyan/20 text-texto-secundario'
            }`}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => {
              limpiarMensajes();
              setModo('register');
            }}
            className={`py-2 rounded border text-sm ${
              modo === 'register' ? 'border-neon-cyan text-neon-cyan' : 'border-neon-cyan/20 text-texto-secundario'
            }`}
          >
            Registro
          </button>
        </div>

        {(modo === 'login' || modo === 'register') && (
          <form onSubmit={modo === 'login' ? onSubmitLogin : onSubmitRegister} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="email" className="text-sm text-texto-secundario">Correo</label>
              <input
                id="email"
                type="email"
                className="w-full px-3 py-2 rounded bg-futurista-negro border border-neon-cyan/20 text-texto-principal"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="password" className="text-sm text-texto-secundario">Contraseña</label>
              <input
                id="password"
                type="password"
                className="w-full px-3 py-2 rounded bg-futurista-negro border border-neon-cyan/20 text-texto-principal"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            {modo === 'register' && (
              <>
                <div className="space-y-2">
                  <label htmlFor="confirmPassword" className="text-sm text-texto-secundario">Confirmar contraseña</label>
                  <input
                    id="confirmPassword"
                    type="password"
                    className="w-full px-3 py-2 rounded bg-futurista-negro border border-neon-cyan/20 text-texto-principal"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                </div>

                <label className="flex items-start gap-2 text-xs text-texto-secundario">
                  <input
                    type="checkbox"
                    checked={acceptedLegal}
                    onChange={(e) => setAcceptedLegal(e.target.checked)}
                    className="mt-0.5"
                  />
                  <span>
                    Acepto los{' '}
                    <Link to="/legal/terminos" className="text-neon-cyan hover:underline">Términos</Link>,{' '}
                    <Link to="/legal/privacidad" className="text-neon-cyan hover:underline">Política de Privacidad</Link>{' '}
                    y <Link to="/legal/disclaimer" className="text-neon-cyan hover:underline">Disclaimer</Link>
                    {' '}versión {LEGAL_VERSION}.
                  </span>
                </label>
              </>
            )}

            <button
              type="submit"
              className="w-full py-2 rounded bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 hover:bg-neon-cyan/30 disabled:opacity-50"
              disabled={cargando}
            >
              {cargando ? 'Procesando…' : modo === 'login' ? 'Entrar' : 'Crear cuenta'}
            </button>
          </form>
        )}

        {modo === 'forgot' && (
          <form onSubmit={onSubmitForgot} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="forgotEmail" className="text-sm text-texto-secundario">Correo</label>
              <input
                id="forgotEmail"
                type="email"
                className="w-full px-3 py-2 rounded bg-futurista-negro border border-neon-cyan/20 text-texto-principal"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 rounded bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 hover:bg-neon-cyan/30 disabled:opacity-50"
              disabled={cargando}
            >
              {cargando ? 'Enviando…' : 'Solicitar recuperación'}
            </button>
          </form>
        )}

        {modo === 'reset' && (
          <form onSubmit={onSubmitReset} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="tokenReset" className="text-sm text-texto-secundario">Token de recuperación</label>
              <input
                id="tokenReset"
                type="text"
                className="w-full px-3 py-2 rounded bg-futurista-negro border border-neon-cyan/20 text-texto-principal"
                value={tokenReset}
                onChange={(e) => setTokenReset(e.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="resetPassword" className="text-sm text-texto-secundario">Nueva contraseña</label>
              <input
                id="resetPassword"
                type="password"
                className="w-full px-3 py-2 rounded bg-futurista-negro border border-neon-cyan/20 text-texto-principal"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="resetConfirmPassword" className="text-sm text-texto-secundario">Confirmar contraseña</label>
              <input
                id="resetConfirmPassword"
                type="password"
                className="w-full px-3 py-2 rounded bg-futurista-negro border border-neon-cyan/20 text-texto-principal"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>

            <button
              type="submit"
              className="w-full py-2 rounded bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 hover:bg-neon-cyan/30 disabled:opacity-50"
              disabled={cargando}
            >
              {cargando ? 'Restableciendo…' : 'Guardar nueva contraseña'}
            </button>
          </form>
        )}

        <div className="flex justify-between text-xs">
          <button
            type="button"
            className="text-texto-secundario hover:text-neon-cyan"
            onClick={() => {
              limpiarMensajes();
              setModo('forgot');
            }}
          >
            ¿Olvidaste tu contraseña?
          </button>
          <button
            type="button"
            className="text-texto-secundario hover:text-neon-cyan"
            onClick={() => {
              limpiarMensajes();
              setModo('reset');
            }}
          >
            Ya tengo token
          </button>
        </div>

        {error && <p className="text-red-400 text-sm">{error}</p>}
        {mensaje && <p className="text-neon-verde text-sm">{mensaje}</p>}
      </div>
    </div>
  );
}
