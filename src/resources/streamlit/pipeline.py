# pipeline.py
import requests
import pandas as pd
import joblib
import numpy as np
import re
from pathlib import Path

# ==============================================================================
# 1. CARGA DE RECURSOS ESTÁTICOS AL ARRANCAR EL MÓDULO
# ==============================================================================

# Variables globales
df_ssi_aditivos = None
mapping_traffic_light = None
scaler_alimentos = None
kmeans_alimentos = None

def cargar_recursos():
    """Carga los recursos al inicio. Se llama desde app.py con st.cache_resource"""
    global df_ssi_aditivos, mapping_traffic_light, scaler_alimentos, kmeans_alimentos
    
    try:
        # Intentar rutas relativas desde el script de streamlit
        ruta_csv = Path('./data/ssi_final_con_semaforo.csv')
        ruta_scaler = Path('./models/scaler_alimentos.pkl')
        ruta_kmeans = Path('./models/kmeans_alimentos.pkl')
        
        # Si no existen, intentar rutas alternativas
        if not ruta_csv.exists():
            ruta_csv = Path('../../../data/ssi_final_con_semaforo.csv')
        if not ruta_scaler.exists():
            ruta_scaler = Path('../../../models/scaler_alimentos.pkl')
        if not ruta_kmeans.exists():
            ruta_kmeans = Path('../../../models/kmeans_alimentos.pkl')
        
        # Cargar CSV
        print(f"📂 Buscando CSV en: {ruta_csv.resolve()}")
        df_ssi_aditivos = pd.read_csv(ruta_csv)
        print(f"✅ CSV cargado: {len(df_ssi_aditivos)} aditivos")
        
        # Mapeo: id_aditivo → traffic_light
        # Importante: Mantener el formato exacto del CSV (en:e150d)
        mapping_traffic_light = dict(zip(
            df_ssi_aditivos['id'].astype(str).str.strip().str.lower(),
            df_ssi_aditivos['traffic_light'].astype(str).str.strip().str.upper()
        ))
        print(f"✅ Mapping creado: {len(mapping_traffic_light)} aditivos mapeados")
        print(f"   Ejemplo de claves en mapping: {list(mapping_traffic_light.keys())[:5]}")
        
        # Cargar modelos
        print(f"📂 Buscando scaler en: {ruta_scaler.resolve()}")
        scaler_alimentos = joblib.load(ruta_scaler)
        print(f"✅ Scaler cargado (espera {scaler_alimentos.n_features_in_} features)")
        
        print(f"📂 Buscando kmeans en: {ruta_kmeans.resolve()}")
        kmeans_alimentos = joblib.load(ruta_kmeans)
        print(f"✅ K-Means cargado ({kmeans_alimentos.n_clusters} clusters)")
        
        print("🔬 [INFO] Todos los recursos cargados con éxito.")
        
        # Retornar diccionario con referencias
        return {
            'df_ssi': df_ssi_aditivos,
            'mapping': mapping_traffic_light,
            'scaler': scaler_alimentos,
            'kmeans': kmeans_alimentos
        }
        
    except FileNotFoundError as e:
        print(f"❌ [ERROR CRÍTICO] Archivo no encontrado: {e}")
        print("📋 Verifica que existan:")
        print("   - ./data/ssi_final_con_semaforo.csv")
        print("   - ./models/scaler_alimentos.pkl")
        print("   - ./models/kmeans_alimentos.pkl")
        import traceback
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"❌ [ERROR CRÍTICO] Error al cargar recursos: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==============================================================================
# 2. FUNCIONES DE PROCESAMIENTO
# ==============================================================================

