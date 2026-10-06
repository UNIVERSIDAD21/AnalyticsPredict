# H9 — métricas probabilísticas, avance verificable

**Estado:** EN CURSO. Este cambio no certifica modelos ni cierra H9.

## Definición y alcance

`backend/metricas_probabilisticas.py` define Brier como media de `(p-y)^2`, Log Loss binaria en nats con clipping numérico `1e-15` y ECE como suma ponderada de gaps absolutos en 10 bins fijos `[0,.1), …, [.9,1]`. Solo entran pares binarios completos con `p∈[0,1]`; sin pares válidos las tres métricas son `null`, no cero. `n` es la cantidad efectivamente medida. La raw es la salida anterior a calibración; la calibrada exige transformación real y procedencia, no igualdad de nombres de columnas.

## Checklist y evidencia

- [x] Inventariar productores/consumidores activos en `backend/api`, `backend/backtesting`, `backend/calidad`, `backend/motor_futbol`, `backend/scripts` y `frontend/src` mediante búsqueda de `brier`, `log_loss`, `ece` y `calibration_error`.
- [x] Unificar fórmulas numéricas de rutas Python principales y el corte agregado; probar pares conocidos, extremos 0/1, ausencia de muestra y comparación NBA/fútbol.
- [x] Separar series raw/calibrada del calculador NBA; ausencia de calibrada devuelve `null` y cobertura parcial genera alerta, no fallback silencioso.
- [x] Impedir que el corte agregado llame calibrada a una predicción sin `calibrador_id`; el endpoint de calibración fútbol exige esa procedencia y compara Brier sobre pares coincidentes.
- [x] Retirar del script de scorecard fútbol el ECE=1 sin datos, `resolved_rate=1` y el claim no comprobado de ausencia de leakage. Este script queda no promocionable mientras no demuestre corte temporal y estado operativo.
- [ ] Corregir inferencia/persistencia fútbol que aún copia raw en campos `*_calibrada` y conserva ausencia de `calibrador_id`.
- [ ] Revisar y alinear consumidores SQL/reportes legacy que todavía aplican clipping distinto o `COALESCE` sin procedencia, y verificar todos los mercados NBA/fútbol con datos actuales.
- [ ] Ejecutar pruebas completas backend y frontend y verificar representación N/D en todas las superficies antes de cerrar H9.

## Criterio de aceptación

- [ ] Una única definición operativa para Brier, Log Loss y ECE en rutas actuales y reportes vigentes.
- [ ] Ningún campo calibrado se publica sin transformación y procedencia verificable.
- [ ] Ausencia de datos o de muestra equivalente aparece N/D; los conteos acompañan la métrica.
- [ ] Backend, frontend y contratos pasan en entorno reproducible.

## Pruebas y límites

En el checkout: 66 pruebas dirigidas pasan con `DATABASE_URL` vacío. Esto no incluye suite global, PostgreSQL efímera ni prueba de interfaz. El corte read-only previo documentó fútbol 567/567 `p_calibrada == p_raw` sin `calibrador_id`; no se han alterado esas filas. El análisis retrospectivo permanece **NO CERTIFICADO**.

**Siguiente acción:** reparar el flujo real de calibradores de fútbol (carga, ID, inferencia y persistencia), después recorrer los consumidores restantes y ejecutar gates completos. No promover mercado ni afirmar rentabilidad por estos cambios.
