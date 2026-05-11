# Pipeline Maestro - Food Safety Analysis v4.0

## 📋 Descripción General

Script de orquestación que ejecuta el pipeline COMPLETO de análisis de seguridad alimentaria:

1. **Extracción de aditivos** (Open Food Facts)
2. **Análisis SSI** (Búsqueda en PubMed)
3. **Extracción de alimentos** (Open Food Facts)
4. **Fusión de datasets** (Multiprocessing)
5. **Clustering final** (K-Means K=4)

## 🚀 Uso Rápido

```bash
# Todo el pipeline
python3 pipeline_maestro.py --step all

# Paso específico
python3 pipeline_maestro.py --step 1  # Extracción aditivos
python3 pipeline_maestro.py --step 2  # SSI (⚠️ ~5-7h)
python3 pipeline_maestro.py --step 3  # Alimentos
python3 pipeline_maestro.py --step 4  # Fusión
python3 pipeline_maestro.py --step 5  # Clustering

# O usar el script bash
bash run_pipeline.sh                # Menú interactivo
```

## 📊 Pasos del Pipeline

### PASO 1: Extracción de Aditivos

- **Input**: API de Open Food Facts
- **Output**: `maestro_aditivos_limpio.csv` (651 aditivos)
- **Tiempo**: ~2 min
- **Qué hace**:
  - Descarga taxonomía de aditivos
  - Limpia códigos E
  - Estandariza nombres

```python
paso_1_extraccion_aditivos()
```

### PASO 2: Clasificación SSI (⚠️ MUY LARGO)

- **Input**: `maestro_aditivos_limpio.csv`
- **Output**: `ssi_final_con_semaforo.csv` (651 aditivos clasificados)
- **Tiempo**: ~5-7 horas
- **Qué hace**:
  - Busca en PubMed: ~16k búsquedas
  - Calcula SSI scores (fórmula balanceada)
  - Asigna semáforo (🟢 SEGURO, 🟡 PRECAUCIÓN, 🔴 EVITAR)
  - Usa checkpoints automáticos

```python
paso_2_clasificacion_aditivos(df_aditivos)
```

**⚠️ NOTA**: Cambiar `PUBMED_EMAIL` con tu email antes de ejecutar.

### PASO 3: Extracción de Alimentos

- **Input**: API de Open Food Facts
- **Output**: `dataset_800k_aditivos.csv` (836k alimentos)
- **Tiempo**: ~5-10 min
- **Qué hace**:
  - Descarga 836k alimentos
  - Extrae: Nutriscore, NOVA, aditivos
  - Genera one-hot encoding de aditivos

```python
paso_3_extraccion_alimentos()
```

### PASO 4: Fusión de Datasets

- **Input**: `maestro_aditivos_limpio.csv` + `dataset_800k_aditivos.csv`
- **Output**: `alimentos_con_semaforo_final.csv` (836k alimentos con conteos)
- **Tiempo**: ~2-3 min (con multiprocessing)
- **Qué hace**:
  - Mapea aditivos → semáforo
  - Cuenta aditivos por categoría (SEGURO/PRECAUCIÓN/EVITAR)
  - Usa `joblib.Parallel` para paralelizar en todos los cores

```python
paso_4_fusion(df_aditivos, df_alimentos)
```

### PASO 5: Clustering Final

- **Input**: `alimentos_con_semaforo_final.csv`
- **Output**: `alimentos_clasificacion_final_completa.csv` (12 categorías)
- **Tiempo**: ~5 min
- **Qué hace**:
  - K-Means con K=4
  - Identifica aditivo dominante por alimento
  - Crea clasificación final: `cluster_ID_aditivo_dominante`
  - Genera 12 categorías (4 clusters × 3 subclases)

```python
paso_5_clustering(df_alimentos)
```

## 📁 Estructura de Directorios

```
proyecto/
├── pipeline_maestro.py          # Script principal
├── run_pipeline.sh              # Bash wrapper (menú interactivo)
├── utils/
│   ├── ssi_pipeline.py          # Funciones SSI
│   └── food_classification_pipeline.py  # Funciones clustering
├── data/
│   ├── maestro_aditivos_limpio.csv
│   ├── ssi_final_con_semaforo.csv
│   ├── dataset_800k_aditivos.csv
│   └── alimentos_con_semaforo_final.csv
├── models/
│   ├── scaler_alimentos.pkl
│   └── kmeans_alimentos.pkl
└── outputs/
    ├── alimentos_clasificacion_final_completa.csv
    ├── plots/
    │   └── food_products/
    │       ├── dendrograma_ward.png
    │       └── ...
    └── logs/
```

## ⚙️ Configuración

Editar `Config` en `pipeline_maestro.py`:

```python
class Config:
    DATA_DIR = Path('../data')              # Directorio de datos
    MODELS_DIR = Path('../models')          # Directorio de modelos
    OUTPUTS_DIR = Path('../outputs')        # Directorio de outputs
    PUBMED_EMAIL = "tu_email@ejemplo.com"   # ← CAMBIAR ESTO
```

