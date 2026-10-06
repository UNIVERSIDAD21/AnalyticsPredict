# Compose local privado (opcional)

> Configuración heredada de staging, adaptada al modo single-user local. Los puertos publicados quedan ligados a `127.0.0.1`. Para acceso desde otro host se requiere una capa privada (VPN/access proxy) verificada. No hay auth, pagos, SMTP ni MailHog. Este archivo no despliega nada por sí mismo.

## 1) Preparar variables
```bash
cd deploy/staging
cp staging.env.example staging.env
# configurar DATABASE_URL de forma protegida; no versionar staging.env
```

## 2) Levantar servicios
```bash
docker compose --env-file staging.env up -d --build
```

## 3) Verificar
- Backend: http://localhost:18000/salud
- Frontend: http://localhost:15173

La URL del backend se integra al build del frontend con el puerto local configurado. Si cambia ese puerto, reconstruir el frontend. El arranque backend entrena el modelo habitual; no usar este Compose contra BD productiva para pruebas.

> Puedes cambiar puertos en `staging.env` (`STAGING_BACKEND_PORT`, `STAGING_FRONTEND_PORT`).

## 4) Apagar
```bash
docker compose --env-file staging.env down
```

## Límite

Docker no estaba instalado en el host observado, así que esta configuración se validó estáticamente, no ejecutando contenedores. No es una receta de despliegue público.
