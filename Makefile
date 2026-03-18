.PHONY: help dev backend frontend calidad-ciclo calidad-ciclo-fast reporte-ejecutivo qa-preflight reporte-semanal-template reporte-semanal-auto export-metricas-csv snapshot-tendencias revision-politica check-modo-estricto cierre-operativo estado-unificado operacion-diaria-full reporte-b3-estabilidad

help:
	@echo "Targets disponibles:"
	@echo "  make dev                  # Levanta entorno local"
	@echo "  make backend              # Inicia API backend"
	@echo "  make frontend             # Inicia frontend"
	@echo "  make calidad-ciclo        # Ejecuta ciclo completo de calidad"
	@echo "  make calidad-ciclo-fast   # Ciclo de calidad rápido"
	@echo "  make reporte-ejecutivo    # Genera reporte ejecutivo"
	@echo "  make qa-preflight         # Validaciones previas"
	@echo "  make operacion-diaria-full# Pipeline diaria completa"
	@echo "  make reporte-b3-estabilidad# Reporte semanal B3 por liga"

dev:
	bash scripts/dev.sh

backend:
	cd backend && python3 -m uvicorn app:app --reload --host 0.0.0.0 --port 8000

frontend:
	cd frontend && npm run dev -- --host 0.0.0.0 --port 5173

calidad-ciclo:
	bash scripts/ciclo_calidad.sh

calidad-ciclo-fast:
	LIMITE_BASKET=300 LIMITE_FUTBOL=300 MIN_MUESTRAS=20 bash scripts/ciclo_calidad.sh

reporte-ejecutivo:
	bash scripts/reporte_ejecutivo_calidad.sh

qa-preflight:
	bash scripts/qa_preflight.sh

reporte-semanal-template:
	bash scripts/reporte_semanal_stub.sh

reporte-semanal-auto:
	bash scripts/reporte_semanal_auto.sh

export-metricas-csv:
	bash scripts/export_metricas_csv.sh

snapshot-tendencias:
	bash scripts/snapshot_tendencias.sh

revision-politica:
	bash scripts/revision_politica_mercados.sh

check-modo-estricto:
	bash scripts/check_modo_estricto.sh

cierre-operativo:
	bash scripts/cierre_operativo.sh

estado-unificado:
	bash scripts/estado_unificado.sh

operacion-diaria-full:
	bash scripts/operacion_diaria_full.sh

reporte-b3-estabilidad:
	bash scripts/reporte_b3_estabilidad.sh
