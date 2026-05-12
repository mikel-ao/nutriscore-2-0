# Nutriscore 2.0: Sistema Inteligente de Clasificación Alimentaria

> **Continuación de:** [Análisis Exploratorio de Datos - Nutriscore es Incompleto y Manipulable](link_a_eda_anterior)

## 📋 Resumen Ejecutivo

Este proyecto es la **evolución del análisis exploratorio previo** que concluyó que el **Nutriscore clásico** (basado únicamente en nutrientes) es incompleto y puede ser manipulable. 

**Nutriscore 2.0** resuelve esto combinando **3 dimensiones de evaluación:**
- ✅ **Calidad nutricional** (Nutriscore 1-5)
- ✅ **Grado de procesamiento** (NOVA 1-4)  
- ✅ **Seguridad de aditivos** (Scientific Safety Index - SSI)

**Resultado:** Clasificación holística en **4 clusters** con **12 categorías finales**, validada con dos métodos independientes (K-Means + Hierarchical Clustering).

---

## 🎯 Contexto del Problema

### ¿Por qué Nutriscore 2.0?

En 2026, **millones de alimentos** circulan en mercados europeos, pero los consumidores solo tienen **UN etiquetado global**: Nutriscore. Sin embargo:

| Limitación | Impacto |
|-----------|---------|
| Solo analiza **nutrientes** | Ignora si es ultraprocesado |
| No considera **aditivos químicos** | Un "Nutriscore A" puede tener 651 aditivos permitidos pero riesgosos |
| Susceptible a **optimización de formulación** | Empresas pueden mejorar score sin mejorar salud |

**Caso de uso real:** Un zumo de fruta "natural" puede tener:
- ✅ Nutriscore A (bien)
- ❌ NOVA 3-4 (ultraprocesado)
- ⚠️ Aditivos de precaución no visibles en etiqueta

---

## 📊 Análisis de Datos

### Dataset Principal

| Métrica | Valor |
|---------|-------|
| **Alimentos totales** | 836,897 |
| **Aditivos únicos analizados** | 651 |
| **Papers científicos consultados** | 10,400+ (PubMed) |
| **Distribución Nutriscore** | A(15%), B(11%), C(21%), D(24%), E(29%) |
| **Alimentos ultraprocesados (NOVA 3-4)** | 55-60% |

### Distribuciones Clave

```
🔴 PROBLEMA: 53% de alimentos tienen Nutriscore D-E (pobre)
🔴 PROBLEMA: 55-60% son ultraprocesados (NOVA 3-4)
🔴 PROBLEMA: 40-45% contienen 1-3 aditivos; 5-10% contienen 8+ aditivos
```

**Visualización completa:** Ver `results/figures/eda/` para gráficos de distribuciones.

---

## 🔍 Metodología

### Etapa 1: Clasificación de Aditivos (Scientific Safety Index)

**Proceso:**
1. Búsqueda en **PubMed API** de 651 aditivos × 16 palabras clave = 10,400 búsquedas
2. Extracción de papers por categoría: negativos, positivos, estudios humanos vs animales
3. Filtros inteligentes:
   - Negaciones semánticas: "no dañino" reduce peso de "adverso"
   - Ponderación por tipo de estudio: In vitro ×0.30, animal ×0.50, humano ×1.00
4. **Cálculo SSI:** Fórmula que combina evidencia científica + recencia + confianza
5. Validación contra **EFSA oficial** (si aditivo fue retirado → EVITABLE)

**Resultado:**

```
🟢 SEGURO:      475 aditivos (73%)
🟡 PRECAUCIÓN:   84 aditivos (13%)
🔴 EVITABLE:     92 aditivos (14%)
```

**Código:** `notebooks/01_ssi_aditivos.ipynb`

---

### Etapa 2: Clustering de Alimentos (K-Means + Validación Jerárquica)

**Features seleccionados:**
```python
features = [
    'nutriscore_grade',    # Calidad nutricional (1-5)
    'nova_group',          # Grado de procesamiento (1-4)
    'total_aditivos'       # Cantidad de aditivos (0-20+)
]
```

**¿Por qué estos 3?** Representan las 3 dimensiones independientes de riesgo nutricional.

**Determinación de K:**

| Método | Resultado |
|--------|-----------|
| **Elbow Method** | Codo claro en K=4 |
| **Silhouette Score (K=4)** | 0.41 (Bueno) |
| **Hierarchical Clustering (WARD)** | 4 ramas naturales en altura ~53 |

![Elbow Plot](results/figures/metodo_codo_alimentos2.png)
![Silhouette Score](results/figures/silhouette_4_clusters2.png)
![Dendrograma Validación](results/figures/dendrograma_ward_validacion.png)

**Conclusión:** K=4 validado por dos métodos independientes → **ROBUSTO**.

