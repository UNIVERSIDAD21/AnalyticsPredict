# Scripts de validación comercial histórica

`validar_a6_rca.sh` se conserva aquí como evidencia del gate RC-A de la etapa comercial C0–C7. No es un comando operativo single-user: exige `backend/tests/api/test_auth_endpoints.py`, retirado con la eliminación de auth, y genera un reporte de release comercial. No ejecutarlo para certificar la aplicación actual. La CI vigente en `.github/workflows/ci.yml` reemplaza sus verificaciones automatizadas.
