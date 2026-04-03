# FUENTE_DE_VERDAD_ACTUAL — AnalyticsPredict

Este archivo es el punto de entrada oficial para trabajo operativo y técnico.

## Qué es AnalyticsPredict hoy
Plataforma analítica de decisiones deportivas con foco operativo (calidad de datos, contratos API, métricas, política de operación y trazabilidad), no una app de picks masivos.

## Qué documento manda
1. `docs/FUENTE_DE_VERDAD_ACTUAL.md` (este archivo)
2. `docs/arquitectura/ESTADO_PROYECTO.md` (estado formal por bloques)
3. `docs/arquitectura/PLAN_BLOQUES_C0_C7_LANZAMIENTO_PROFESIONAL.md` (plan estratégico vigente)
4. `docs/work_orders/c0_c7/00_INDICE_WORK_ORDERS_C0_C7.md` (órdenes operativas por bloque)
5. `docs/borlty-context/` (contexto activo mínimo)

## Prioridades activas
- Ejecutar en repo según bloque activo definido por Jefe.
- Mantener contrato, calidad y trazabilidad antes de expansión comercial.
- Actualizar siempre estado y changelog al cerrar bloques.
- Prioridades públicas de negocio vigentes en `docs/comercial/publico/00_INDICE_PLAN_PUBLICO_NEGOCIO.md` (Olas P1/P2/P3 → P4/P6/P8 → P7/P9).
- Panel operativo permanente para ejecución inmediata: `docs/roadmap_inmediato/00_INDICE_EJECUCION_INMEDIATA.md`.

## Estrategia comercial vigente (C0)
- Camino principal de caja: `C0 -> C1 -> C2 -> C3 -> C4 -> C7`.
- Camino paralelo controlado: `C5 -> C6` (no bloquea primer peso).
- NBA = frente comercial principal.
- Fútbol = **beta global con madurez diferenciada por mercado** (gobernado por scorecards walk-forward, política formal, monitoreo continuo y shadow mode).
- Regla vigente: no hay salida beta global automática; la promoción es parcial y reversible por mercado.
- Estado de cierre de etapa (bloques 10-13): **0 mercados promocionables** en la evidencia actual, por lo que fútbol mantiene beta global.
- No se posiciona el producto como app masiva de picks ni promesa de ganancias fáciles.

## Bloqueo comercial explícito (auditoría)
- C1 permanece **EN_CURSO** hasta ejecutar validación manual real de MercadoPago con dominio/URL pública final y callback estable.
- C7 permanece **PENDIENTE** y no se abre hasta cierre manual real de C1 (no aplica cierre por validación equivalente únicamente).

## Qué está en laboratorio
- Líneas no cerradas por criterios formales en `ESTADO_PROYECTO`.
- Funcionalidades con evidencia parcial en `docs/borlty-deliverables/` (reportes, pruebas de ciclo, validaciones puntuales).

## Qué se considera histórico
- `docs/archive/` → contexto obsoleto o reemplazado.
- Entregables cerrados y evidencia histórica viven en `docs/borlty-deliverables/`.

## Dónde consultar evidencia
- Reportes de ejecución/ciclos: `docs/borlty-deliverables/reportes/`
- Cierres por bloque: `docs/borlty-deliverables/bloque_08/`, `docs/borlty-deliverables/bloque_09/`
- Checklists históricos: `docs/borlty-deliverables/checklists/`

## Regla de gobierno documental
- Contexto activo debe mantenerse corto y gobernable.
- Entregables/evidencia no se borran; se preservan en `borlty-deliverables`.
- Lo obsoleto se archiva en `archive`.