**Código:** `notebooks/02_kmeans_clustering.ipynb`

---

## 📈 Resultados: Los 4 Clusters

### Matriz de Perfiles

![Matriz de Perfiles de Clusters](results/figures/matriz2.png)

### Perfil Detallado de Cada Cluster

#### **Cluster 0: "Falso Saludable"** (21.1% = 176,894 alimentos)

```
Nutriscore:    2.28  ✅ Parece bueno
NOVA:          3.65  ⚠️ Pero ultraprocesado
Aditivos:      1.39  (pocos)

Ejemplos típicos: Zumos "naturales", yogures de dieta, batidos
Riesgo: ENGAÑOSO - Marketing saludable, realidad ultraprocesada
```

#### **Cluster 1: "Simple Malo"** (41.2% = 344,688 alimentos)

```
Nutriscore:    4.54  ❌ Pobre
NOVA:          3.67  ⚠️ Procesado
Aditivos:      1.74  (pocos)

Ejemplos típicos: Refrescos, snacks salados, bollería
Riesgo: CLARO pero "simple" - al menos sabes lo que obtienes
```

#### **Cluster 2: "Verdaderamente Saludable"** (15.6% = 130,602 alimentos)

```
Nutriscore:    1.93  ✅ Excelente
NOVA:          1.17  ✅ Natural
Aditivos:      0.06  ✅✅ CASI NINGUNO

Ejemplos típicos: Frutas frescas, verduras, legumbres naturales
Riesgo: MÍNIMO - La mejor opción
```

#### **Cluster 3: "Ultraprocesado"** (22.1% = 184,543 alimentos)

```
Nutriscore:    4.18  ❌ Malo
NOVA:          4.00  🔴 MÁXIMO procesado
Aditivos:      8.97  ⚠️⚠️ MUCHOS

Ejemplos típicos: Ultraprocesados industriales, comida lista para comer
Riesgo: MÁXIMO - Evitar cuando sea posible
```

### Visualización 3D

![Scatter Plot 3D de Clusters](results/figures/dispersion.png)

**Interpretación:**
- Cada punto = 1 alimento (836k puntos)
- X = Nutriscore (1-5), Y = NOVA (1-4), Z = Total aditivos (0-20+)
- Colores = Clusters K-Means
- Separación clara y natural entre grupos

**Código:** `notebooks/03_visualizacion_resultados.ipynb`

---

## 🎓 Clasificación Final: Nutriscore 2.0

### Arquitectura de Categorización (4 × 3 = 12)

**Punto clave:** Cada alimento tiene DOS dimensiones:

```
┌─────────────────────────────────────────────────┐
│                   ALIMENTO                       │
├─────────────────────────────────────────────────┤
│                                                   │
│  1️⃣  CLUSTER (K-Means sobre 836k)               │
│      └─ Determinado por: Nutriscore + NOVA      │
│         + Cantidad total de aditivos             │
│         └─ Resultado: Cluster 0, 1, 2 ó 3       │
│                                                   │
│  2️⃣  RIESGO DE ADITIVOS (SSI por aditivo)       │
│      └─ Determinado por: PEOR aditivo presente  │
│         ├─ Si hay 1+ aditivo EVITABLE → EVITABLE│
│         ├─ Si hay 1+ aditivo PRECAUCIÓN → PRECAU│
│         └─ Si todos SEGUROS o sin aditivos → SEGURO
│                                                   │
│  CATEGORÍA FINAL = Cluster_Riesgo_Aditivos      │
│  Ej: 0_EVITABLE, 2_SEGUROS, 3_PRECAUCIÓN       │
│                                                   │
└─────────────────────────────────────────────────┘
```

### Algoritmo de Categorización

```python
def categorizar_alimento(alimento):
    """
    Asigna categoría final 0-3 + riesgo de aditivos
    """
    
    # 1. Obtener Cluster (ya calculado en K-Means)
    cluster = alimento['cluster']  # 0, 1, 2 ó 3
    
    # 2. Determinar riesgo de aditivos (el MÁXIMO)
    aditivos = alimento['additives_tags'].split(',')
    
    riesgos = []
    for e_code in aditivos:
        ssi_level = consultar_ssi(e_code)  # SEGURO, PRECAUCIÓN, EVITABLE
        riesgos.append(ssi_level)
    
    # 3. Ganador: el más peligroso (EVITABLE > PRECAUCIÓN > SEGURO)
    if 'EVITABLE' in riesgos:
        riesgo_final = 'EVITABLE'
    elif 'PRECAUCIÓN' in riesgos:
        riesgo_final = 'PRECAUCIÓN'
    else:
        riesgo_final = 'SEGUROS'  # Incluye sin aditivos
    
    # 4. Categoría final
    categoria_final = f"{cluster}_{riesgo_final}"
    
    return categoria_final
```

