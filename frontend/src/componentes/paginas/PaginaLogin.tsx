import { FormEvent, useState } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contextos/AuthContext';

export function PaginaLogin() {
  const { autenticado, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  if (autenticado) {
    return <Navigate to="/" replace />;
  }

  const destino = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname || '/';

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
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

  return (
    <div className="min-h-screen bg-futurista-negro flex items-center justify-center p-4">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-md rounded-xl border border-neon-cyan/20 bg-futurista-oscuro/60 p-6 space-y-4"
      >
        <h1 className="text-2xl font-bold text-neon-cyan">Iniciar sesión</h1>
        <p className="text-texto-secundario text-sm">Accede para usar AnalyticsPredict.</p>

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

        {error && <p className="text-red-400 text-sm">{error}</p>}

        <button
          type="submit"
          className="w-full py-2 rounded bg-neon-cyan/20 text-neon-cyan border border-neon-cyan/40 hover:bg-neon-cyan/30 disabled:opacity-50"
          disabled={cargando}
        >
          {cargando ? 'Ingresando…' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}
