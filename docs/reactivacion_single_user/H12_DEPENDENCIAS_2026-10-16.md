# H12: dependencias y mantenimiento específico — 2026-10-16

**Avance parcial, no cierre H12.** Auditoría del árbol de desarrollo pasó de
10avisos(3moderados/7altos) a **5altos**. Producción permanece con **0**.
No se suprimen advisories ni se ejecuta `npm audit fix --force`.

## Cambios y compatibilidad

- Vite5.4.21→7.3.7 y pluginReact4→5.2.0, con peer compatible. Node declarado
  `^20.19.0 || >=22.12.0`; CI usa20actual, host24.21.0.
- Overrides explícitos para picomatch<2.3.2→2.3.2 y
  postcss-selector-parser<7.1.6→7.1.6. Se preserva Tailwind3, sin migración visual
  a4. El override del parser cruza major: compatibilidad comprobada con compilación
  real, no asumida por el mero resultado de auditoría.
- `npm ci` desde lock,27testsfrontend,lint/build y auditoría producción verdes.
- CSS Tailwind antes/después **idéntico byte a byte**, SHA256
  `6e2dbf52ebeed848c956d5a54d67139b1e24ec3dcec3fece27c956b496c527ff`.
- `favicon.ico` servido estaba vacío y declarado como SVG. Copia original externa,
  sustituido por favicon.svg válido y referencia HTML coherente; HTTP200/MIMEsvg.
- Inventario de modos contra índice: **0discrepancias**, sin chmod. Los30cambios
  observados en el respaldo histórico no se tocan. Los dos `__init__.py` vacíos
  restantes son marcadores de paquete intencionales, no datos/reportes fabricados.

## Residuo real

Cinco avisos altos en la cadena braces/chokidar/micromatch/fast-glob/tailwindcss:
[GHSA-vfj7-8cjw-p6xm](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm).
Al corte, `npm view braces version` devuelve3.0.3 y el advisory afecta<=3.0.3;
3.0.4 no está publicada. La última Tailwind3 publicada también conserva esa cadena.

Eliminar el residuo exige una corrección upstream o sustituir/migrar la cadena
con pruebas y revisión visual propias. No se presenta una versión inexistente,
un override de nombre o una ocultación de auditoría como solución. H12 y su revisión
de rot más amplia siguen abiertos. No afecta el dato de producción0, pero tampoco
se minimizan los avisos de herramientas de desarrollo por ese motivo.

## Operación y evidencias

Servicios locales8000/5173 reanudados tras reinicio del host, loopback y
`AUTO_KILL_PORTS=false`, sin autoentrenar ni parar procesos ajenos; salud/Estado
frontend/faviconHTTP200. Esto no es despliegue público ni revisión visual.
Browsergestionado/CDPsanos, pero apertura5173 rechazada de nuevo por política;
configuración browser sin excepciónSSRF explícita y esquema con bloqueo privado
por defecto. No se altera política global ni se elude por otra ruta. Diagnóstico
pertenece al agente, no es falta de autorización del propietario.

Evidencia externa `H12_DEPENDENCIAS_DESARROLLO_2026-10-16`: auditorías completas,
copias package/lock anteriores, CSS antes/después, permisos/vacíos, npmci/tests/
lint/build, favicon original y HTTP. CI/commit se verifican en acta externa.
