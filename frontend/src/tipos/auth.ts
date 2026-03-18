export interface UsuarioAuth {
  id: number;
  email: string;
  created_at?: string;
}

export interface RespuestaAuth {
  ok: boolean;
  user?: UsuarioAuth;
  access_token: string;
  refresh_token: string;
  token_type: 'Bearer';
  expires_in: number;
}
