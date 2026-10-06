# Staging (Docker)

> Transición single-user: los puertos publicados por Compose quedan ligados a `127.0.0.1` por defecto. Para acceso desde otro host se requiere una capa privada (VPN/access proxy) verificada; no publicar la API sensible directamente. El cambio de Compose solo aplica al recrear servicios; no altera despliegues existentes por sí mismo.

## 1) Preparar variables
```bash
cd deploy/staging
cp staging.env.example staging.env
# editar staging.env con valores reales (especialmente DATABASE_URL)
```

## 2) Levantar servicios
```bash
docker compose up -d --build
```

## 3) Verificar
- Backend: http://localhost:18000/salud
- Frontend: http://localhost:15173

> Puedes cambiar puertos en `staging.env` (`STAGING_BACKEND_PORT`, `STAGING_FRONTEND_PORT`).

## 4) Apagar
```bash
docker compose down
```

## Notas
- Esta carpeta es base de staging inicial (A1). El hardening productivo (TLS, backups, rollback formal) se ejecuta en B6.
