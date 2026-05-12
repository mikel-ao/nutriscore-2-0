# app.py - VERSIÓN MÓVIL CON CÁMARA
import streamlit as st
import pipeline_mobile as pipe
from pathlib import Path
import time
from streamlit_webrtc import webrtc_streamer, RTCConfiguration
import cv2
from pyzbar.pyzbar import decode
import numpy as np

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================

st.set_page_config(
    page_title="NutriScore 2.0 Mobile",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

col_logo, col_title = st.columns([0.5, 3])

with col_logo:
    try:
        st.image("nutri/A1.png", width=80)
    except:
        st.write("🍎")

with col_title:
    st.title("NutriScore 2.0 Mobile")
    st.markdown("### Escanea códigos de barras")

st.markdown("---")

# ============================================================================
# TABS: CÁMARA O ENTRADA MANUAL
# ============================================================================

tab_camera, tab_manual = st.tabs(["📷 Escanear", "⌨️ Código Manual"])

barcode_result = None

# ============================================================================
# TAB 1: ESCANEAR CON CÁMARA
# ============================================================================

with tab_camera:
    st.markdown("### 📷 Escanea un código de barras")
    
    # Configuración WebRTC
    rtc_configuration = RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    )
    
    class BarCodeProcessor:
        def recv(self, frame):
            img = frame.to_ndarray(format="bgr24")
            
            # Decodificar códigos de barras
            barcodes = decode(img)
            
            for barcode in barcodes:
                # Dibujar rectángulo alrededor del código
                (x, y, w, h) = barcode.rect
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Mostrar el valor
                barcode_data = barcode.data.decode("utf-8")
                cv2.putText(
                    img,
                    barcode_data,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )
                
                # Guardar resultado
                st.session_state.barcode_found = barcode_data
            
            return img
    
    webrtc_streamer(
        key="barcode-scanner",
        mode="sendrecv",
        rtc_configuration=rtc_configuration,
        video_frame_callback=BarCodeProcessor().recv,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )
    
    # Mostrar código detectado
    if "barcode_found" in st.session_state and st.session_state.barcode_found:
        st.success(f"✅ Código detectado: `{st.session_state.barcode_found}`")
        barcode_result = st.session_state.barcode_found
        
        if st.button("🔍 Analizar este código", key="analyze_camera"):
            st.session_state.process_barcode = True
            st.session_state.current_barcode = barcode_result

# ============================================================================
# TAB 2: ENTRADA MANUAL
# ============================================================================

with tab_manual:
    st.markdown("### ⌨️ Introduce el código manualmente")
    
    barcode_input = st.text_input(
        "Código de barras:",
        value="",
        placeholder="Ej: 5060095140439"
    )
    
    if barcode_input and st.button("🔍 Analizar", key="analyze_manual"):
        st.session_state.process_barcode = True
        st.session_state.current_barcode = barcode_input.strip()

# ============================================================================
# PROCESAR BARCODE
# ============================================================================

if "process_barcode" in st.session_state and st.session_state.process_barcode:
    barcode = st.session_state.current_barcode
    
    with st.spinner("🔍 Analizando alimento..."):
        time.sleep(0.3)
        resultado = pipe.ejecutar_pipeline_alimento(barcode)
    
    if resultado is None:
        st.error(f"❌ Producto no encontrado: `{barcode}`")
        st.session_state.process_barcode = False
    elif resultado.get('error'):
        st.error(f"⚠️ {resultado['mensaje']}")
        st.info("Intenta con otro producto que tenga información completa")
        st.session_state.process_barcode = False
    else:
        # Desempaquetar resultados
        info = resultado["info_basica"]
        metricas = resultado["metricas_modelo"]
        
        st.markdown("---")
        st.subheader("🎯 Tu NutriScore 2.0")
        
        # LAYOUT MOBILE
        col1, col2 = st.columns([1, 1.5])
        
        # COLUMNA 1: IMAGEN
        with col1:
            st.markdown("### 🛒 Producto")
            
            if info["imagen_url"]:
                st.image(info["imagen_url"], width=150)
            else:
                st.info("Imagen no disponible")
            
            st.markdown(f"**{info['nombre'][:40]}**")
            st.caption(info['marca'][:30])
        
        # COLUMNA 2: NUTRISCORE 2.0 + ADITIVOS
        with col2:
            # Mostrar imagen del Nutriscore 2.0
            imagen_path = Path(__file__).parent / "nutri" / f"{metricas['codigo_imagen']}.png"
            
            if imagen_path.exists():
                st.image(str(imagen_path), width=200)
            else:
                st.warning(f"Imagen {metricas['codigo_imagen']}.png no encontrada")
            
            st.markdown(f"**{metricas['perfil_final']}**")
        
        st.markdown("---")
        
        # ADITIVOS DETECTADOS
        st.markdown("### 🧪 Aditivos")
        
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
                else:
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
        
        # Botón para escanear otro
        if st.button("🔄 Escanear otro"):
            st.session_state.process_barcode = False
            st.session_state.barcode_found = None
            st.rerun()
