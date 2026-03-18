import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from modules.db import db_medical 

def render_medical_module():
    # --- CABECERA VISUAL ---
    # Usamos la ruta que confirmamos en tu carpeta: assets/images/banner.png
    st.image("assets/images/banner.png", use_container_width=True)
    
    st.header("🏥 Gestión de Historias Clínicas")
    
    jugadoras = db_medical.get_lista_jugadoras()
    nombres_jugadoras = [j["nombre"] for j in jugadoras]
    
    # Selector en el panel principal
    nombre_seleccionado = st.selectbox("🔍 Seleccione la jugadora para gestionar su historial:", nombres_jugadoras)
    jugadora = next(j for j in jugadoras if j["nombre"] == nombre_seleccionado)

    st.divider()

    # --- CUERPO DEL MÓDULO ---
    col_info, col_chart = st.columns([1, 1])
    
    with col_info:
        # Aquí usamos la silueta/foto definida en tu base de datos o una imagen genérica de la carpeta
        # Si jugadora['foto'] es una ruta, asegúrate que sea correcta. 
        # Si no, puedes usar: st.image("assets/images/female.png", width=120)
        st.image(jugadora.get("foto", "assets/images/female.png"), width=120)
        st.subheader(f"{jugadora['nombre']}")
        st.write(f"**ID:** {jugadora['id']} | **Edad:** {jugadora['edad']} años")
        st.info("**Grupo Sanguíneo:** O+ | **Alergias:** Ninguna")

    with col_chart:
        # Resumen estadístico
        data_stats = db_medical.get_stats_disponibilidad()
        df_stats = pd.DataFrame(data_stats)
        fig = px.pie(df_stats, values='Días', names='Categoría', 
                     title="Disponibilidad Histórica",
                     color_discrete_sequence=px.colors.qualitative.Safe)
        fig.update_layout(margin=dict(t=30, b=0, l=0, r=0), height=220)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- SECCIÓN PRIORITARIA: CARGA DE HISTORIA CLÍNICA ---
    st.subheader("📁 Digitalización de Documentos Físicos")
    with st.expander("⬆️ Cargar Documentación (PDF/Analíticas/Resonancias)", expanded=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            tipo_doc = st.selectbox("Tipo de documento:", ["Historia Clínica Completa", "Informe de Cirugía", "Analítica Antigua", "Eco/Resonancia"])
        with col_f2:
            fecha_doc = st.date_input("Fecha del documento original:", datetime.now())
        
        uploaded_files = st.file_uploader("Arrastre los archivos aquí", accept_multiple_files=True)
        if st.button("Confirmar Carga al Historial Digital"):
            if uploaded_files:
                st.success(f"¡Carga exitosa! {len(uploaded_files)} documentos vinculados.")
            else:
                st.warning("Seleccione archivos para cargar.")

    # --- ANTECEDENTES Y CIRUGÍAS ---
    st.write("### Información Clínica Adicional")
    col_a, col_b = st.columns(2)
    
    with col_a:
        with st.expander("🩺 Antecedentes y Medicación"):
            st.checkbox("Anemia ferropénica", value=True)
            st.text_input("Medicación Habitual:")
    
    with col_b:
        with st.expander("🩹 Cirugías Previas"):
            st.selectbox("Categoría Quirúrgica:", db_medical.get_clasificacion_cirugias())
            st.text_area("Notas sobre la intervención:", height=68)

    # --- NUEVA EVALUACIÓN ---
    with st.expander("➕ Registrar Nueva Evaluación"):
        c1, c2 = st.columns(2)
        with c1: st.selectbox("Tipo de Prueba", db_medical.get_tipos_evaluacion())
        with c2: st.date_input("Fecha de hoy")
        st.text_area("Conclusiones médicas")