def obtener_datos_openfoodfacts(barcode):
    """
    Consulta Open Food Facts API v2 con extractor regex de rescate.
    """
    barcode_str = str(barcode).strip()
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode_str}.json"
    
    headers = {
        'User-Agent': 'NutriScore2.0/1.0 (mklanibarro@gmail.com)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"❌ Status code {response.status_code} para barcode {barcode_str}")
            return None
            
        data = response.json()
        
        if data.get('status') == 1 or "found" in data.get('status_verbose', '').lower():
            product = data['product']
            
            # Extraer aditivos de canales oficiales
            aditivos_oficiales = product.get('additives_tags', [])
            if not aditivos_oficiales:
                aditivos_oficiales = product.get('additives_original_tags', [])
            
            aditivos_finales = [str(tag).lower() for tag in aditivos_oficiales]
            
            # RESCATE REGEX: Buscar E### en texto de ingredientes
            texto_ingredientes = product.get('ingredients_text_es', product.get('ingredients_text', ''))
            
            if texto_ingredientes:
                codigos_encontrados = re.findall(r'\b[Ee]-?\d{3,4}\b', texto_ingredientes)
                for codigo in codigos_encontrados:
                    codigo_limpio = f"en:{codigo.lower().replace('-', '')}"
                    if codigo_limpio not in aditivos_finales:
                        aditivos_finales.append(codigo_limpio)
                        print(f"🎯 [RESCATE REGEX] Aditivo extraído: {codigo_limpio}")
            
            nutriments = product.get('nutriments', {})
            
            return {
                'nombre': product.get('product_name_es', product.get('product_name', 'Nombre no disponible')),
                'marca': product.get('brands', 'Marca no disponible'),
                'imagen_url': product.get('image_url', product.get('image_front_url', None)),
                'nutriscore': product.get('nutriscore_grade', 'unknown').upper(),
                'nova': int(product.get('nova_group', 0)) if product.get('nova_group') is not None else 0,
                'aditivos_lista': aditivos_finales,
                'ingredients_text_raw': product.get('ingredients_text_es', product.get('ingredients_text', '')),
                'energia': nutriments.get('energy-kcal_100g', nutriments.get('energy-kcal', 0)),
                'grasas': nutriments.get('fat_100g', nutriments.get('fat', 0)),
                'azucares': nutriments.get('sugars_100g', nutriments.get('sugars', 0)),
                'proteinas': nutriments.get('proteins_100g', nutriments.get('proteins', 0)),
                'sal': nutriments.get('salt_100g', nutriments.get('salt', 0))
            }
        else:
            print(f"⚠️ Producto no encontrado: {data.get('status_verbose')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return None


def obtener_traffic_light_aditivos(aditivos_lista):
    """
    Mapea cada aditivo a su traffic_light del CSV SSI.
    Retorna lista con detalles: (e_code, nombre, traffic_light)
    """
    aditivos_detallados = []
    traffic_lights = []
    
    for aditivo in aditivos_lista:
        # Normalizar a minúsculas pero MANTENER el formato 'en:eXXX'
        aditivo_normalizado = str(aditivo).lower().strip()
        
        # Buscar en mapping
        tl = None
        e_code = None
        nombre = None
        
        if aditivo_normalizado in mapping_traffic_light:
            tl = mapping_traffic_light[aditivo_normalizado]
            # Buscar e_code y nombre en el CSV
            row = df_ssi_aditivos[df_ssi_aditivos['id'].astype(str).str.lower() == aditivo_normalizado]
            if not row.empty:
                e_code = row.iloc[0]['e_code']
                nombre = row.iloc[0]['nombre']
            print(f"✅ Aditivo '{aditivo}' → '{tl}' ({e_code} {nombre})")
        else:
            # Intentar sin 'en:' si no funciona
            aditivo_sin_en = aditivo_normalizado.replace('en:', '')
            aditivo_con_en = f"en:{aditivo_sin_en}"
            
            if aditivo_con_en in mapping_traffic_light:
                tl = mapping_traffic_light[aditivo_con_en]
                row = df_ssi_aditivos[df_ssi_aditivos['id'].astype(str).str.lower() == aditivo_con_en]
                if not row.empty:
                    e_code = row.iloc[0]['e_code']
                    nombre = row.iloc[0]['nombre']
                print(f"✅ Aditivo '{aditivo}' → '{tl}' ({e_code} {nombre}) (con en:)")
            elif aditivo_sin_en in mapping_traffic_light:
                tl = mapping_traffic_light[aditivo_sin_en]
                row = df_ssi_aditivos[df_ssi_aditivos['id'].astype(str).str.lower() == aditivo_sin_en]
                if not row.empty:
                    e_code = row.iloc[0]['e_code']
                    nombre = row.iloc[0]['nombre']
                print(f"✅ Aditivo '{aditivo}' → '{tl}' ({e_code} {nombre}) (sin en:)")
            else:
                # Default a SEGURO si no está en CSV
                tl = "SEGURO"
                e_code = aditivo_normalizado.replace('en:', '').upper()
                nombre = "Desconocido"
                print(f"⚠️ Aditivo '{aditivo}' no encontrado en CSV → Default SEGURO")
        
        traffic_lights.append(tl)
        aditivos_detallados.append({
            'e_code': e_code,
            'nombre': nombre,
            'traffic_light': tl
        })
    
    # Aplicar lógica de dominancia (el más peligroso prevalece)
    if "EVITABLE" in traffic_lights or "EVITAR" in traffic_lights:
        dominante = "EVITABLE"
    elif "PRECAUCION" in traffic_lights or "PRECAUCIÓN" in traffic_lights:
        dominante = "PRECAUCIÓN"
    else:
        dominante = "SEGURO"
    
    return aditivos_detallados, traffic_lights, dominante


def estimar_grupo_nova(aditivos_lista):
    """
    Si NOVA es 0 (nulo), estimarlo por cantidad de aditivos.
    """
    num_aditivos = len(aditivos_lista)
    
    if num_aditivos == 0:
        return 1  # Natural
    elif num_aditivos <= 2:
        return 2  # Procesado simple
    elif num_aditivos <= 5:
        return 3  # Más procesado
    else:
        return 4  # Ultraprocesado


def estimar_nutriscore_por_nutrientes(energia, grasas, azucares, sal, proteinas):
    """
    Estima Nutriscore si no está disponible.
    """
    puntos_negativos = 0
    
    # Energía
    if energia > 335: puntos_negativos += 2
    if energia > 670: puntos_negativos += 4
    
    # Grasas saturadas
    if grasas > 1: puntos_negativos += 1
    if grasas > 2: puntos_negativos += 3
    if grasas > 5.5: puntos_negativos += 6
    
    # Azúcares
    if azucares > 4.5: puntos_negativos += 1
    if azucares > 9: puntos_negativos += 3
    if azucares > 18: puntos_negativos += 4
    if azucares > 36: puntos_negativos += 8
    
    # Sal
    if sal > 0.5: puntos_negativos += 2
    if sal > 1.1: puntos_negativos += 5
    if sal > 1.8: puntos_negativos += 9
    
    # Proteínas (puntos positivos)
    puntos_positivos = 0
    if proteinas > 1.6: puntos_positivos += 1
    if proteinas > 3.2: puntos_positivos += 2
    if proteinas > 4.8: puntos_positivos += 3
    
    score_final = puntos_negativos - puntos_positivos
    
    if score_final <= -1: return 'A'
    elif score_final <= 2: return 'B'
    elif score_final <= 10: return 'C'
    elif score_final <= 18: return 'D'
    else: return 'E'


def obtener_letra_cluster(cluster):
    """
    Mapea cluster (0-3) a letra:
    0: B (falso saludable)
    1: D (ultraprocesado)
    2: A (verdaderamente saludable)
    3: C (simple malo)
    """
    cluster_to_letter = {
        0: "B",  # Falso saludable
        1: "D",  # Ultraprocesado
        2: "A",  # Verdaderamente saludable
        3: "C",  # Simple malo
    }
    return cluster_to_letter.get(cluster, "C")


def obtener_numero_aditivos(traffic_light_dominante):
    """
    Mapea traffic_light a número (1, 2, 3):
    - SEGURO → 1
    - PRECAUCIÓN → 2
    - EVITABLE → 3
    """
    if traffic_light_dominante in ["EVITABLE", "EVITAR"]:
        return 3
    elif traffic_light_dominante in ["PRECAUCION", "PRECAUCIÓN"]:
        return 2
    else:
        return 1


def perfilado_cluster_aditivos(cluster, traffic_light_dominante):
    """
    Genera el perfil final basado en cluster y aditivos.
    """
    cluster_names = {
        0: "Procesados/Ultraprocesados Engañosos",
        1: "Ultraprocesados Críticos",
        2: "Base Natural",
        3: "Procesados/Ultraprocesados de Carga Calórica Vacía"
    }
    
    cluster_name = cluster_names.get(cluster, "Desconocido")
    
    if traffic_light_dominante in ["EVITABLE", "EVITAR"]:
        return f"{cluster_name} - Aditivos a Evitar ❌"
    elif traffic_light_dominante in ["PRECAUCION", "PRECAUCIÓN"]:
        return f"{cluster_name} - Aditivos de Precaución ⚠️"
    else:
        return f"{cluster_name} - Aditivos Seguros ✅"


# ==============================================================================
# 3. FUNCIÓN MAESTRA (ORQUESTADOR)
# ==============================================================================

def ejecutar_pipeline_alimento(barcode):
    """
    Pipeline completo:
    1. Obtener datos de Open Food Facts API v2
    2. Extraer aditivos (oficial + regex rescue)
    3. Mapear a traffic_light SSI
    4. Aplicar K-Means para clasificar alimento
    5. Generar Nutriscore 2.0 (letra + número)
    """
    
    barcode_str = str(barcode).strip()
    
    # Obtener datos de API
    print(f"🌐 [API] Consultando Open Food Facts para barcode: {barcode_str}")
    datos_alimento = obtener_datos_openfoodfacts(barcode_str)
    
    if datos_alimento is None:
        print(f"❌ [FALLO] El producto {barcode_str} no existe en Open Food Facts.")
        return None
    
    # ==================================================================
    # VALIDAR QUE TENGA DATOS COMPLETOS
    # ==================================================================
    
    if datos_alimento['nutriscore'] == 'UNKNOWN' or not datos_alimento['nutriscore']:
        print(f"❌ [INCOMPLETO] El producto {barcode_str} no tiene Nutriscore en Open Food Facts.")
        return {
            'error': True,
            'mensaje': 'Este producto no tiene Nutriscore disponible en Open Food Facts'
        }
    
    if datos_alimento['nova'] == 0:
        print(f"❌ [INCOMPLETO] El producto {barcode_str} no tiene NOVA en Open Food Facts.")
        return {
            'error': True,
            'mensaje': 'Este producto no tiene clasificación NOVA disponible en Open Food Facts'
        }
    
    # ==================================================================
    # PROCESAMIENTO DE ADITIVOS Y EXTRACCIÓN SSI
    # ==================================================================
    
    # Rescate REGEX adicional si no hay aditivos oficiales
    if datos_alimento['ingredients_text_raw'] and not datos_alimento['aditivos_lista']:
        codigos_encontrados = re.findall(r'\b[Ee]-?\d{3,4}\b', datos_alimento['ingredients_text_raw'])
        for codigo in codigos_encontrados:
            codigo_limpio = f"en:{codigo.lower().replace('-', '')}"
            if codigo_limpio not in datos_alimento['aditivos_lista']:
                datos_alimento['aditivos_lista'].append(codigo_limpio)
    
    # Obtener traffic_light de aditivos
    aditivos_detallados, traffic_lights, traffic_light_dominante = obtener_traffic_light_aditivos(
        datos_alimento['aditivos_lista']
    )
    
    # ==================================================================
    # ESTIMACIONES EN NULOS
    # ==================================================================
    
    nutriscore_final = datos_alimento['nutriscore']
    nova_final = datos_alimento['nova']
    
    nutriscore_estimado = False
    nova_estimado = False
    
    # Estimar NOVA si es 0
    if nova_final == 0:
        nova_final = estimar_grupo_nova(datos_alimento['aditivos_lista'])
        nova_estimado = True
        datos_alimento['nova'] = nova_final
    
    # Estimar Nutriscore si es unknown
    if nutriscore_final == 'UNKNOWN' or not nutriscore_final:
        nutriscore_final = estimar_nutriscore_por_nutrientes(
            datos_alimento['energia'],
            datos_alimento['grasas'],
            datos_alimento['azucares'],
            datos_alimento['sal'],
            datos_alimento['proteinas']
        )
        nutriscore_estimado = True
        datos_alimento['nutriscore'] = nutriscore_final
    
    # ==================================================================
    # PREDICCIÓN K-MEANS
    # ==================================================================
    
    # Mapear Nutriscore a número
    ns_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
    nutriscore_num = ns_map.get(nutriscore_final, 3)
    
    # Vector: [Nutriscore_num, NOVA, Total_aditivos]
    # (Solo 3 features: los mismos con los que se entrenó el scaler)
    vector_alimento = np.array([[nutriscore_num, nova_final, len(traffic_lights)]])
    vector_scaled = scaler_alimentos.transform(vector_alimento)
    cluster_alimento = kmeans_alimentos.predict(vector_scaled)[0]
    
    # ==================================================================
    # GENERAR NUTRISCORE 2.0
    # ==================================================================
    
    letra = obtener_letra_cluster(cluster_alimento)
    numero = obtener_numero_aditivos(traffic_light_dominante)
    codigo_imagen = f"{letra}{numero}"  # A1, B2, D3, etc.
    
    perfil = perfilado_cluster_aditivos(cluster_alimento, traffic_light_dominante)
    
    # Calcular cargas para mostrar en la UI
    carga_seguro = traffic_lights.count("SEGURO")
    carga_peligroso = len(traffic_lights) - carga_seguro
    
    # ==================================================================
    # RETORNAR RESULTADOS
    # ==================================================================
    
    return {
        'info_basica': datos_alimento,
        'metricas_modelo': {
            'cluster_alimento': cluster_alimento,
            'letra_nutriscore2': letra,
            'numero_aditivos': numero,
            'codigo_imagen': codigo_imagen,
            'carga_clase_0': carga_seguro,
            'carga_clase_1': carga_peligroso,
            'perfil_final': perfil,
            'traffic_light_dominante': traffic_light_dominante,
            'traffic_lights': traffic_lights,
            'aditivos_detallados': aditivos_detallados,
            'nutriscore_estimado': nutriscore_estimado,
            'nova_estimado': nova_estimado
        }
    }
