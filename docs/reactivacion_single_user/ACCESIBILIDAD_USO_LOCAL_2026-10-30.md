# Teclado, etiquetas y legibilidad local — 2026-10-30

Continuación L24: revisión de nueve rutas iniciales × temas claro/oscuro × anchos
1366/390px =36 estados. Frontend compilado y API reales en modo base sin BD;
ningún análisis, ingesta, escritura de configuración ni POST durante el ensayo.

## Hallazgos corregidos

- Cuatro inputs numéricos de Configuración tenían texto visible sin asociación
  semántica. Ahora `label[for]`/`id` los nombran; `aria-invalid` y `aria-describedby`
  vinculan el error ya existente sin cambiar validaciones ni valores guardados.
- Los botones de perfil declaran su estado `aria-pressed`.
- Hoy, Base local, Cuaderno, Laboratorio y Baloncesto tenían el destino del salto
  al contenido sin foco programático. Ahora usan `tabIndex=-1`; no se añade el
  contenedor al orden normal de Tab. El navegador enfoca el contenido al activar
  con Enter el enlace de salto, sin recorrer toda la navegación.

Las36 comprobaciones finales verifican nombres de controles visibles, salto con
teclado real, destino enfocado, ancho y ausencia de errores JavaScript. En
Configuración también prueban un valor inválido, su mensaje asociado y estado
accesible, sin guardar la configuración.0 controles sin nombre/0overflow/0JS.

La revisión orientativa de contraste sobre texto/fondos uniformes no encontró
contrastes por debajo del umbral aplicado en esos estados. Fondos con imágenes o
gradientes, opacidad de ancestros, todos los diálogos/hover/gráficos/estados con
datos y lectores de pantalla reales **no quedan certificados** por este script.
No es una declaración WCAG ni una auditoría exhaustiva del producto.

Se conserva la evidencia inicial con los16 hallazgos repetidos (cuatro campos
×cuatro combinaciones de tamaño/tema) y las capturas finales auténticas. El tema
claro usa tokens con contraste propio; siguen existiendo decoraciones legacy.
Fuentes locales, foco visible, densidad/tamaño y `prefers-reduced-motion` del
primer bloque permanecen. No se añade librería ni servicio externo de accesibilidad.

Pruebas frontend, lint y build en recibo externo
`ACCESIBILIDAD_USO_LOCAL_2026-10-30`. Backend no cambia: no es necesario repetir
entrenamiento ni suites de BD para una asociación de etiquetas y foco.
