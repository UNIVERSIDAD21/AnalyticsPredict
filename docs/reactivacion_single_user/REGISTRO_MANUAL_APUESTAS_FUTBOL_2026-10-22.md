# Registro manual de apuestas de fútbol — 2026-10-22

## Hallazgo

La pantalla de resultados permitía abrir el formulario de guardado únicamente si
el motor devolvía una recomendación exactamente coincidente con mercado, lado y
línea. Así, una selección válida del usuario quedaba bloqueada cuando no había
recomendación, pese a que el componente común de resultados presenta el guardado
como disponible incluso cuando no hay candidatos aptos.

## Corrección

- Fútbol permite abrir el formulario y registrar la selección válida del usuario,
  tanto cuando existe una recomendación exacta como cuando se trata de una
  selección manual. El modal distingue ambos casos.
- Se guarda la cuota del lado seleccionado (`OVER` o `UNDER`), no la primera cuota
  disponible de cualquier lado.
- Se conserva la probabilidad del objetivo solo cuando el análisis la expone para
  esa misma selección. Confianza y valor esperado quedan `NULL` si no hay una
  recomendación exacta; no se fabrican probabilidades, confianza ni EV.
- El endpoint de fútbol mantiene la escritura por dominio en `apuestas_futbol`,
  que ya forma parte de la lectura canónica `GET /api/bitacora/unificada`.
  La respuesta y los lectores de apuestas preservan valores `NULL` como N/D.

## Validación y límites

- Backend: `tests/api/test_rutas_futbol.py` y `tests/api/test_apuestas_futbol_contract.py`,
  27 pruebas aprobadas; incluyen persistencia simulada con y sin snapshot analítico.
- Frontend: 4 pruebas focalizadas aprobadas; lint y `tsc -b`/build aprobados.
- `git diff --check` aprobado. PostgreSQL consultado solo para metadatos de columnas
  y enums dentro de una transacción READ ONLY.
- No se envió POST a la base productiva ni se creó, modificó o eliminó apuesta real.
- No se modificaron modelos, resultados, cohortes ni configuración de apuestas.

El formulario guarda una entrada de bitácora a solicitud del usuario. No certifica
el análisis, recomienda una apuesta ni acredita eficacia, calibración o ROI.