**Ejemplo en la práctica:**

```
YOGUR DANONE NATURAL
├─ Nutriscore: A (1)
├─ NOVA: 2 (procesado)
├─ Aditivos: E406, E1442
│
├─ K-Means Cluster: 0 ("Falso Saludable")
│  └─ Razón: Nutriscore bueno BUT NOVA 2 + 2 aditivos
│
├─ SSI de aditivos:
│  ├─ E406 (carragenina): PRECAUCIÓN
│  └─ E1442 (almidón modificado): SEGURO
│
├─ Riesgo dominante: PRECAUCIÓN (porque hay 1+ PRECAUCIÓN)
│
└─ CATEGORÍA FINAL: 0_PRECAUCIÓN ⚠️
   └─ Interpretación: "Parece saludable pero tiene aditivos cuestionables"

═══════════════════════════════════════════════════════════════

REFRESCO COCA COLA ZERO
├─ Nutriscore: E (5)
├─ NOVA: 4 (ultraprocesado)
├─ Aditivos: E150d, E950, E951, E320, E321
│
├─ K-Means Cluster: 3 ("Ultraprocesado")
│  └─ Razón: Nutriscore malo + NOVA máxima + muchos aditivos
│
├─ SSI de aditivos:
│  ├─ E150d (caramelo): SEGURO
│  ├─ E950 (acesulfame potásico): PRECAUCIÓN
│  ├─ E951 (aspartamo): PRECAUCIÓN
│  ├─ E320 (BHA): EVITABLE ← ⚠️ AQUÍ
│  └─ E321 (BHT): EVITABLE ← ⚠️ Y AQUÍ
│
├─ Riesgo dominante: EVITABLE (porque hay 2+ EVITABLE)
│
└─ CATEGORÍA FINAL: 3_EVITABLE 🔴
   └─ Interpretación: "Evitar. Ultraprocesado con aditivos peligrosos"

═══════════════════════════════════════════════════════════════

MANZANA ROJA ECO
├─ Nutriscore: A (1)
├─ NOVA: 1 (natural)
├─ Aditivos: (ninguno)
│
├─ K-Means Cluster: 2 ("Verdaderamente Saludable")
│  └─ Razón: Nutriscore excelente + NOVA natural + sin aditivos
│
├─ SSI de aditivos: (vacío)
│
├─ Riesgo dominante: SEGUROS (sin aditivos)
│
└─ CATEGORÍA FINAL: 2_SEGUROS ✅
   └─ Interpretación: "Mejor opción"
```

### Matriz de 12 Categorías Finales

```
                SEGUROS      PRECAUCIÓN     EVITABLE
CLUSTER 0   →  0_SEGUROS    0_PRECAUCIÓN   0_EVITABLE
CLUSTER 1   →  1_SEGUROS    1_PRECAUCIÓN   1_EVITABLE
CLUSTER 2   →  2_SEGUROS    2_PRECAUCIÓN   2_EVITABLE
CLUSTER 3   →  3_SEGUROS    3_PRECAUCIÓN   3_EVITABLE
```

### Interpretación por Categoría

| Categoría | Cluster | Aditivos | Significado | Acción |
|-----------|---------|----------|-------------|--------|
| **0_SEGUROS** | Falso Saludable | Ninguno peligroso | Parece bien pero NO es | ⚠️ Revisar NOVA |
| **0_PRECAUCIÓN** | Falso Saludable | Cuestionables | Engañoso + dudas | ❌ Evitar |
| **0_EVITABLE** | Falso Saludable | Peligrosos | Marketing falso | 🔴 NUNCA |
| **1_SEGUROS** | Simple Malo | Ninguno peligroso | Malo pero honesto | ⚠️ Ocasional |
| **1_PRECAUCIÓN** | Simple Malo | Cuestionables | Malo + dudas | ❌ Evitar |
| **1_EVITABLE** | Simple Malo | Peligrosos | Muy malo | 🔴 NUNCA |
| **2_SEGUROS** | Verdad. Saludable | Ninguno peligroso | Excelente | ✅ MEJOR |
| **2_PRECAUCIÓN** | Verdad. Saludable | Cuestionables | Raro pero posible | ⚠️ Revisar |
| **2_EVITABLE** | Verdad. Saludable | Peligrosos | Muy raro | 🔴 NUNCA |
| **3_SEGUROS** | Ultraprocesado | Ninguno peligroso | Raro, muy bueno | ✅ BIEN |
| **3_PRECAUCIÓN** | Ultraprocesado | Cuestionables | Ultra + dudas | ❌ Evitar |
| **3_EVITABLE** | Ultraprocesado | Peligrosos | Peor que peor | 🔴 NUNCA |

---

## 📊 Output Esperado: nutriscore_2_0_final.csv

