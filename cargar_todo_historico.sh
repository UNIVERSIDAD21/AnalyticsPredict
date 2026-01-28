#!/bin/bash

# Script para cargar datos históricos de todas las ligas de fútbol
# Temporadas: 2018-19 hasta 2025-26

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Arrays de configuración
LIGAS=("laliga" "premier" "bundesliga" "seriea" "ligue1" "champions" "europa" "conference" "copa_rey" "fa_cup")
TEMPORADAS="2018-19,2019-20,2020-21,2021-22,2022-23,2023-24,2024-25,2025-26"

# Archivo de log
LOG_FILE="carga_historica_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}CARGA HISTÓRICA COMPLETA${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo "📋 Ligas a procesar: ${#LIGAS[@]}"
echo "📅 Temporadas: 2018-19 hasta 2025-26"
echo "📝 Log: $LOG_FILE"
echo ""

# Contador de éxitos y errores
EXITOSAS=0
FALLIDAS=0

# Procesar cada liga
for liga in "${LIGAS[@]}"; do
    echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}Procesando: ${liga^^}${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}\n"
    
    # Ejecutar el script
    python backend/scripts/cargar_historico_futbol_v3.py \
        --liga "$liga" \
        --temporadas "$TEMPORADAS" \
        --verbose 2>&1 | tee -a "$LOG_FILE"
    
    # Verificar resultado
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        echo -e "\n${GREEN}✅ $liga completada exitosamente${NC}\n"
        ((EXITOSAS++))
    else
        echo -e "\n${RED}❌ Error procesando $liga${NC}\n"
        ((FALLIDAS++))
    fi
    
    # Pausa pequeña entre ligas para no sobrecargar la API
    echo "⏳ Esperando 5 segundos antes de la siguiente liga..."
    sleep 5
done

# Resumen final
echo -e "\n${BLUE}================================${NC}"
echo -e "${BLUE}RESUMEN FINAL${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}✅ Ligas exitosas: $EXITOSAS${NC}"
echo -e "${RED}❌ Ligas fallidas: $FALLIDAS${NC}"
echo "📝 Log completo: $LOG_FILE"
echo ""