#!/usr/bin/env python3
# verificar_barcode_entrenamiento.py
"""
Script para verificar si un código de barras está en el dataset de entrenamiento
"""

import pandas as pd
import sys
from pathlib import Path

def main():
    print("="*60)
    print("VERIFICADOR DE BARCODE EN DATASET DE ENTRENAMIENTO")
    print("="*60)
    
    # Pedir input al usuario
    barcode = input("\n📱 Introduce el código de barras: ").strip()
    
    if not barcode:
        print("❌ Error: Debes introducir un código de barras")
        sys.exit(1)
    
    # Buscar el CSV en diferentes rutas
    rutas_posibles = [
        Path("../data/dataset_800k_aditivos.csv"),
    ]
    
    csv_path = None
    for ruta in rutas_posibles:
        if ruta.exists():
            csv_path = ruta
            break
    
    if csv_path is None:
        print("❌ Error: No se encontró dataset_800k_aditivos.csv")
        print("   Verifica que esté en: ./data/dataset_800k_aditivos.csv")
        sys.exit(1)
    
    print(f"\n📥 Cargando dataset desde: {csv_path}")
    try:
        df_raw = pd.read_csv(csv_path, usecols=['code'])
        print(f"✅ Dataset cargado: {len(df_raw)} productos")
    except Exception as e:
        print(f"❌ Error cargando dataset: {e}")
        sys.exit(1)
    
    # Verificar barcode
    print(f"\n🔍 Verificando barcode {barcode}...")
    
    if str(barcode).strip() in df_raw['code'].astype(str).str.strip().values:
        print(f"\n❌ Barcode {barcode} ESTÁ en el dataset de entrenamiento")
        print("   ⚠️ Este NO es una predicción real, estaba en los datos de entrenamiento")
    else:
        print(f"\n✅ Barcode {barcode} NO está en el dataset de entrenamiento")
        print("   ✓ Este SÍ es una predicción real (producto nuevo)")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()
