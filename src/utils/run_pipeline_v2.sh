#!/bin/bash

# QUICK START - Pipeline Maestro
# Ubicación: additive_info/run_pipeline.sh
# Ejecuta: python3 -m src.utils.pipeline_maestro
#
# Formas de ejecutar:
#   ./run_pipeline.sh              # Todo el pipeline
#   ./run_pipeline.sh 1            # Solo paso 1
#   ./run_pipeline.sh --step 1 2 3 # Pasos específicos

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║         FOOD SAFETY ANALYSIS PIPELINE v4.0 - QUICK START                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"

# Verificar si Python está disponible
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado"
    exit 1
fi

# Menú de opciones si no hay argumentos
if [ $# -eq 0 ]; then
    echo ""
    echo "Selecciona qué deseas ejecutar:"
    echo ""
    echo "  1) Todo el pipeline (PASO 1-5)"
    echo "  2) Solo PASO 1: Extracción de aditivos"
    echo "  3) Solo PASO 2: Clasificación SSI (⚠️ ~5-7 horas)"
    echo "  4) Solo PASO 3: Extracción de alimentos"
    echo "  5) Solo PASO 4: Fusión de datasets"
    echo "  6) Solo PASO 5: Clustering final"
    echo ""
    read -p "Selecciona una opción (1-6): " opcion
else
    opcion=$1
fi

echo ""

case $opcion in
    1)
        echo "🚀 Ejecutando TODO el pipeline (PASO 1-5)..."
        python3 -m src.utils.pipeline_maestro --step all
        ;;
    2)
        echo "🚀 Ejecutando PASO 1: Extracción de aditivos..."
        python3 -m src.utils.pipeline_maestro --step 1
        ;;
    3)
        echo "🚀 Ejecutando PASO 2: Clasificación SSI..."
        echo "⚠️  ADVERTENCIA: Este paso requiere ~5-7 horas"
        python3 -m src.utils.pipeline_maestro --step 2
        ;;
    4)
        echo "🚀 Ejecutando PASO 3: Extracción de alimentos..."
        python3 -m src.utils.pipeline_maestro --step 3
        ;;
    5)
        echo "🚀 Ejecutando PASO 4: Fusión de datasets..."
        python3 -m src.utils.pipeline_maestro --step 4
        ;;
    6)
        echo "🚀 Ejecutando PASO 5: Clustering final..."
        python3 -m src.utils.pipeline_maestro --step 5
        ;;
    *)
        echo "❌ Opción no válida"
        exit 1
        ;;
esac

echo ""
echo "✅ Pipeline ejecutado"
echo ""
echo "📁 Outputs guardados en: outputs/"
echo "📁 Logs guardados en: outputs/logs/"
echo ""
