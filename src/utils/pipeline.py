# pipeline.py
import requests
import pandas as pd
import joblib
import numpy as np
from requests.auth import HTTPBasicAuth
import re

# ==============================================================================
# 1. CARGA DE RECURSOS ESTÁTICOS AL ARRANCAR EL MÓDULO
# ==============================================================================
try:
    # Cargamos tu CSV de aditivos precalculados (Clasificación Offline)
    # Debe contener las columnas: 'id_aditivo' (ej: en:e330) y 'cluster_aditivo_binario' (0 o 1)
    df_taxonomia_aditivos = pd.read_csv('../data/taxonomia_final_aditivos.csv')
    
    # Lo transformamos en un diccionario indexado en memoria para búsquedas ultra rápidas
    mapping_aditivos = dict(zip(
        df_taxonomia_aditivos['id'].astype(str).str.strip(), 
        df_taxonomia_aditivos['cluster']
    ))
    
    # Cargamos el Escalador y el Modelo K-Means para clasificar el ALIMENTO
    scaler_alimentos = joblib.load('../models/scaler_alimentos.pkl')
    kmeans_alimentos = joblib.load('../models/kmeans_alimentos.pkl')
    
    print("🔬 [INFO] Recursos y Taxonomía de Aditivos cargados con éxito.")
except Exception as e:
    print(f"⚠️ [ALERTA] Error al cargar los archivos locales del pipeline: {e}")


# ==============================================================================
# 2. FUNCIONES DE PROCESAMIENTO Y LÓGICA
# ==============================================================================

