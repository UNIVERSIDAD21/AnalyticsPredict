import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import {
  limpiarSesionAuth,
  guardarSesionAuth,
  login as loginServicio,
  register as registerServicio,
  logout as logoutServicio,
  obtenerAccessToken,
  obtenerPerfil,
  obtenerRefreshToken,
  obtenerUsuarioAuth,
} from '../servicios/auth';
import type { UsuarioAuth } from '../tipos/auth';

interface AuthContextType {
  autenticado: boolean;
  cargando: boolean;
  usuario: UsuarioAuth | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function ProveedorAuth({ children }: { children: ReactNode }) {
  const [cargando, setCargando] = useState(true);
  const [usuario, setUsuario] = useState<UsuarioAuth | null>(null);

  useEffect(() => {
    const inicializar = async () => {
      const access = obtenerAccessToken();
      const refresh = obtenerRefreshToken();
      const user = obtenerUsuarioAuth();

      if (!access || !refresh) {
        limpiarSesionAuth();
        setUsuario(null);
        setCargando(false);
        return;
      }

      if (user) {
        setUsuario(user);
        setCargando(false);
        return;
      }

      try {
        const perfil = await obtenerPerfil(access);
        guardarSesionAuth({ accessToken: access, refreshToken: refresh, user: perfil });
        setUsuario(perfil);
      } catch {
        limpiarSesionAuth();
        setUsuario(null);
      } finally {
        setCargando(false);
      }
    };

    void inicializar();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await loginServicio(email, password);
    const perfil = data.user ?? (await obtenerPerfil(data.access_token));
    guardarSesionAuth({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user: perfil,
    });
    setUsuario(perfil);
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const data = await registerServicio(email, password);
    const perfil = data.user ?? (await obtenerPerfil(data.access_token));
    guardarSesionAuth({
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user: perfil,
    });
    setUsuario(perfil);
  }, []);

  const logout = useCallback(async () => {
    const access = obtenerAccessToken();
    if (access) {
      await logoutServicio(access);
    }
    limpiarSesionAuth();
    setUsuario(null);
  }, []);

  const value = useMemo<AuthContextType>(
    () => ({
      autenticado: !!usuario,
      cargando,
      usuario,
      login,
      register,
      logout,
    }),
    [usuario, cargando, login, register, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth debe usarse dentro de ProveedorAuth');
  }
  return ctx;
}