```csv
product_name,product_id,nutriscore_grade,nova_group,total_aditivos,cluster,aditivos_ssi,riesgo_dominante,categoria_final
Yogur Danone Natural,123456,A,2,2,0,PRECAUCIÓN,PRECAUCIÓN,0_PRECAUCIÓN
Manzana Roja,789012,A,1,0,2,ninguno,SEGUROS,2_SEGUROS
Coca Cola Zero,456789,E,4,5,3,EVITABLE,EVITABLE,3_EVITABLE
Refresco Fanta,111222,D,3,4,1,PRECAUCIÓN,PRECAUCIÓN,1_PRECAUCIÓN
Aceite Oliva Virgen,333444,A,1,0,2,ninguno,SEGUROS,2_SEGUROS
Galletas Digestive,555666,C,3,3,1,SEGURO,SEGUROS,1_SEGUROS
```

**Columnas clave:**
- `cluster` → 0, 1, 2, 3 (del K-Means)
- `riesgo_dominante` → SEGUROS, PRECAUCIÓN, EVITABLE (del SSI + lógica "ganador es el peor")
- `categoria_final` → {0-3}_{SEGUROS|PRECAUCIÓN|EVITABLE} (combinación)

---

![Nutriscore 2.0 Concept](results/figures/nutriscore2-0.png)

---

## 📁 Estructura del Proyecto

```
nutriscore-2.0/
│
├── README.md                          ← Este archivo
├── requirements.txt                   ← Dependencias Python
├── .env.example                       ← Variables de entorno (API keys)
├── pipeline.py                        ← Orquestador principal (ejecuta todo)
│
├── data/
│   ├── raw/
│   │   ├── food.parquet              ← Dataset principal (836k alimentos)
│   │   └── additives.json            ← Taxonomía de aditivos (651)
│   │
│   └── processed/
│       ├── alimentos_clustering.csv   ← Datos con clusters asignados
│       ├── aditivos_ssi.csv          ← Aditivos con SSI calculado
│       └── nutriscore_2_0_final.csv  ← Clasificación final
│
├── notebooks/
│   ├── 00_eda_exploratorio.ipynb     ← Análisis exploratorio previo (referencia)
│   ├── 01_ssi_aditivos.ipynb         ← Clasificación de aditivos por PubMed
│   ├── 02_kmeans_clustering.ipynb    ← K-Means + validación jerárquica
│   ├── 03_visualizacion_resultados.ipynb ← Gráficos finales
│   └── 04_nutriscore_2_0_final.ipynb ← Integración y exportación
│
├── src/
│   ├── __init__.py
│   ├── pubmed_scraper.py             ← Búsquedas en PubMed API
│   ├── ssi_calculator.py             ← Cálculo Scientific Safety Index
│   ├── clustering.py                 ← K-Means + métodos de validación
│   └── utils.py                      ← Funciones auxiliares
│
├── results/
│   ├── figures/
│   │   ├── eda/
│   │   │   ├── distribucion_nutriscore.png
│   │   │   ├── distribucion_nova.png
│   │   │   └── distribucion_aditivos.png
│   │   ├── clustering/
│   │   │   ├── metodo_codo_alimentos2.png
│   │   │   ├── silhouette_4_clusters2.png
│   │   │   └── dendrograma_ward_validacion.png
│   │   ├── resultados/
│   │   │   ├── matriz2.png
│   │   │   ├── dispersion.png
│   │   │   └── nutriscore2-0.png
│   │   └── comparativas/
│   │       ├── nutriscore_vs_nutriscore2.png
│   │       └── distribucion_clusters.png
│   │
│   └── reports/
│       ├── memoria_tecnica.pdf       ← Documento completo
│       └── ssi_aditivos_detallado.xlsx ← Tabla de aditivos con scores
│
├── app/
│   ├── streamlit_app.py              ← Aplicación user-facing
│   ├── requirements_app.txt           ← Dependencias específicas app
│   └── assets/
│       └── logo_nutriscore2.png
│
└── .gitignore                         ← Ignorar archivos grandes
```

---

## 🚀 Cómo Ejecutar el Proyecto

### Requisitos Previos

- **Python 3.9+**
- **Jupyter Notebook** o **JupyterLab**
- Conexión a internet (para PubMed API)

### Instalación

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/nutriscore-2.0.git
cd nutriscore-2.0

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de PubMed
```

### Variables de Entorno Necesarias

```bash
# .env
NCBI_EMAIL="tu_email@example.com"
NCBI_API_KEY="tu_api_key_pubmed"
NOMBRE_HERRAMIENTA="NutriscorePyProject"
```

**Obtener API key PubMed:**
1. Registrarse en [NCBI Account](https://www.ncbi.nlm.nih.gov/account/)
2. Generar API key en "Account Settings"
3. Pegar en `.env`

### Ejecución del Pipeline

```bash
# ✅ OPCIÓN 1: Ejecutar todo de una vez (RECOMENDADO)
python pipeline.py