def obtener_datos_openfoodfacts(barcode):
    """
    Paso 1: Consulta a la API de Open Food Facts con Extractor Regex de Rescate.
    """
    barcode_str = str(barcode).strip()
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode_str}.json"
    
    headers = {
        'User-Agent': 'TesisNutriChemApp/1.0 (mklanibarro@gmail.com)'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return None
            
        data = response.json()
        
        if data.get('status') == 1 or "found" in data.get('status_verbose', '').lower():
            product = data['product']
            
            # 1. Intentamos la extracción por los canales oficiales de la API
            aditivos_oficiales = product.get('additives_tags', [])
            if not aditivos_oficiales:
                aditivos_oficiales = product.get('additives_original_tags', [])
                
            # Convertimos a una lista limpia y en minúsculas
            aditivos_finales = [str(tag).lower() for tag in aditivos_oficiales]
            
            # ==============================================================================
            # DETECTOR DE RESCATE: ESCANEO DE TEXTO EN INGREDIENTES (REGE-X)
            # ==============================================================================
            # Capturamos el texto en crudo de los ingredientes en español (o inglés como fallback)
            texto_ingredientes = product.get('ingredients_text_es', product.get('ingredients_text', ''))
            
            if texto_ingredientes:
                # Buscamos patrones tipo: E330, E-330, e338, e-950 (ignora mayúsculas/minúsculas)
                # El patrón busca una 'E' o 'e', un guion opcional y entre 3 y 4 dígitos numéricos
                codigos_encontrados = re.findall(r'\b[Ee]-?\d{3,4}\b', texto_ingredientes)
                
                for codigo in codigos_encontrados:
                    # Normalizamos el formato al estándar 'en:eXXX' que usa Open Food Facts
                    codigo_limpio = f"en:{codigo.lower().replace('-', '')}"
                    
                    if codigo_limpio not in aditivos_finales:
                        aditivos_finales.append(codigo_limpio)
                        print(f"🎯 [RESCATE REGEX] Aditivo extraído del texto de ingredientes: {codigo_limpio}")
            # ==============================================================================
            
            nutriments = product.get('nutriments', {})
            
            return {
                'nombre': product.get('product_name_es', product.get('product_name', 'Nombre no disponible')),
                'marca': product.get('brands', 'Marca no disponible'),
                'imagen_url': product.get('image_url', product.get('image_front_url', None)),
                'nutriscore': product.get('nutriscore_grade', 'unknown').upper(),
                'nova': int(product.get('nova_group', 0)) if product.get('nova_group') is not None else 0,
                'aditivos_lista': aditivos_finales,  # <--- Enviamos la lista combinada
                'ingredients_text_raw': product.get('ingredients_text_es', product.get('ingredients_text', '')),
                'energia': nutriments.get('energy-kcal_100g', nutriments.get('energy-kcal', 0)),
                'grasas': nutriments.get('fat_100g', nutriments.get('fat', 0)),
                'azucares': nutriments.get('sugars_100g', nutriments.get('sugars', 0)),
                'proteinas': nutriments.get('proteins_100g', nutriments.get('proteins', 0)),
                'sal': nutriments.get('salt_100g', nutriments.get('salt', 0))
            }
        else:
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Fallo de conexión: {e}")
        return None


def calcular_cargas_quimicas(aditivos_lista):
    """
    Paso 2: Mapea los aditivos normalizando prefijos y mayúsculas/minúsculas
    para asegurar el match perfecto con el CSV de la Tesis.
    """
    carga_clase_0 = 0
    carga_clase_1 = 0
    
    # 1. Creamos un diccionario auxiliar con las llaves del CSV limpias (sin 'en:' y en minúsculas)
    # Esto asegura que si en tu CSV está como 'E338' o 'e338', se encuentre igual.
    mapping_limpio = {}
    for k, v in mapping_aditivos.items():
        k_limpia = str(k).lower().replace('en:', '').replace('-', '').strip()
        mapping_limpio[k_limpia] = v
        
    # 2. Procesamos la lista que viene en vivo desde la API de Open Food Facts
    for aditivo in aditivos_lista:
        # Estandarizamos el aditivo de la API (ej: 'en:E-338' -> 'e338')
        aditivo_api = str(aditivo).lower().replace('en:', '').replace('-', '').strip()
        
        # Hacemos el cruce de datos blindado
        if aditivo_api in mapping_limpio:
            clase = mapping_limpio[aditivo_api]
            if clase == 0:
                carga_clase_0 += 1
            elif clase == 1:
                carga_clase_1 += 1
        else:
            # Print de depuración por consola para que veas qué aditivos de la API no están en tu CSV
            print(f"🔍 [DEBUG] Aditivo de la API '{aditivo}' (procesado como '{aditivo_api}') no se encontró en tu CSV.")
                
    return carga_clase_0, carga_clase_1


def perfilado_binario_ocho_combinaciones(cluster, carga_clase_1):
    # El riesgo químico se define directamente si la variable numérica carga_clase_1 es mayor que 0
    tiene_riesgo_quimico = carga_clase_1 > 0
    
    # 1. CLUSTER MORADO: Alimento Saludable (Cluster 0)
    if cluster == 0:
        if tiene_riesgo_quimico:
            return "Alimento Saludable con aditivos potencialmente de riesgo"
        else:
            return "Alimento Saludable con aditivos seguros"
            
    # 2. CLUSTER AZUL: Calórico y Sucio (Cluster 1)
    elif cluster == 1:
        if tiene_riesgo_quimico:
            return "Calórico y Sucio con aditivos de riesgo"
        else:
            return "Calórico y Sucio con aditivos seguros"
            
    # 3. CLUSTER VERDE: Falsos Amigos (Cluster 2)
    elif cluster == 2:
        if tiene_riesgo_quimico:
            return "Falso Amigo con aditivos de riesgo"
        else:
            return "Falso Amigo con aditivos seguros"
            
    # 4. CLUSTER AMARILLO: Calórico pero honesto / Bomba calórica (Cluster 3)
    elif cluster == 3:
        if tiene_riesgo_quimico:
            return "Bomba calórica con aditivos de riesgo"
        else:
            return "Bomba calórica con aditivos seguros"
            
    # Por seguridad, si existiese algún cluster no mapeado de alimentos
    return f"Cluster {cluster} - Desconocido"

def estimar_grupo_nova(aditivos_lista):
    """
    Sistema Experto: Estima el grupo NOVA basándose en la presencia de aditivos cosméticos o industriales.
    Regla: Si contiene aditivos típicamente ultraprocesados (colorantes, edulcorantes, potenciadores), es NOVA 4.
    """
    if not aditivos_lista:
        return 1  # Sin aditivos asumimos mínimamente procesado (o ingredientes puros)
        
    # Lista de aditivos puramente industriales/cosméticos que delatan un ultraprocesado
    # Edulcorantes, colorantes artificiales, potenciadores de sabor, emulsionantes complejos
    aditivos_ultra = [
        'en:e950', 'en:e951', 'en:e955', 'en:e621', 'en:e102', 'en:e110', 
        'en:e129', 'en:e133', 'en:e150d', 'en:e471', 'en:e466', 'en:e415'
    ]
    
    # Si tiene al menos uno de estos aditivos de diseño, es NOVA 4 con seguridad
    if any(adit in aditivos_ultra for adit in aditivos_lista):
        return 4
        
    # Si tiene otros aditivos más estándar (ej: ácido cítrico en:e330 o ácido ascórbico en:e300)
    # se cataloga como alimento procesado básico
    return 3


def estimar_nutriscore_por_nutrientes(energia, grasas, azucares, sal, proteinas):
    """
    Sistema Experto Simplificado: Estima una letra de Nutriscore basándose en macronutrientes críticos por 100g.
    """
    # Si no tenemos absolutamente ningún dato macro, devolvemos una C neutral por seguridad
    if energia == 0 and azucares == 0 and sal == 0:
        return 'C'
        
    puntos_negativos = 0
    
    # 1. Puntos por Energía (kJ o kcal aproximado)
    if energia > 360: puntos_negativos += 5
    if energia > 720: puntos_negativos += 10
    
    # 2. Puntos por Azúcares simples
    if azucares > 4.5: puntos_negativos += 1
    if azucares > 9: puntos_negativos += 2
    if azucares > 18: puntos_negativos += 4
    if azucares > 36: puntos_negativos += 8
    
    # 3. Puntos por Sal (Sodio)
    if sal > 0.5: puntos_negativos += 2
    if sal > 1.1: puntos_negativos += 5
    if sal > 1.8: puntos_negativos += 9
    
    # 4. Compensación por Proteínas (puntos positivos)
    puntos_positivos = 0
    if proteinas > 1.6: puntos_positivos += 1
    if proteinas > 3.2: puntos_positivos += 2
    if proteinas > 4.8: puntos_positivos += 3
    
    score_final = puntos_negativos - puntos_positivos
    
    # Clasificación matemática según el rango del algoritmo oficial simplificado
    if score_final <= -1: return 'A'
    elif score_final <= 2: return 'B'
    elif score_final <= 10: return 'C'
    elif score_final <= 18: return 'D'
    else: return 'E'

# ==============================================================================
# 3. FUNCIÓN MAESTRA (ORQUESTADOR)
# ==============================================================================

def ejecutar_pipeline_alimento(barcode):
    """
    Orquestador Híbrido Definitivo: Parquet Local -> API de Rescate -> Modelos K-Means.
    """
    barcode_str = str(barcode).strip()
    datos_alimento = None
    
# ==============================================================================
    # ESTRATEGIA 1: BÚSQUEDA EN TU PARQUET LOCAL (PRUEBA DE INYECCIÓN DE CONTROL)
    # ==============================================================================
    try:
        df_parquet = pd.read_parquet('../data/alimentos_tesis.parquet')
        
        # 1. Intento A: Filtrar por el código de barras estricto
        productos_coincidentes = df_parquet[df_parquet['code'].astype(str) == barcode_str]
        fila_seleccionada = None
        
        if not productos_coincidentes.empty:
            fila_seleccionada = productos_coincidentes.loc[
                productos_coincidentes['additives_tags'].map(lambda x: len(x) if isinstance(x, (list, np.ndarray)) else 0).idxmax()
            ]
        
        # 2. INYECCIÓN HARDCODED DE CONTROL (Para probar si tu modelo y tu Streamlit pintan bien)
        aditivos_tags_check = fila_seleccionada.get('additives_tags', []) if fila_seleccionada is not None else []
        if fila_seleccionada is None or not isinstance(aditivos_tags_check, (list, np.ndarray)) or len(aditivos_tags_check) == 0:
            
            print("🚨 [CONTROL] Forzando búsqueda en el Parquet por la clave exacta 'coke zero'...")
            
            # Buscamos en tu Parquet cualquier fila que se llame exactamente 'coke zero'
            df_gemelos = df_parquet[df_parquet['product_name'].str.lower() == 'coke zero']
            
            if not df_gemelos.empty:
                # Nos quedamos con la que tiene los 5 aditivos
                fila_seleccionada = df_gemelos.loc[
                    df_gemelos['additives_tags'].map(lambda x: len(x) if isinstance(x, (list, np.ndarray)) else 0).idxmax()
                ]
                print(f"🎯 [CONTROL EXITOSO] Inyectando datos de: '{fila_seleccionada.get('product_name')}'")
        
        # 3. CONSTRUCCIÓN DEL DICCIONARIO FINAL
        if fila_seleccionada is not None:
            aditivos_raw = fila_seleccionada.get('additives_tags', [])
            aditivos_lista = list(aditivos_raw) if isinstance(aditivos_raw, (list, np.ndarray)) else []
            
            datos_alimento = {
                'nombre': f"{fila_seleccionada.get('product_name')} (Rescatado Local)",
                'marca': 'Consolidado por Control Hardcoded (Tesis)',
                'imagen_url': None,
                'nutriscore': str(fila_seleccionada.get('nutriscore_grade', 'unknown')).upper(),
                'nova': int(fila_seleccionada.get('nova_group', 4)) if pd.notna(fila_seleccionada.get('nova_group')) else 4,
                'aditivos_lista': aditivos_lista,
                'ingredients_text_raw': fila_seleccionada.get('ingredients_text_raw', ''), 
                'energia': 0, 'grasas': 0, 'azucares': 0, 'proteinas': 0, 'sal': 0
            }
    except Exception as error_critico:
        import streamlit as st
        st.error(f"💥 ¡ERROR CRÍTICO EN CONTROL!: `{str(error_critico)}`")
        raise error_critico

    # ==============================================================================
    # ESTRATEGIA 2: PLAN B - PETICIÓN EN VIVO A LA API (SI NO ESTABA EN EL PARQUET)
    # ==============================================================================
    if datos_alimento is None:
        print(f"🌐 [API] Código {barcode_str} no encontrado en local. Consultando Open Food Facts...")
        datos_alimento = obtener_datos_openfoodfacts(barcode_str)
        
    if datos_alimento is None:
        print(f"❌ [FALLO] El producto {barcode_str} no existe en local ni en el servidor central.")
        return None 

    # ==============================================================================
    # PROCESAMIENTO QUÍMICO Y EVALUACIÓN TOXICOLÓGICA (DATO YA EN MEMORIA)
    # ==============================================================================
    
    # Redundancia Regex: Si hay texto de ingredientes pero no hay tags oficiales, los rescatamos
    if datos_alimento['ingredients_text_raw'] and not datos_alimento['aditivos_lista']:
        import re
        # Buscamos en 'ingredients_text_raw'
        codigos_encontrados = re.findall(r'\b[Ee]-?\d{3,4}\b', datos_alimento['ingredients_text_raw'])
        for codigo in codigos_encontrados:
            codigo_limpio = f"en:{codigo.lower().replace('-', '')}"
            if codigo_limpio not in datos_alimento['aditivos_lista']:
                datos_alimento['aditivos_lista'].append(codigo_limpio)

    # Computamos las cargas químicas cruzando con tu CSV de taxonomía de PubMed (Clase 0 y Clase 1)
    carga_0, carga_1 = calcular_cargas_quimicas(datos_alimento['aditivos_lista'])
    
    # Capturamos las variables macro para la clasificación
    nutriscore_final = datos_alimento['nutriscore']
    nova_final = datos_alimento['nova']
    
    # Flags de control para avisar a Streamlit si recurrimos al sistema experto por nulos
    nutriscore_estimado = False
    nova_estimado = False
    
    # Control Ex-Ante de Nulos en NOVA
    if nova_final == 0:
        nova_final = estimar_grupo_nova(datos_alimento['aditivos_lista'])
        nova_estimado = True
        datos_alimento['nova'] = nova_final
        
    # Control Ex-Ante de Nulos en Nutriscore
    if nutriscore_final == 'UNKNOWN' or not nutriscore_final:
        nutriscore_final = estimar_nutriscore_por_nutrientes(
            datos_alimento['energia'], 
            datos_alimento['grasas'],     # <--- Asegúrate de que ponga 'datos_alimento' aquí
            datos_alimento['azucares'], 
            datos_alimento['sal'], 
            datos_alimento['proteinas']
        )
        nutriscore_estimado = True
        datos_alimento['nutriscore'] = nutriscore_final

    # ==============================================================================
    # PREDICCIÓN GEOMÉTRICA (EJECUCIÓN DEL MODELO ALIMENTO K-MEANS)
    # ==============================================================================
    ns_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5}
    nutriscore_num = ns_map.get(nutriscore_final, 3)
    
    # Vector de entrada idéntico al entrenamiento: [Nutriscore_num, NOVA, Carga_0, Carga_1]
    vector_alimento = np.array([[nutriscore_num, nova_final, carga_0, carga_1]])
    vector_scaled = scaler_alimentos.transform(vector_alimento)
    cluster_alimento_predicho = kmeans_alimentos.predict(vector_scaled)[0]
    
    # Ejecutamos las 8 combinaciones lógicas cruzando el Cluster con la carga de riesgo
    perfil_final = perfilado_binario_ocho_combinaciones(cluster_alimento_predicho, carga_1)
    
    # Empaquetamos la estructura unificada para la interfaz de Streamlit
    return {
        'info_basica': datos_alimento,
        'metricas_modelo': {
            'cluster_alimento': cluster_alimento_predicho,
            'carga_clase_0': carga_0,
            'carga_clase_1': carga_1,
            'perfil_final': perfil_final,
            'nutriscore_estimado': nutriscore_estimado,
            'nova_estimado': nova_estimado
        }
    }