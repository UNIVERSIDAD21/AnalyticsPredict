# Reparación histórica analítica autorizada — 2026-10-25

El propietario aprobó expresamente el plan fijo de 99 registros sobre 25 partidos.
Aplicación transaccional única confirmada: 65 filas de `apuestas_analizadas`, seis
de `predicciones_futbol` y 28 de `predicciones_registradas`. Cambió el valor real
en las 99 y el outcome en 45 (31 y 14, respectivamente). Las seis de tiros al arco
conservan UNDER; sus valores observados se corrigieron.

Los 65 textos legados «Resultado final: 0-0» se sustituyeron por el mercado y su
valor observado. Los triggers existentes actualizaron `actualizado_en` en las 34
predicciones. No se cambiaron probabilidades, líneas, lados, cuotas, importes,
modelos, payloads de emisión ni fechas originales de generación/resolución.

## Controles realizados

1. SHA-256 del plan, las 99 filas y sus 25 fuentes coincidieron antes de escribir.
2. Respaldo lógico privado de todas las columnas; esquema/tipos y triggers de
   timestamp revisados. Restauración exacta en PostgreSQL16 aislado, no una
   restauración completa de la BD. Nueve pruebas de restauración, rollback,
   rechazo de campos/IDs/fuentes ajenos, fallo intermedio e idempotencia aprobadas.
3. Ensayo en la BD real con `force_rollback=True`; lectura posterior independiente
   confirmó las 99 filas originales y 22 tablas protegidas sin modificaciones.
4. Aplicación atómica con locks y comparación de filas/fuentes/campos; cualquier
   fallo revierte el lote. La evidencia del intento se guardó antes del commit.
5. Postflight READ ONLY y cálculo independiente directo de los cuatro mercados
   afectados verificaron 99/99. Una nueva simulación propone cero cambios.
6. Las 22 tablas protegidas permanecieron idénticas fuera del lote; las 40
   predicciones no comparables y los pendientes quedaron fuera de la operación.

No se ejecutó el ciclo global de liquidación ni se cerraron los 306 pendientes
resolubles observados en el diagnóstico anterior. No hubo apuestas financieras,
ingesta, fuentes nuevas, entrenamiento, calibración ni publicación de artefactos.
Corregir outcomes retrospectivos no certifica precisión ni anterioridad de emisión.

El código funcional anterior sigue local sin commit/push ni CI remota nueva. En
este encargo solo se actualizó documentación dentro del producto; los scripts de
la operación y datos de respaldo permanecen privados fuera del repositorio.

Entrega externa `REPARACION_99_REGISTROS_ANALITICOS_2026-10-25`: autorización, plan,
respaldo, pruebas, ensayo, recibo de commit, postflight e inventario de integridad.
No repetir la aplicación. Para cualquier reparación adicional preparar otro
alcance y autorización, sin ampliar los IDs de este plan.
