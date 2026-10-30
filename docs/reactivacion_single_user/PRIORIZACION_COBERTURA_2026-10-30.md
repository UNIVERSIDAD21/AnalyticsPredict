# Cobertura según uso personal — 2026-10-30

## Implementado

Laboratorio reutiliza favoritos y cuaderno de este navegador. Orden lexicográfico
explícito: liga favorita, cantidad de equipos/competiciones favoritos, copias
guardadas. Empates conservan orden del catálogo. No cuenta las copias como partidos
únicos ni como frecuencia real de uso; no combina eficacia y preferencia.
No equipara un favorito por nombre con un ID de otra liga/BD.

El corte del artefacto permanece separado de la cobertura de BD. Abrir Laboratorio,
cambiar preferencias o ventana no conecta al inventario de BD. El botón explícito
consulta `GET /api/local/cobertura?dias=365`; soporta1–1095días, interfaz30/90/365.
La API abre transacción `READ ONLY` y ejecuta dos SELECT agregados por competición.
No inicia sincronización, red de fuentes, entrenamiento, reparación o ingesta.

Ventana de días calendario en Colombia, desde medianoche inclusiva hasta instante
observado. Fútbol tiene límite temporal con zona; baloncesto conserva precisión
diaria y no acredita hora. Se retornan ID/código/nombre, registros, finales válidos
con marcador y conteos de campos presentes dentro de esos finales. Catálogo vacío
o competición sin registros se distinguen de error; cero publicado no se imputa.
Fútbol0–0 es final válido. Un valor NULL no se convierte en cero observado.

Error503 no incluye detalle del driver/credenciales ni tabla con ceros. Si había
lectura previa, se conserva rotulada como anterior, no como actualización exitosa.
Una selección de ventana nueva no reetiqueta la lectura anterior. Cancelación al
salir evita aplicar respuestas tardías. Preferencias dañadas no se sobrescriben ni
exportan como un plan vacío válido. Exportación local conserva prioridades,
artefactos, ventana/observación, inventario disponible y señal de último fallo.

## Límites y estado L14

**Parcial**: mecanismo implementado y verificado, pero no hay medición productiva
vigente por cuota del origen. No se volvió a intentar Neon para estas pruebas.
No se dispone de calendario oficial conciliado: completitud oficial N/D. Contar
campos presentes no valida coherencia, fases, OT, mitad, fuente, elegibilidad,
actualidad ni muestra del predictor. No es una autorización para llenar huecos.
No atribuye a favoritos/copias preferencias que el Jefe todavía no haya guardado.

Para cerrar: con fuente vigente legible, consultar una vez la ventana apropiada,
conciliar IDs exactos de las competiciones prioritarias y conservar recibo. Si se
solicita reparar un gap, definir cobertura/fuente y ensayo aislado antes de ingesta.
No cambia las cohortes, calibradores o artefactos del catálogo científico.

## Verificación

403backend conPG18 sintético aprobadas/0omitidas. SQL real comprueba límites de
ventana COT, exclusión de futuro e inválidos, 0–0, NULL, competición vacía y
conteos de campos. API verifica READ ONLY, validación de rango sin abrir pool y
error sanitizado que no inventa cero. Frontend comprueba orden, ligas separadas,
ausencia de consulta automática, ventana explícita, error N/D, lectura anterior y
almacenamiento dañado. Conteos finales, lint/build, captura rotulada, integración y
CI se conservan fuera del producto en `PRIORIZACION_COBERTURA_PERSONAL_2026-10-30`.
