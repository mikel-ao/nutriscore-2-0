# app.py
import streamlit as st
import pipeline as pipe  # Importamos tu orquestador lógico integrado

# 1. CONFIGURACIÓN DE LA PÁGINA (Estilo panorámico moderno)
st.set_page_config(
    page_title="NutriChem Analyzer", 
    page_icon="🔬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS mínimos para redondear contenedores de Streamlit
st.markdown("""
    <style>
    .stAlert { border-radius: 12px; }
    div[data-testid="stTable"] { border-radius: 10px; overflow: hidden; }
    </style>
""", unsafe_allow_html=True)

# 2. ENCABEZADO DE LA APLICACIÓN
st.title("🔬 Pipeline de Clasificación Inteligente de Alimentos")
st.markdown("### *Modelado predictivo cruzado: Calidad Nutricional vs. Evidencia Química (PubMed)*")
st.markdown("---")

# 3. CONTROL DE ENTRADA (Barra Lateral)
st.sidebar.header("📥 Escaneo de Producto")
st.sidebar.write("Introduce o escanea el código de barras (EAN/UPC) del alimento para ejecutar el pipeline de la tesis.")

barcode_input = st.sidebar.text_input("Código de Barras:", value="", placeholder="Ej: 8410013017770")

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Nota metodológica:** La clasificación de aditivos está precalculada (offline) en base a "
    "un modelo entrenado sobre la densidad de alertas científicas en PubMed, aplicando un criterio "
    "de tolerancia cero para la Clase 1."
)

