# FUENTE_DE_VERDAD_ACTUAL — AnalyticsPredict

Este archivo es el punto de entrada oficial para trabajo operativo y técnico.

> **Estado operativo 2026-10-05:** AnalyticsPredict funciona localmente como herramienta personal single-user, sin login, pagos, suscripciones ni tiers. Neon fue migrada tras backup verificado: 182 apuestas NBA, 13 de fútbol, 7 combinadas y 16 selecciones conservadas. La configuración proviene de la cuenta con mayor actividad; por instrucción posterior del propietario, **todos** los registros deportivos son historial personal visible. La procedencia original permanece en el backup privado. `docs/reactivacion_single_user/` gobierna el trabajo nuevo. C0–C7 y la estrategia comercial descritos debajo son históricos, no tareas vigentes.

## Qué es AnalyticsPredict hoy
Plataforma analítica de decisiones deportivas con foco operativo (calidad de datos, contratos API, métricas, política de operación y trazabilidad), no una app de picks masivos.

## Qué documento manda
1. `docs/FUENTE_DE_VERDAD_ACTUAL.md` (este archivo)
2. `docs/arquitectura/ESTADO_PROYECTO.md` (estado formal por bloques)
3. `docs/reactivacion_single_user/ROADMAP_REACTIVACION_ANALYTICSPREDICT.md` (plan vigente)
4. `docs/reactivacion_single_user/DEUDA_TECNICA_PRIORIZADA.md` (prioridades técnicas)
5. `docs/borlty-context/` (contexto histórico complementario)

## Prioridades activas
- Seguir las instrucciones más recientes del propietario y el roadmap single-user.
- H7 y la base de reproducibilidad/CI se verificaron con pruebas dirigidas y CI alojada (4/4 jobs, 2026-10-06). La recertificación analítica **no pasó**: ver `docs/reactivacion_single_user/RECERTIFICACION_ANALITICA_2026-10-06.md` antes de citar métricas de rendimiento.
- Mantener estado y changelog al cerrar bloques; el plan comercial y sus órdenes son históricos.

## Estrategia comercial histórica (C0; no vigente)
- Camino principal de caja: `C0 -> C1 -> C2 -> C3 -> C4 -> C7`.
- Camino paralelo controlado: `C5 -> C6` (no bloquea primer peso).
- NBA = frente comercial principal.
- Fútbol = **beta global con madurez diferenciada por mercado** (gobernado por scorecards walk-forward, política formal, monitoreo continuo y shadow mode).
- Regla vigente: no hay salida beta global automática; la promoción es parcial y reversible por mercado.
- Estado de cierre de etapa (bloques 10-14): **0 mercados promocionables** en la evidencia actual, por lo que fútbol mantiene beta global.
- No se posiciona el producto como app masiva de picks ni promesa de ganancias fáciles.

## Bloqueo comercial histórico (auditoría; no aplica al producto actual)
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