# ✅ OPCIÓN 2: Ejecutar notebooks en orden (más control)
jupyter notebook notebooks/01_ssi_aditivos.ipynb
jupyter notebook notebooks/02_kmeans_clustering.ipynb
jupyter notebook notebooks/03_visualizacion_resultados.ipynb
jupyter notebook notebooks/04_nutriscore_2_0_final.ipynb

# ✅ OPCIÓN 3: Ejecutar Streamlit app (después de completar pipeline)
streamlit run app/streamlit_app.py
```

**¿Qué hace cada opción?**

| Opción | Tiempo | Control | Cuándo usar |
|--------|--------|---------|-------------|
| `python pipeline.py` | ~30-40 min | Automático | Primera vez, producción |
| Notebooks secuenciales | ~30-40 min | Total | Desarrollo, debugging |
| Streamlit app | N/A | UI interactiva | Explorar resultados |

**Recomendación:** Si es primera vez, usa `python pipeline.py`. Si necesitas debuggear, usa notebooks.

### Qué contiene `pipeline.py`

El archivo `pipeline.py` es el **orquestador maestro** que ejecuta todo en orden:

```python
# pipeline.py (pseudocódigo)

import logging
from src.pubmed_scraper import scrape_additives_pubmed
from src.ssi_calculator import calculate_ssi
from src.clustering import kmeans_clustering, hierarchical_validation
from src.categorization import categorizar_alimentos
from src.utils import load_data, save_results

# 1. Descargar datos si no existen
print("📥 Descargando food.parquet y additives.json...")
load_data()

# 2. Etapa 1: Clasificar aditivos por PubMed → SSI
print("🔬 Clasificando 651 aditivos (PubMed)... (~15 min)")
aditivos_ssi = scrape_additives_pubmed()  # Output: aditivos_ssi.csv
calculate_ssi(aditivos_ssi)

# 3. Etapa 2: Clustering de alimentos (K-Means)
print("🎯 K-Means clustering (836k alimentos)... (~5 min)")
clusters = kmeans_clustering(k=4)  # Output: alimentos_clustering.csv

# 4. Validación con Hierarchical Clustering
print("✅ Validando con Hierarchical Clustering...")
hierarchical_validation(clusters)

# 5. Etapa 3: Mapear SSI a alimentos → Categorizar
print("📊 Asignando categorías finales (Cluster + SSI)...")
for each_alimento in food_data:
    cluster = alimento['cluster']  # 0, 1, 2, 3
    aditivos = alimento['additives_tags'].split(',')
    
    # Lógica: aditivo más peligroso gana
    riesgos = [aditivos_ssi[e]['categoria'] for e in aditivos]
    if 'EVITABLE' in riesgos:
        riesgo_final = 'EVITABLE'
    elif 'PRECAUCIÓN' in riesgos:
        riesgo_final = 'PRECAUCIÓN'
    else:
        riesgo_final = 'SEGUROS'
    
    alimento['categoria_final'] = f"{cluster}_{riesgo_final}"

nutriscore_2_0 = categorizar_alimentos(clusters, aditivos_ssi)
# Output: nutriscore_2_0_final.csv (12 categorías)

# 6. Guardar resultados
print("💾 Guardando resultados...")
save_results(nutriscore_2_0)

print("✨ ¡DONE! Resultados en data/processed/ y results/figures/")
```

**Salidas esperadas:**
```
data/processed/
├── aditivos_ssi.csv              (651 rows × 4 cols)
│   └─ [E_code, nombre, ssi_score, ssi_categoria]
├── alimentos_clustering.csv       (836k rows con clusters 0-3)
│   └─ [product_id, cluster, ...]
└── nutriscore_2_0_final.csv       (836k rows con 12 categorías)
    └─ [product_id, cluster, riesgo_dominante, categoria_final]

results/figures/
├── clustering/
│   ├── metodo_codo_alimentos2.png
│   ├── silhouette_4_clusters2.png
│   └── dendrograma_ward_validacion.png
└── resultados/
    ├── matriz2.png
    ├── dispersion.png
    └── nutriscore2-0.png
```

### Descarga de Datos

Los datos se descargarán automáticamente si no existen:

```python
# Descarga automática en notebooks:
# - food.parquet: ~2.5 GB (⚠️ Tomar 30-60 minutos)
# - additives.json: ~5 MB (rápido)
```

**Descargar manualmente si prefieres:**

```bash
# Alimentos (836k productos)
wget -O data/raw/food.parquet \
  "https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet?download=true"

# Aditivos (651 aditivos)
wget -O data/raw/additives.json \
  "https://world.openfoodfacts.org/data/taxonomies/additives.json"
