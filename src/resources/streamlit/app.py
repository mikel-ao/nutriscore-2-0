# app.py
import streamlit as st
import pipeline as pipe
from pathlib import Path
import time

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="NutriScore 2.0",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Metadata para preview (aparece cuando compartes el link)
st.markdown('<meta name="description" content="NUTRI-SCORE 2.0">', unsafe_allow_html=True)

# ============================================================================
# CARGAR RECURSOS AL INICIAR
# ============================================================================

@st.cache_resource
def init_recursos():
    """Cargar recursos una sola vez"""
    recursos = pipe.cargar_recursos()
    if recursos is None:
        st.error("❌ ERROR: No se pudieron cargar los recursos. Verifica que existan los archivos.")
        st.stop()
    return recursos

# Cargar recursos
recursos_globales = init_recursos()

# Inyectar en el módulo pipeline para que los use
pipe.df_ssi_aditivos = recursos_globales['df_ssi']
pipe.mapping_traffic_light = recursos_globales['mapping']
pipe.scaler_alimentos = recursos_globales['scaler']
pipe.kmeans_alimentos = recursos_globales['kmeans']

# ============================================================================
# ENCABEZADO
# ============================================================================

st.title("NutriScore 2.0")
st.markdown("### Clasificación Multidimensional de Alimentos")

st.markdown("---")

# ============================================================================
# ENTRADA
# ============================================================================

barcode_input = st.text_input(
    "📱 Introduce el código de barras:",
    value="",
    placeholder="Ej: 5060095140439"
)

# ============================================================================
# LÓGICA PRINCIPAL
# ============================================================================

if barcode_input and barcode_input.strip():
    
    with st.spinner("🔍 Analizando alimento..."):
        time.sleep(0.3)
        resultado = pipe.ejecutar_pipeline_alimento(barcode_input.strip())
    
    if resultado is None:
        st.error(f"❌ Producto no encontrado: `{barcode_input.strip()}`")
        st.stop()
    
    # Verificar si hay error de datos incompletos
    if resultado.get('error'):
        st.error(f"⚠️ {resultado['mensaje']}")
        st.info("Intenta con otro producto que tenga información completa en Open Food Facts")
        st.stop()
    
    # Desempaquetar resultados
    info = resultado["info_basica"]
    metricas = resultado["metricas_modelo"]
    
    # ====================================================================
    # LAYOUT PRINCIPAL
    # ====================================================================
    
    col1, col2 = st.columns([1, 2])
    
    # COLUMNA 1: IMAGEN
    with col1:
        st.markdown("### 🛒 Producto")
        
        if info["imagen_url"]:
            st.image(info["imagen_url"], width=200)
        else:
            st.info("Imagen no disponible")
        
        st.markdown(f"**{info['nombre']}**")
        st.caption(info['marca'])
    
    # COLUMNA 2: NUTRISCORE 2.0 + ADITIVOS
    with col2:
                
        # Mostrar imagen del Nutriscore 2.0
        imagen_path = Path(__file__).parent / "nutri" / f"{metricas['codigo_imagen']}.png"
        
        if imagen_path.exists():
            st.image(str(imagen_path), width=250)
        else:
            st.warning(f"Imagen {metricas['codigo_imagen']}.png no encontrada")
        
        st.markdown(f"**Clasificación:** {metricas['perfil_final']}")
        
        st.markdown("---")
        
        # ADITIVOS DETECTADOS
        st.markdown("### 🧪 Aditivos Detectados")
        
        if metricas["aditivos_detallados"]:
            # Crear tabs para las 3 categorías
            tab1, tab2, tab3 = st.tabs(["🟢 Seguros", "🟡 Precaución", "🔴 Evitables"])
            
            # Separar aditivos por categoría
            seguros = []
            precaucion = []
            evitables = []
            
            for aditivo in metricas["aditivos_detallados"]:
                if aditivo['traffic_light'] == "SEGURO":
                    seguros.append(aditivo)
                elif aditivo['traffic_light'] in ["PRECAUCION", "PRECAUCIÓN"]:
                    precaucion.append(aditivo)
                else:  # EVITABLE, EVITAR
                    evitables.append(aditivo)
            
            with tab1:
                if seguros:
                    for aditivo in seguros:
                        st.markdown(f"✅ **{aditivo['e_code']}** — {aditivo['nombre']}")
                else:
                    st.markdown("*Ninguno*")
            
            with tab2:
                if precaucion:
                    for aditivo in precaucion:
                        st.markdown(f"⚠️ **{aditivo['e_code']}** — {aditivo['nombre']}")
                else:
                    st.markdown("*Ninguno*")
            
            with tab3:
                if evitables:
                    for aditivo in evitables:
                        st.markdown(f"❌ **{aditivo['e_code']}** — {aditivo['nombre']}")
                else:
                    st.markdown("*Ninguno*")
        
        else:
            st.markdown("✨ Ningún aditivo detectado")
        
        # RESUMEN
        st.markdown("---")
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            seguros_count = sum(1 for a in metricas["aditivos_detallados"] if a['traffic_light'] == "SEGURO")
            st.metric("Seguros", seguros_count)
        
        with col_b:
            precaucion_count = sum(1 for a in metricas["aditivos_detallados"] if a['traffic_light'] in ["PRECAUCION", "PRECAUCIÓN"])
            st.metric("Precaución", precaucion_count)
        
        with col_c:
            evitables_count = sum(1 for a in metricas["aditivos_detallados"] if a['traffic_light'] in ["EVITABLE", "EVITAR"])
            st.metric("Evitables", evitables_count)

else:
    st.info("👋 Introduce un código de barras para analizar un alimento")

# ============================================================================
# FOOTER CON IMAGEN
# ============================================================================

st.markdown("---")
imagen_footer = Path(__file__).parent / "nutri" / "2.png"

if imagen_footer.exists():
    st.image(str(imagen_footer), use_container_width=True)
else:
    st.warning(f"⚠️ Imagen no encontrada: {imagen_footer}")