## 📊 Resultados Esperados

### Distribución Final

```
Cluster 0 (Falso Saludable):           176,894 alimentos (21.1%)
Cluster 1 (Simple Malo):                344,688 alimentos (41.2%)
Cluster 2 (Verdaderamente Saludable):   130,602 alimentos (15.6%)
Cluster 3 (Ultraprocesado):             184,543 alimentos (22.1%)
────────────────────────────────────────────────────
TOTAL:                                  836,897 alimentos
```

### 12 Categorías Finales

```
0_SEGUROS       0_PRECAUCION      0_EVITAR
1_SEGUROS       1_PRECAUCION      1_EVITAR
2_SEGUROS       2_PRECAUCION      2_EVITAR
3_SEGUROS       3_PRECAUCION      3_EVITAR
```

### Métricas de Clustering

```
Silhouette Score:      0.4100  (Bueno para datos reales)
Davies-Bouldin Index:  1.2500  (Bajo es mejor)
Calinski-Harabasz:     2100.50 (Alto es mejor)
```

## 🔄 Checkpoints y Reanudación

El pipeline usa checkpoints automáticos:

- **PASO 2**: Checkpoint cada 10 aditivos (`ssi_checkpoint.csv`)
- **Reanudar**: Automático si existe checkpoint previo

Si quieres limpiar checkpoints:

```bash
rm ../data/ssi_checkpoint.csv
rm ../data/ssi_progress.txt
```

## ⚠️ Requisitos

```bash
pip install pandas numpy scikit-learn scipy matplotlib seaborn plotly joblib requests
```

## 🎯 Casos de Uso

### Ejecutar TODO (Primera vez)

```bash
python3 pipeline_maestro.py --step all
```

### Actualizar solo clasificación de alimentos

```bash
# Si los aditivos ya están procesados
python3 pipeline_maestro.py --step 4
python3 pipeline_maestro.py --step 5
```

### Reanudar SSI interrumpido

```bash
python3 pipeline_maestro.py --step 2
# Continúa desde donde se paró
```

## 📈 Rendimiento

### Tiempos esperados (836k alimentos)

| Paso            | Tiempo          | Paralelizable                   |
| --------------- | --------------- | ------------------------------- |
| 1. Aditivos     | 2 min           | No                              |
| 2. SSI          | 5-7h            | Sí (si se ejecuta en paralelo) |
| 3. Alimentos    | 5-10 min        | No                              |
| 4. Fusión      | 2-3 min         | Sí (joblib multicore)          |
| 5. Clustering   | 5 min           | Sí                             |
| **TOTAL** | **~5-7h** |                                 |

### Optimizaciones aplicadas

- ✅ PASO 4: `joblib.Parallel` con `n_jobs=-1`
- ✅ PASO 2: Checkpoints cada 10 aditivos
- ✅ PCA solo para visualización, NO para clustering

## 🐛 Troubleshooting

### Error: "Módulo no encontrado"

```bash
export PYTHONPATH="${PYTHONPATH}:./utils"
python3 pipeline_maestro.py --step all
```

### PASO 2 interrumpido

No hay problema, tiene checkpoints:

```bash
python3 pipeline_maestro.py --step 2
# Continúa desde donde se paró
```

### Memoria insuficiente en PASO 4

Reduce el tamaño del batch:

```python
# En paso_4_fusion():
for i in range(0, len(df_alimentos), 100000):  # Procesar en chunks
    ...
```

## 📚 Documentación Completa

- `ssi_pipeline.py`: Detalles de cálculo SSI
- `food_classification_pipeline.py`: Detalles de clustering
- Notebooks: 01_extraccion → 05_clasificacion (proceso paso a paso)

## 🎓 Interpretación de Resultados

### ¿Qué significan los 4 clusters?

**Cluster 0: Falso Saludable**

- Nutriscore: 2.28 (parece bueno)
- NOVA: 3.65 (pero muy procesado)
- Aditivos: 1.39 (pocos)
- Ejemplo: Zumo de naranja "natural" (ultraprocesado)

**Cluster 1: Simple Malo**

- Nutriscore: 4.54 (malo)
- NOVA: 3.67 (procesado)
- Aditivos: 1.74 (pocos)
- Ejemplo: Refrescos, snacks salados

**Cluster 2: Verdaderamente Saludable**

- Nutriscore: 1.93 (excelente)
- NOVA: 1.17 (natural)
- Aditivos: 0.06 (casi ninguno) ✅
- Ejemplo: Frutas, verduras, alimentos frescos

**Cluster 3: Ultraprocesado**

- Nutriscore: 4.18 (malo)
- NOVA: 4.00 (ultraprocesado)
- Aditivos: 8.97 (MUCHOS) ⚠️
- Ejemplo: Productos ultra-procesados industriales

## 📞 Soporte

Para problemas:

1. Revisa logs en `../outputs/logs/`
2. Verifica checkpoints en `../data/`
3. Consulta los notebooks originales para debugging

---

**Versión**: 4.0
**Última actualización**: 2025-05-11
**Estado**: Producción ✅