```

### Especificación Técnica de Datos

#### Pipeline Lógico (Importante entender)

```
ETAPA 1: Clasificar Aditivos (SSI)
├─ Input: 651 aditivos + PubMed
├─ Output: aditivos_ssi.csv (651 rows)
│   └─ Columns: [E_code, nombre, SSI_score, SSI_categoria]
│      └─ SSI_categoria: SEGURO (73%) | PRECAUCIÓN (13%) | EVITABLE (14%)
└─ Nota: SIN esto, no hay riesgo de aditivos

ETAPA 2: Cluster de Alimentos (K-Means)
├─ Input: 836k alimentos + 3 features (Nutriscore, NOVA, total_aditivos)
├─ Output: alimentos_clustering.csv (836k rows)
│   └─ Columns: [product_id, cluster (0-3), ...]
└─ Nota: Independiente de SSI (puro clustering)

ETAPA 3: Mapear Aditivos a Alimentos
├─ Input: 
│   ├─ alimentos_clustering.csv (cluster asignado)
│   ├─ aditivos_ssi.csv (SSI por E_code)
│   └─ additives_tags de cada alimento
├─ Output: nutriscore_2_0_final.csv (836k rows, 12 categorías)
│   └─ Columns: [cluster, riesgo_dominante, categoria_final]
└─ Algoritmo: Para cada alimento:
   1. Lee additives_tags → ["E100", "E101", "E102"]
   2. Consulta SSI de cada → [SEGURO, PRECAUCIÓN, SEGURO]
   3. Ganador = MAX(riesgos) → PRECAUCIÓN
   4. Categoría = f"{cluster}_{riesgo_final}" → "0_PRECAUCIÓN"
```

#### food.parquet (836,897 alimentos)

**Columnas requeridas por pipeline:**

```python
REQUERIDAS = {
    'product_name': str,           # Ej: "Yogur Natural Danone"
    'product_id': int,             # ID único
    'nutriscore_grade': str,       # 'A', 'B', 'C', 'D', 'E'
    'nova_group': int,             # 1, 2, 3, 4
    'additives_tags': str,         # "E100,E101,E102" (CSV separado)
}

NUTRIENTES_VALIDACION = {
    'energy-kcal_100g': float,
    'fat_100g': float,
    'carbohydrates_100g': float,
    'sugars_100g': float,
    'proteins_100g': float,
    'salt_100g': float,
}
```

**⚠️ Nota importante sobre nombres de columnas:**

El dataset de HuggingFace puede tener variaciones de nombres. Antes de ejecutar pipeline, inspecciona:

```python
import pandas as pd

df = pd.read_parquet('data/raw/food.parquet')
print(df.shape)                           # Ej: (836897, 220+)
print([c for c in df.columns if 'nutriscore' in c.lower()])  # Encontrar columna Nutriscore
print([c for c in df.columns if 'nova' in c.lower()])        # Encontrar columna NOVA
print([c for c in df.columns if 'additive' in c.lower()])    # Encontrar columna aditivos

# Ejemplos de nombres reales encontrados:
# - 'nutriscore_grade' o 'nutriscore_grade_en'
# - 'nova_group' o 'nova'
# - 'additives_tags' o 'additives' (puede ser lista)
```

**Limpieza de datos:**

```python
# Filtrar registros con datos completos
df_clean = df.dropna(subset=['nutriscore_grade', 'nova_group', 'additives_tags'])
print(f"Registros válidos: {len(df_clean)} / {len(df)}")

# Ver ejemplos
print(df_clean[['product_name', 'nutriscore_grade', 'nova_group', 'additives_tags']].head(3))
```

**Salida esperada:**

```
                              product_name nutriscore_grade nova_group          additives_tags
0  Yogur Natural Activia Danone                        B              2  E406,E1442
1  Zumo Naranja Natural Minute Maid                    B              3  E300,E330
2  Manzana Roja Bio Ecológica                         A              1  
```

#### aditivos_ssi.csv (651 aditivos, OUTPUT de etapa 1)

**Estructura después de procesar PubMed:**

```csv
E_code,nombre_quimico,ssi_score,ssi_categoria,papers_pubmed
E100,Curcumina,0.92,SEGURO,145
E101,Riboflavina,0.88,SEGURO,203
E102,Tartrazina,0.34,PRECAUCIÓN,89
E150d,Caramelo clase IV,0.79,SEGURO,56
E320,BHA,0.12,EVITABLE,234
E321,BHT,0.15,EVITABLE,198
```

**Cómo usar en categorización:**

```python
ssi_df = pd.read_csv('data/processed/aditivos_ssi.csv', index_col='E_code')