# 4. EJECUCIÓN DEL PIPELINE DE DATOS
if barcode_input:
    # Mostramos un spinner académico mientras se conecta a la API y computa los clusters
    with st.spinner("Consultando Open Food Facts y ejecutando modelos predictivos..."):
        resultado = pipe.ejecutar_pipeline_alimento(barcode_input)
        
    if resultado is None:
        st.error(f"❌ **Error:** El código de barras `{barcode_input}` no existe en Open Food Facts o no hay conexión a Internet.")
    else:
        # Desempaquetamos los sub-diccionarios estructurados en pipeline.py
        info = resultado['info_basica']
        metricas = resultado['metricas_modelo']
        
        # ==============================================================================
        # CASSETTE DE CONTROL VISUAL (MÉDICO DE GUARDIA)
        # ==============================================================================
        st.warning("🚨 **Testigo de Control en Vivo (Datos Crudos de la API):**")
        st.write("Lista exacta de aditivos que el pipeline ha logrado extraer:")
        st.code(info['aditivos_lista']) 
        
        # Si quieres ver qué texto de ingredientes está leyendo el script, descomenta la línea de abajo:
        # st.write("**Texto de ingredientes indexado:**", info.get('nombre'))
        st.markdown("---")
        # ==============================================================================
        
        # DISEÑO DE LA INTERFAZ EN 3 COLUMNAS SIMÉTRICAS
        col1, col2, col3 = st.columns([1, 1.3, 1.7])
        
        # ----------------------------------------------------------------------
        # COLUMNA 1: FICHA TÉCNICA Y VISUALIZACIÓN
        # ----------------------------------------------------------------------
        with col1:
            st.subheader("🖼️ Identificación")
            if info['imagen_url']:
                st.image(info['imagen_url'], use_container_width=True, caption=info['nombre'])
            else:
                st.warning("⚠️ Imagen no disponible en la API.")
            
            st.markdown(f"**Producto:** {info['nombre']}")
            st.markdown(f"**Marca:** {info['marca']}")
            st.markdown(f"**Código:** `{barcode_input.strip()}`")

        # ----------------------------------------------------------------------
        # COLUMNA 2: INDICADORES OFICIALES Y MATRIZ NUTRICIONAL
        # ----------------------------------------------------------------------
        with col2:
            st.subheader("📊 Indicadores Oficiales")
            
            # Estandarización visual de Nutriscore mediante emoticonos de color
            ns = info['nutriscore']
            color_ns = {"A": "🟢", "B": "🍏", "C": "🟡", "D": "🟠", "E": "🔴"}.get(ns, "⚪")
            st.markdown(f"#### **Nutri-Score:** {color_ns} `{ns}`")
            
            # Formateo semántico del Grupo NOVA
            nova = info['nova']
            txt_nova = {
                1: "Mínimamente procesado",
                2: "Ingrediente culinario",
                3: "Alimento procesado",
                4: "Ultraprocesado (UFP)"
            }.get(nova, "No detectado")
            st.markdown(f"#### **Grupo NOVA:** `Grupo {nova}` — *{txt_nova}*")
            
            st.markdown("---")
            st.markdown("#### **Composición por 100g**")
            
            # Construcción limpia de la tabla de macronutrientes
            tabla_data = {
                "Nutriente": ["Energía", "Grasas", "Azúcares", "Proteínas", "Sal"],
                "Valor": [
                    f"{info['energia']:.1f} kcal" if isinstance(info['energia'], (int, float)) else f"{info['energia']}",
                    f"{info['grasas']:.1f} g",
                    f"{info['azucares']:.1f} g",
                    f"{info['proteinas']:.1f} g",
                    f"{info['sal']:.2f} g"
                ]
            }
            st.table(tabla_data)

        # ----------------------------------------------------------------------
        # COLUMNA 3: EL NÚCLEO DE LA TESIS (TU CLASIFICACIÓN PROPIA)
        # ----------------------------------------------------------------------
        with col3:
            st.subheader("🔬 Clasificación del Modelo (Tesis)")
            
            perfil = metricas['perfil_final']
            
            # Selector de color dinámico para el contenedor principal de tu diagnóstico
            if "de riesgo" in perfil.lower():
                st.error(f"### **Perfil Asignado:**\n## {perfil}")
            elif "falso amigo" in perfil.lower() or "potencialmente" in perfil.lower():
                st.warning(f"### **Perfil Asignado:**\n## {perfil}")
            else:
                st.success(f"### **Perfil Asignado:**\n## {perfil}")
            
            st.markdown("---")
            st.markdown("#### **Análisis Químico de Aditivos de Entrada**")
            
            # Desglose en tarjetas numéricas independientes de las cargas de aditivos
            c1, c2 = st.columns(2)
            c1.metric(
                label="Aditivos Clase 0 (Seguros)", 
                value=int(metricas['carga_clase_0']),
                help="Sustancias con nula o residual evidencia de riesgo indexada en PubMed."
            )
            c2.metric(
                label="Aditivos Clase 1 (Riesgo)", 
                value=int(metricas['carga_clase_1']),
                delta="- Alerta" if metricas['carga_clase_1'] > 0 else None,
                delta_color="inverse",
                help="Sustancias con alta saturación de literatura científica sobre toxicidad o disrupción metabólica."
            )
            
            # Listado de los aditivos concretos detectados por la API
            st.markdown("**Códigos de aditivos indexados en este producto:**")
            if info['aditivos_lista']:
                # Mostramos los aditivos en formato de etiquetas de código inline
                codigos_html = " ".join([f"`{adit.replace('en:', '').upper()}`" for adit in info['aditivos_lista']])
                st.markdown(codigos_html)
            else:
                st.markdown("*Ninguno detectado por la API.*")
                
            # Explicación del clúster de alimentos predicho por tu K-Means
            st.markdown("---")
            st.caption(
                f"**Nota del modelo predictivo:** Este alimento ha sido asignado de forma automatizada al "
                f"**Cluster de Alimento {metricas['cluster_alimento']}** mediante el algoritmo K-Means basado en sus "
                f"características nutricionales. El diagnóstico final responde a la regla de interacción química estricta."
            )
else:
    # Pantalla de bienvenida / Espera de datos
    st.info("👋 **Bienvenido al módulo interactivo.** Por favor, introduce o escanea un código de barras en la barra lateral izquierda para comenzar el análisis genómico del alimento.")
