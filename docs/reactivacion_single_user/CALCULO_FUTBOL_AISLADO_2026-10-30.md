# Cálculo y lecturas de fútbol separados de HTTP — 2026-10-30

L27, extracción acotada al flujo intervenido; no reescritura de la aplicación.

- `motor_futbol/prediccion/distribuciones_contextuales.py`: normal, Poisson,
  binomial negativa y Dixon-Coles1X2 del estimador contextual existente.
- `servicios/lecturas_analisis_futbol.py`: lecturas por equipo, competición y H2H.
  Reciben un cursor: no crean pool/conexión, no escriben, entrenan ni confirman
  transacciones. Se conservan el corte exclusivo, temporadas/fallback y sede.
- La ruta HTTP mantiene orquestación, validaciones, transacción, calibradores y
  formato de respuesta. Importa las nueve funciones previas como alias compatibles
  para sus consumidores/test, sin mantener copias duplicadas de la implementación.

269 líneas de cuerpos se trasladaron sin cambio lógico. Antes de editar se
conservaron resultados sintéticos y SQL/params/salida. Después: **536 cálculos
idénticos en representación hexadecimal de float y72 consultas idénticas**,
cero intentos de red/subproceso con instrumentación Python. No datos deportivos
reales, consulta productiva ni comparación de eficacia. El baseline externo y su
hash permiten revisar diferencias sin regenerar silenciosamente el esperado.

395 pruebas backend aprobadas con PostgreSQL18 sintético exclusivo/0omitidas;
incluyen contratos HTTP, elegibilidad, reconstrucción, alcance,1X2 y los nuevos
tests de matemática/lectura. CI incorpora el módulo de test también en Windows.
Frontend no cambia: no se repite su suite para mover código Python.

Se preservan intencionalmente las aproximaciones legacy: truncamiento de1X2,
fallback sigma, mínimos de media y parametrización NB. Esta extracción **no**
repara/calibra la distribución, estima nuevos parámetros por competición ni
resuelve el push de contratos que antes no conservaban masa. Tampoco certifica
eficacia por cambiar carpetas. Esas mejoras tienen su propio protocolo y datos.

Quedan orquestación y otras funciones históricas en la ruta: L27 no exige ni
declara una reescritura completa. El alcance implementado ahora separa cálculo
NBA base y matemática/lecturas de fútbol, con equivalencia y regresiones. No se
introducen cachés, frameworks, consultas nuevas ni cambios de modelo/BD activa.

Entrega externa `CALCULO_FUTBOL_AISLADO_2026-10-30`: baseline antes del cambio,
recibo de equivalencia, pruebas, fuentes por SHA, integración y manifiesto.
