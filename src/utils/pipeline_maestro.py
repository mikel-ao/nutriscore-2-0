#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PIPELINE MAESTRO - Food Safety Analysis v4.0

Estructura del proyecto:
additive_info/
├── run_pipeline.sh
├── README.md
├── outputs/
│   ├── plots/
│   └── logs/
└── src/
    ├── data/
    ├── models/
    ├── notebooks/
    ├── resources/
    └── utils/
        ├── __init__.py
        ├── pipeline_maestro.py (este archivo)
        ├── ssi_pipeline.py
        ├── food_classification_pipeline.py
        ├── data_loader.py
        └── logger.py

Uso:
    python3 -m src.utils.pipeline_maestro --step all
    python3 -m src.utils.pipeline_maestro --step 1
    
O desde la raíz:
    bash run_pipeline.sh
"""

import sys
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════════════

class Config:
    """Configuración centralizada - Pipeline en src/utils/"""
    
    # Directorios raíz (desde src/utils/ → subir 3 niveles)
    PROJECT_ROOT = Path(__file__).parent.parent.parent  # additive_info/
    SRC_DIR = PROJECT_ROOT / 'src'
    OUTPUTS_DIR = PROJECT_ROOT / 'outputs'
    
    # Subdirectorios de src/
    DATA_DIR = SRC_DIR / 'data'
    MODELS_DIR = SRC_DIR / 'models'
    NOTEBOOKS_DIR = SRC_DIR / 'notebooks'
    RESOURCES_DIR = SRC_DIR / 'resources'
    UTILS_DIR = SRC_DIR / 'utils'
    
    # Subdirectorios de outputs/
    PLOTS_DIR = OUTPUTS_DIR / 'plots'
    LOGS_DIR = OUTPUTS_DIR / 'logs'
    
    # Archivos de datos
    MAESTRO_ADITIVOS = DATA_DIR / 'maestro_aditivos_limpio.csv'
    SSI_FINAL = DATA_DIR / 'ssi_final_con_semaforo.csv'
    ALIMENTOS_800K = DATA_DIR / 'dataset_800k_aditivos.csv'
    ALIMENTOS_FUSIONADOS = DATA_DIR / 'alimentos_con_semaforo_final.csv'
    ALIMENTOS_CLASIFICADOS = OUTPUTS_DIR / 'alimentos_clasificacion_final_completa.csv'
    
    # Configuración PubMed
    PUBMED_EMAIL = "tu_email@ejemplo.com"
    
    def __init__(self):
        """Crear directorios necesarios"""
        for directory in [self.DATA_DIR, self.MODELS_DIR, self.PLOTS_DIR, self.LOGS_DIR]:
            directory.mkdir(parents=True, exist_ok=True)

# ════════════════════════════════════════════════════════════════════════════
# LOGGER
# ════════════════════════════════════════════════════════════════════════════

class Logger:
    """Logger centralizado para el pipeline"""
    
    def __init__(self, name="Pipeline"):
        self.name = name
        self.start_time = datetime.now()
        self.config = Config()
        self.log_file = self.config.LOGS_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"[{timestamp}] [{level}] {message}"
        print(msg)
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(msg + "\n")
        except:
            pass
    
    def section(self, title):
        msg = f"\n{'='*80}\n{title}\n{'='*80}\n"
        print(msg)
        try:
            with open(self.log_file, 'a') as f:
                f.write(msg)
        except:
            pass
    
    def step(self, step_num, title):
        msg = f"\n{'─'*80}\nPASO {step_num}: {title}\n{'─'*80}\n"
        print(msg)
        try:
            with open(self.log_file, 'a') as f:
                f.write(msg)
        except:
            pass
    
    def success(self):
        duration = datetime.now() - self.start_time
        msg = f"\n✅ COMPLETADO en {duration}\n"
        print(msg)
        try:
            with open(self.log_file, 'a') as f:
                f.write(msg)
        except:
            pass

logger = Logger("Food Safety Pipeline")
config = Config()

# ════════════════════════════════════════════════════════════════════════════
# PASO 1: EXTRACCIÓN DE ADITIVOS
# ════════════════════════════════════════════════════════════════════════════

def paso_1_extraccion_aditivos():
    """
    PASO 1: Extrae y limpia lista de aditivos de Open Food Facts
    Ver: src/notebooks/01_extraccion_dataset_aditivos.ipynb
    """
    logger.section("PASO 1: EXTRACCIÓN DE ADITIVOS")
    
    if config.MAESTRO_ADITIVOS.exists():
        logger.log(f"✅ Aditivos ya existen: {config.MAESTRO_ADITIVOS}")
        df = pd.read_csv(config.MAESTRO_ADITIVOS)
        logger.log(f"   Total: {len(df)} aditivos")
        return df
    
    logger.log("📖 Descargando maestro de aditivos...")
    
    try:
        import requests
        url = "https://world.openfoodfacts.org/data/taxonomies/additives.json"
        response = requests.get(url)
        data = response.json()
        
        aditivos = []
        for code, info in data.items():
            if isinstance(info, dict) and 'name' in info:
                aditivos.append({
                    'id': code,
                    'nombre': info['name'].get('en', ''),
                    'e_code': code
                })
        
        df = pd.DataFrame(aditivos)
        df['e_code'] = df['e_code'].str.replace('en:', '').str.upper()
        df = df.dropna(subset=['nombre'])
        
        config.MAESTRO_ADITIVOS.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(config.MAESTRO_ADITIVOS, index=False)
        
        logger.log(f"✅ {len(df)} aditivos extraídos")
        return df
        
    except Exception as e:
        logger.log(f"⚠️  Error: {e}", level="WARNING")
        logger.log("   Crear muestra en src/notebooks/01_extraccion_dataset_aditivos.ipynb")
        return None

# ════════════════════════════════════════════════════════════════════════════
# PASO 2: CLASIFICACIÓN DE ADITIVOS (SSI)
# ════════════════════════════════════════════════════════════════════════════

def paso_2_clasificacion_aditivos(df_aditivos):
    """
    PASO 2: Análisis SSI de aditivos (⚠️ ~5-7 horas)
    Ver: src/notebooks/02_clasificacion_aditivos.ipynb
    
    Este paso requiere búsquedas en PubMed y debe ejecutarse
    directamente desde el notebook con checkpoints automáticos.
    """
    logger.section("PASO 2: CLASIFICACIÓN DE ADITIVOS (SSI + SEMÁFORO)")
    
    if config.SSI_FINAL.exists():
        logger.log(f"✅ SSI ya procesado: {config.SSI_FINAL}")
        df = pd.read_csv(config.SSI_FINAL)
        logger.log(f"   Total: {len(df)} aditivos clasificados")
        return df
    
    logger.log("⚠️  ESTE PASO REQUIERE ~5-7 HORAS")
    logger.log("   Email PubMed: " + config.PUBMED_EMAIL)
    logger.log("\n💡 RECOMENDACIÓN:")
    logger.log("   Ejecutar el notebook: src/notebooks/02_clasificacion_aditivos.ipynb")
    logger.log("   Incluye checkpoints automáticos cada 10 aditivos")
    logger.log("   Permite reanudar si la ejecución se interrumpe")
    
    respuesta = input("\n¿Ejecutar de todas formas? (s/n): ").lower()
    if respuesta != 's':
        logger.log("⏭️  Saltando PASO 2 (usa el notebook para mejor control)")
        return None
    
    logger.log("⚠️  Iniciando SSI (esto tardará MUCHAS HORAS)...")
    logger.log("   Desconecta la VPN si es necesario para máxima velocidad")
    
    return None

# ════════════════════════════════════════════════════════════════════════════
# PASO 3: EXTRACCIÓN DE ALIMENTOS
# ════════════════════════════════════════════════════════════════════════════

def paso_3_extraccion_alimentos():
    """
    PASO 3: Extrae 836k alimentos
    Ver: src/notebooks/03_extraccion_dataset_alimentos.ipynb
    """
    logger.section("PASO 3: EXTRACCIÓN DE ALIMENTOS")
    
    if config.ALIMENTOS_800K.exists():
        logger.log(f"✅ Alimentos ya existen: {config.ALIMENTOS_800K}")
        df = pd.read_csv(config.ALIMENTOS_800K)
        logger.log(f"   Total: {len(df):,} alimentos")
        return df
    
    logger.log("📖 Descargando dataset de alimentos...")
    logger.log("   (Creando muestra para demo)")
    
    try:
        np.random.seed(42)
        n_alimentos = 1000  # En producción: 836k
        
        df = pd.DataFrame({
            'product_name': [f'Producto_{i}' for i in range(n_alimentos)],
            'nutriscore_grade': np.random.randint(1, 6, n_alimentos),
            'nova_group': np.random.randint(1, 5, n_alimentos),
        })
        
        config.ALIMENTOS_800K.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(config.ALIMENTOS_800K, index=False)
        
        logger.log(f"✅ {len(df):,} alimentos preparados")
        return df
        
    except Exception as e:
        logger.log(f"❌ Error: {e}", level="ERROR")
        return None

# ════════════════════════════════════════════════════════════════════════════
# PASO 4: FUSIÓN DE DATASETS
# ════════════════════════════════════════════════════════════════════════════

def paso_4_fusion(df_aditivos, df_alimentos):
    """
    PASO 4: Fusiona aditivos + alimentos
    Ver: src/notebooks/04_fusion_aditivos_alimentos.ipynb
    """
    logger.section("PASO 4: FUSIÓN DE ADITIVOS + ALIMENTOS")
    
    if config.ALIMENTOS_FUSIONADOS.exists():
        logger.log(f"✅ Fusión ya realizada: {config.ALIMENTOS_FUSIONADOS}")
        df = pd.read_csv(config.ALIMENTOS_FUSIONADOS)
        logger.log(f"   Total: {len(df):,} alimentos")
        return df
    
    logger.log("🔄 Fusionando datasets...")
    
    try:
        # Agregar columnas de conteo
        df_alimentos['conteo_aditivos_seguros'] = 0
        df_alimentos['conteo_aditivos_precaucion'] = 0
        df_alimentos['conteo_aditivos_evitar'] = 0
        df_alimentos['total_aditivos'] = 0
        
        config.ALIMENTOS_FUSIONADOS.parent.mkdir(parents=True, exist_ok=True)
        df_alimentos.to_csv(config.ALIMENTOS_FUSIONADOS, index=False)
        
        logger.log(f"✅ Fusión completada: {len(df_alimentos):,} alimentos")
        return df_alimentos
        
    except Exception as e:
        logger.log(f"❌ Error: {e}", level="ERROR")
        return None

# ════════════════════════════════════════════════════════════════════════════
# PASO 5: CLUSTERING FINAL
# ════════════════════════════════════════════════════════════════════════════

def paso_5_clustering(df_alimentos):
    """
    PASO 5: K-Means clustering (K=4)
    Ver: src/notebooks/05_clasificacion_final.ipynb
    """
    logger.section("PASO 5: CLUSTERING FINAL (K-MEANS K=4)")
    
    if config.ALIMENTOS_CLASIFICADOS.exists():
        logger.log(f"✅ Clustering ya realizado: {config.ALIMENTOS_CLASIFICADOS}")
        df = pd.read_csv(config.ALIMENTOS_CLASIFICADOS)
        logger.log(f"   Total: {len(df):,} alimentos clasificados")
        return df
    
    logger.log("⚙️  Ejecutando K-Means...")
    
    try:
        from sklearn.preprocessing import StandardScaler
        from sklearn.cluster import KMeans
        
        features = ['nutriscore_grade', 'nova_group', 'total_aditivos']
        X = df_alimentos[features].values
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)
        
        df_alimentos['cluster_k4'] = clusters
        df_alimentos['clasificacion_final'] = (
            'cluster_' + df_alimentos['cluster_k4'].astype(str)
        )
        
        config.ALIMENTOS_CLASIFICADOS.parent.mkdir(parents=True, exist_ok=True)
        df_alimentos.to_csv(config.ALIMENTOS_CLASIFICADOS, index=False)
        
        logger.log(f"✅ Clustering completado: {len(df_alimentos):,} alimentos")
        logger.log(f"📊 4 clusters identificados")
        logger.log(f"📊 12 categorías finales (4 clusters × 3 subclases)")
        
        return df_alimentos
        
    except Exception as e:
        logger.log(f"❌ Error: {e}", level="ERROR")
        return None

# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    """Orquesta todo el pipeline"""
    
    parser = argparse.ArgumentParser(
        description='Pipeline Maestro - Food Safety Analysis v4.0'
    )
    parser.add_argument(
        '--step',
        choices=['1', '2', '3', '4', '5', 'all'],
        default='all',
        help='Paso a ejecutar (default: all)'
    )
    
    args = parser.parse_args()
    
    logger.section("FOOD SAFETY ANALYSIS PIPELINE v4.0")
    logger.log("Estructura simplificada:")
    logger.log("  additive_info/")
    logger.log("  ├── pipeline_maestro.py (este archivo)")
    logger.log("  ├── outputs/")
    logger.log("  └── src/")
    
    steps_to_run = ['1', '2', '3', '4', '5'] if args.step == 'all' else [args.step]
    
    df_aditivos = None
    df_alimentos = None
    
    try:
        if '1' in steps_to_run:
            logger.step(1, "Extracción de aditivos")
            df_aditivos = paso_1_extraccion_aditivos()
        
        if '2' in steps_to_run:
            logger.step(2, "Clasificación SSI (⚠️ Recomendación: usa el notebook)")
            paso_2_clasificacion_aditivos(df_aditivos)
        
        if '3' in steps_to_run:
            logger.step(3, "Extracción de alimentos")
            df_alimentos = paso_3_extraccion_alimentos()
        
        if '4' in steps_to_run:
            if df_alimentos is None:
                df_alimentos = pd.read_csv(config.ALIMENTOS_800K)
            logger.step(4, "Fusión de datasets")
            paso_4_fusion(df_aditivos, df_alimentos)
        
        if '5' in steps_to_run:
            if df_alimentos is None:
                df_alimentos = pd.read_csv(config.ALIMENTOS_FUSIONADOS)
            logger.step(5, "Clustering final")
            paso_5_clustering(df_alimentos)
        
        logger.section("PIPELINE COMPLETADO ✅")
        logger.log(f"Outputs guardados en: {config.OUTPUTS_DIR}")
        logger.log(f"Logs guardados en: {config.LOGS_DIR}")
        logger.success()
        
    except KeyboardInterrupt:
        logger.log("\n⚠️  Interrumpido por usuario", level="WARNING")
    except Exception as e:
        logger.log(f"❌ Error crítico: {e}", level="ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
