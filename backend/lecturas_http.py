"""Contexto de lectura HTTP, aislado por tarea y sin modificar roles de la BD."""
from contextvars import ContextVar

solo_lectura_http = ContextVar('solo_lectura_http', default=False)
en_peticion_http = ContextVar('en_peticion_http', default=False)


class LecturasHTTPMiddleware:
    """Conserva el contexto hasta terminar cuerpo/stream y tareas de la respuesta."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        token = solo_lectura_http.set(scope['method'] in {'GET', 'HEAD'})
        token_http = en_peticion_http.set(True)
        try:
            await self.app(scope, receive, send)
        finally:
            en_peticion_http.reset(token_http)
            solo_lectura_http.reset(token)