# Para un alimento con E100, E102:
aditivos = ['E100', 'E102']
riesgos = [ssi_df.loc[e, 'ssi_categoria'] for e in aditivos]
# → ['SEGURO', 'PRECAUCIÓN']

# Ganador (el peor)
if 'EVITABLE' in riesgos:
    riesgo_final = 'EVITABLE'
elif 'PRECAUCIÓN' in riesgos:
    riesgo_final = 'PRECAUCIÓN'
else:
    riesgo_final = 'SEGUROS'
# → 'PRECAUCIÓN'
```

#### additives.json (651 aditivos UE, INPUT)

**Estructura esperada:**

```json
{
  "E100": {
    "id": "E100",
    "name": "Curcumina",
    "vegan": true,
    "vegetarian": true
  },
  "E101": {
    "id": "E101",
    "name": "Riboflavina (B2)",
    "vegan": false,
    "vegetarian": false
  }
}
```

**Cómo verificar:**

```python
import json

with open('data/raw/additives.json', 'r') as f:
    aditivos = json.load(f)

print(f"Total aditivos cargados: {len(aditivos)}")
print(f"Primeras claves: {list(aditivos.keys())[:10]}")
print(f"Estructura E100: {aditivos['E100']}")
```

---

## 📚 Fuentes de Datos

### APIs y Datasets Utilizados

| Fuente | Descripción | URL | Documentación |
|--------|-------------|-----|----------------|
| **Open Food Facts** | Base de datos de productos alimenticios | `https://world.openfoodfacts.org` | [Docs](https://world.openfoodfacts.org/data) |
| **Open Food Facts API - Aditivos** | Taxonomía de 651 aditivos permitidos en UE | `https://world.openfoodfacts.org/data/taxonomies/additives.json` | [JSON](https://world.openfoodfacts.org/data) |
| **Open Food Facts - Dataset Parquet** | 836k+ productos con metadatos nutricionales | `https://huggingface.co/datasets/openfoodfacts/product-database/resolve/main/food.parquet?download=true` | [HuggingFace](https://huggingface.co/datasets/openfoodfacts/product-database) |
| **NCBI PubMed API** | Motor de búsqueda de papers científicos | `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` | [API Docs](https://www.ncbi.nlm.nih.gov/books/NBK25499/) |
| **EFSA (European Food Safety Authority)** | Regulaciones de aditivos alimentarios | `https://www.efsa.europa.eu` | [Base de datos](https://www.efsa.europa.eu/en/food-additives-evaluations) |

### Especificaciones de Descarga

**food.parquet (836,897 alimentos)**
```
Tamaño: ~2.5 GB
Tiempo descarga: 30-60 minutos (conexión 10Mbps)
Columnas principales: product_name, nutriscore_grade, nova_group, additives, packaging, etc.
Fuente: Open Food Facts + HuggingFace Hub
```

**additives.json (651 aditivos)**
```
Tamaño: ~5 MB
Columnas principales: E_number, name, vegan, vegetarian, risk_level, etc.
Fuente: Open Food Facts API
```

---

## 📊 Dependencias

**Python:** 3.9 o superior

**Librerías principales:**

```
# requirements.txt
pandas==2.0.3
numpy==1.24.3
scikit-learn==1.3.0
matplotlib==3.7.2
seaborn==0.12.2
requests==2.31.0
scipy==1.11.1
streamlit==1.26.0
pyarrow==12.0.1
python-dotenv==1.0.0       # Para leer .env
jupyter==1.0.0             # Para ejecutar notebooks
plotly==5.16.1             # Para visualizaciones 3D
```

**Instalación rápida:**

```bash
pip install -r requirements.txt
```

**Notas sobre compatibilidad:**

- **Mac M1/M2:** Puede necesitar `conda` en lugar de `pip` para numpy/scipy
  ```bash
  conda install -c conda-forge scikit-learn scipy
  ```
  
- **Windows + WSL2:** Asegurar que `python-dotenv` esté instalado
  ```bash
  pip install python-dotenv --upgrade
  ```

---

## 🔍 Validación de Resultados

### Convergencia de Métodos

**Punto clave: K=4 se valida con dos enfoques independientes**

```
K-Means (determinístico, optimiza intra-cluster)  → 4 clusters
                        +
Hierarchical Clustering WARD (aglomerativo)       → 4 ramas naturales
                        =
        ✅ CONFIANZA MÁXIMA EN K=4
```

**Métricas:**
- **Silhouette Score (K=4):** 0.41 → Moderado a bueno
- **Elbow Point:** Codo claro y pronunciado en K=4
- **Interpretabilidad:** Cada cluster tiene perfil diferenciado y significativo

### Calidad de Datos

```
✅ Nutriscore: 100% valores entre 1-5
✅ NOVA: 100% valores entre 1-4
✅ Aditivos: Códigos E estandarizados
✅ Sin valores faltantes en features críticas
✅ One-hot encoding validado (651 binarios)
```

---

## 💡 Impacto e Implicaciones

### Para Consumidores
✅ Información COMPLETA en 1 clasificación  
✅ Decisiones informadas basadas en ciencia (PubMed + EFSA)  
✅ Detecta productos "engañosos" (Cluster 0)  
✅ Acceso fácil via app Streamlit  

### Para Industria Alimentaria
✅ Incentivo económico para reducir aditivos riesgosos  
✅ Presión competitiva positiva (diferencial "Cluster 2")  
✅ Marketing científicamente válido  

### Para Reguladores
✅ Herramienta de monitoreo basada en análisis de PubMed  
✅ Datos para revisar aditivos automáticamente  
✅ Apoyo a políticas de salud pública  

---

## ⚠️ Limitaciones Conocidas

| Limitación | Descripción | Solución Futura |
|-----------|-------------|------------------|
| **Sinergia de aditivos** | SSI analiza aditivos individualmente, no interacciones | Estudiar combinaciones peligrosas en PubMed |
| **Completitud de datos OFF** | No todos los alimentos listados tienen aditivos detallados | Usar solo alimentos con datos completos |
| **Cambio regulatorio** | Si EFSA retira/aprueba aditivo, SSI cambia | Pipeline automático con actualización diaria |
| **Sesgo geográfico** | Datos principalmente de Europa occidental | Expandir a más regiones |
| **Ingredientes base** | No analiza azúcares/grasas saturadas específicas | Integrar nutritional labels detallados |

---

## 🚀 Mejoras Futuras

```
Corto plazo (1-3 meses):
✅ Análisis de interacciones peligrosas entre aditivos
✅ ML predictivo: qué cambios de formulación moverían clusters
✅ Integración con apps de supermercado (Carrefour, Mercadona)
✅ Traducción a 5+ idiomas

Mediano plazo (3-6 meses):
✅ Propuesta formal a EFSA como estándar europeo
✅ Integración con sistemas de recomendación nutricional
✅ Análisis de costos: cuánto cuesta formular en Cluster 2

Largo plazo (6-12 meses):
✅ Modelo predictivo de cambios EFSA (qué aditivos serán retirados)
✅ APIs públicas para desarrolladores
✅ Mobile app nativa (iOS + Android)
```

---

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Para cambios importantes:

1. Fork el repositorio
2. Crea rama (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push a rama (`git push origin feature/AmazingFeature`)
5. Abre Pull Request

---

## 📄 Licencia

Este proyecto está bajo licencia **MIT**. Ver archivo `LICENSE` para detalles.

---

## 👤 Autor

**Mikel Añibarro Ortega**  
Data Science | Bootcamp The Bridge, Campus Bilbao (2026)

### 📌 Conecta conmigo

> **⚠️ TODO:** Reemplazar placeholders con tus datos reales

- 🔗 LinkedIn: [**[REEMPLAZA CON TU PERFIL]**](https://linkedin.com/in)
- 🔬 ORCID: [**[REEMPLAZA CON TU ORCID]**](https://orcid.org)
- 📧 Email: mikel.anibarro@example.com
- 🐙 GitHub: [**[REEMPLAZA CON TU USUARIO]**](https://github.com)

**Instrucciones para actualizar:**

1. Abre este README en tu editor
2. Busca `[REEMPLAZA CON TU PERFIL]` en LinkedIn
3. Sustituye por: `https://linkedin.com/in/tu-nombre-usuario`
4. Busca `[REEMPLAZA CON TU ORCID]`
5. Obtén tu ORCID en https://orcid.org y sustituye
6. Actualiza Email y GitHub username

---

## 📚 Referencias

### Documentos Técnicos
- **Memoria Técnica Completa:** `results/reports/memoria_tecnica.pdf`
- **Tabla Aditivos SSI:** `results/reports/ssi_aditivos_detallado.xlsx`

### Artículos y Fuentes Científicas
- EFSA (2023): *Evaluación de aditivos alimentarios permitidos en UE*
- Open Food Facts (2024): *Metodología Nutriscore*
- PubMed Central: 10,400+ papers consultados sobre seguridad de aditivos

### Repositorios Relacionados
- [Open Food Facts GitHub](https://github.com/openfoodfacts)
- [NOVA Food Classification](https://www.fao.org/documents/card/en/c/CA5644EN)

---

**Última actualización:** Mayo 2026  
**Estado del proyecto:** ✅ Completo | 🚀 Listo para producción  
**Reproducibilidad:** ✅ 100% | Todas las etapas documentadas

---

## 📞 Soporte

¿Preguntas o problemas?

- 📖 Revisa `CONTRIBUTING.md`
- 🐛 Abre un issue en GitHub
- 💬 Contáctame en LinkedIn

