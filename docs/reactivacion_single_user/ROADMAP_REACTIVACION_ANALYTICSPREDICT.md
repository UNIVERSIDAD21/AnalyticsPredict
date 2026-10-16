# Roadmap vigente de reactivación AnalyticsPredict

**Corte consolidado:2026-10-16.** Directiva single-user del propietario del2026-10-05
y órdenes posteriores. Sustituye C0–C7 comercial; no abre evolución avanzada D.
La ejecución detallada se registra en el `PLAN_MAESTRO.md` externo solicitado por
el propietario, sin copiar memoria/configuración del agente al producto.

## Base cerrada (no repetir)

| Alcance | Evidencia |
|---|---|
| A1–A4: local, retirada comercial, migración/historial | Backup/ensayo/Neon, API/UI sin auth/pagos/tiers; todos los registros deportivos visibles |
| H6/H7 técnico/H10/H11 | Escalas/envelopes corregidos, Python3.12/PG sintético/frontend/Compose en CI |
| NBA dominio/calidad/serving | Selector común válido, artefacto2123 con30NBA,73partidos nuevos; reload no entrena |
| Fútbol datos canónicos | Capturas337/200FT y vínculo explícito a catálogo, idempotencia0/0; histórico conservado |
| Fútbol ciclo ML técnico | Persistencia/activación/loader reparados, JSON verificable, sin modelos/métricas ficticias |
| Fútbol evaluación retrospectiva | Protocolo previo y baseline/IC por partido,581/581/618EVAL, ninguna familia apta para activar |
| Prospectiva técnica NBA | 12snapshotsPRE inmutables anteriores al inicio; no equivalen a12outcomes ni a certificación |

## Pendientes ejecutables del agente

1. **KPI/caches:** grano, ventanas, denominadores, exclusiones y procedencia comunes
   SQL→API→UI; N/D y motivos, raw/calibrado separados, caches observables. Subbloque
   calibración cerrado en [KPI16/10](KPI_CALIBRACION_2026-10-16.md); no cierra P&L/otrosKPI.
2. **Observabilidad/GET:** inventario transitivo y pruebas de ausencia de escrituras;
   fallos de datos/entrenamiento/calibrador/cadena sin ceros o éxitos ficticios.
3. **H12:** resolver auditoría dev, permisos específicos y rot con evidencia,
   preservando cambios previos; lock/tests/lint/build/CI.
4. **Visual:** diagnosticar el rechazo de navegación de la herramienta por vía
   soportada, sin eludir políticas; verificar flujos visibles y registrar evidencia.
5. **Fuentes:** cobertura1T/2T y equipos de fútbol; proveedor NBA independiente
   permitido. No evadir403 ni llamar independientes a dos endpoints ESPN.
6. **Calibración/confidence/odds:** evaluar por versión/deporte/mercado con muestras
   válidas, intervalos y disponibilidad histórica explícita; no fabricar calibrador.
7. **H4 integral:** actualizar preflight/backups/refs y recuperación antes de
   reescritura autorizada; no ejecutar purga parcial si refsGitHub retienen blobs.

## Dependencias medidas, no tareas humanas genéricas

| Frente | Estado | Condición de reanudación |
|---|---|---|
| Activación fútbol | No apta según protocolo actual | Frescura de corners/goles, ningún target corners peor, cobertura disparos>=90%; nuevo protocolo declarado antes de medir si corresponde |
| OutcomesNBA | Espera de evento | Resolver después de partidos16/10 23:00Z→17/10 02:30Z porUUID existente; no retrofechar |
| IndependenciaNBA | No acreditada | Proveedor permitido con identidad/instantes/resultados trazables; CDN403 no se sortea |
| P&L sin soportes | No recuperable controlado | Mantener exclusiones/ROI N/D; propietario confirma ausencia, no pedir pruebas inexistentes |
| H4 | Purga integral no acreditada | Alcance completo de refs y verificación de inaccesibilidad, no solo ramas |

**NO CERTIFICADO** permanece vigente. No hace falta recuperar cada apuesta ni
cerrar toda esta deuda para consulta exploratoria local. No hay login/2FA, compra
ni gestión personal GitHub identificada como requisito actual del propietario.

## Evidencias y antecedentes

- [Evaluación temporal](EVALUACION_TEMPORAL_FUTBOL_2026-10-16.md).
- [Persistencia ML](PERSISTENCIA_ML_FUTBOL_2026-10-15.md).
- [Operación/prospectiva](OPERACION_Y_PROSPECTIVA_2026-10-15.md).
- [Checklist de uso](CHECKLIST_PREPARACION_USO_2026-10-15.md).
- [Recertificación histórica](RECERTIFICACION_ANALITICA_2026-10-06.md).
- [Roadmap anterior íntegro](../archive/ROADMAP_ANTES_CONSOLIDACION_2026-10-16.md).

Cierre por bloque: objetivo, evidencia, pruebas proporcionales, diff/secretos,
estado/changelog y commit/push sin fuerza. Nunca marcar certificado por CI verde.
