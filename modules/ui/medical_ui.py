import streamlit as st
from modules.db.db_medical import (
    get_medical_history_mock, 
    get_evaluations_mock,
    CAT_ESTADOS, 
    CAT_TIPOS_PRUEBA, 
    CAT_SANGRE
)

def render_medical_module():
    st.header("🏥 Módulo Médico Integral", divider="green")
    
    # 1. Selector de Jugadora (Llave de conexión)
    jugadora = st.selectbox("Seleccione Jugadora:", ["Jugadora A", "Jugadora B"])
    
    # 2. Formulario de Registro Rápido (Uso de Catálogos - Punto 14)
    with st.expander("➕ Registrar Nueva Evaluación (Doctor)"):
        c1, c2, c3 = st.columns(3)
        with c1:
            tipo = st.selectbox("Tipo de Prueba", CAT_TIPOS_PRUEBA)
        with c2:
            estado = st.selectbox("Estado Resultante", CAT_ESTADOS)
        with c3:
            fecha = st.date_input("Fecha de evaluación")
        
        observaciones = st.text_area("Notas Clínicas / Observaciones")
        
        if st.button("Guardar en Expediente"):
            st.success(f"✅ Registro de {tipo} guardado correctamente para {jugadora}.")

    # 3. Pestañas de Información (Estructura de Datos - Punto 13)
    tab1, tab2, tab3 = st.tabs([
        "📋 Historial Base", 
        "🩺 Evolución Clínica", 
        "📊 Wellness Integrado"
    ])

    with tab1:
        st.subheader("Información Permanente")
        info = get_medical_history_mock(jugadora)
        
        # Métricas de salud rápida
        col1, col2, col3 = st.columns(3)
        col1.metric("Grupo Sanguíneo", info["sangre"])
        col2.info(f"**Alergias:** {info['alergias']}")
        col3.warning(f"**Cirugías:** {info['cirugias']}")

        st.divider()

        # --- ALIMENTACIÓN POR CARGA DE ARCHIVOS ---
        st.subheader("📁 Documentación Externa (PDF/Imágenes)")
        st.write("Cargue informes externos, resonancias o resultados de laboratorio.")
        
        archivo_subido = st.file_uploader(
            f"Subir documento para {jugadora}", 
            type=['pdf', 'png', 'jpg'],
            key=f"uploader_{jugadora}"
        )

        if archivo_subido:
            st.success(f"Archivo '{archivo_subido.name}' recibido y vinculado al ID de la jugadora.")

    with tab2:
        st.subheader("Histórico de Pruebas Realizadas")
        df_evals = get_evaluations_mock(jugadora)
        st.dataframe(df_evals, use_container_width=True)

    with tab3:
        st.info("Esta sección conectará las cargas de entrenamiento con el riesgo de lesión.")