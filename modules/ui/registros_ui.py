import streamlit as st
import pandas as pd
from datetime import date
# --- IMPORTACIONES ---
from modules.db.db_players import load_players_db
from modules.db.db_medical import (
    get_tipos_evaluacion, 
    get_cat_estados_aptitud, 
    get_clasificacion_cirugias,
    save_medical_evaluation,
    save_surgery_record
)

def render_registros_module():
    st.header("📋 Historial Médico: Perfil de Jugadora")

    # --- 1. CARGA DE DATOS REALES ---
    jug_df = load_players_db()
    
    columna_nombre = 'nombre_jugadora'

    if jug_df is not None and not jug_df.empty:
        if columna_nombre not in jug_df.columns:
            columna_nombre = jug_df.columns[2] 
        
        listado_jugadoras = ["Seleccionar..."] + sorted(jug_df[columna_nombre].dropna().astype(str).unique().tolist())
    else:
        st.error("No se pudieron cargar las jugadoras.")
        return

    jugadora_seleccionada = st.selectbox(
        "👤 Seleccione la Jugadora para consultar o registrar datos:", 
        listado_jugadoras,
        index=0
    )

    st.write("---")

    if jugadora_seleccionada == "Seleccionar...":
        st.info("Por favor, selecciona una jugadora para desplegar su ficha médica.")
        return

    # Extraemos los datos de la jugadora
    datos_jugadora = jug_df[jug_df[columna_nombre].astype(str) == jugadora_seleccionada].iloc[0]
    
    def clean_val(val):
        return str(val) if pd.notna(val) and str(val).lower() not in ["none", "nan", ""] else "No registrado"

    player_id_real = clean_val(datos_jugadora.get('id_jugadora'))

    # --- 🟢 ENCABEZADO: FICHA RESUMIDA ---
    with st.container(border=True):
        col_foto, col_datos = st.columns([1, 3])
        
        # Ajuste de Foto: Probamos con foto_url o imagen (común en otros módulos)
        foto_url = datos_jugadora.get('foto_url', datos_jugadora.get('foto_url_drive', datos_jugadora.get('imagen')))
        
        if not foto_url or pd.isna(foto_url) or str(foto_url).strip() == "":
            foto_url = "https://cdn-icons-png.flaticon.com/512/166/166344.png" 

        with col_foto:
            # Si es URL de Drive, a veces necesita un formateo especial, 
            # pero por ahora intentamos mostrarla directamente.
            st.image(foto_url, width=120)
        
        with col_datos:
            st.subheader(f"Ficha Técnica: {jugadora_seleccionada}")
            c1, c2, c3 = st.columns(3)
            c1.write(f"**ID:** {player_id_real}")
            # Si en otros módulos se ve, 'posicion' y 'dorsal' deberían funcionar
            c2.write(f"**Posición:** {clean_val(datos_jugadora.get('posicion'))}") 
            c3.write(f"**Dorsal:** {clean_val(datos_jugadora.get('dorsal'))}")
            st.write(f"**Plantel:** {clean_val(datos_jugadora.get('plantel'))}")

    st.write("---")

    # --- 🟡 CUERPO: LAS 3 SECCIONES DEL MÓDULO ---

    # 1. EVALUACIONES (La que ya tenías)
    with st.expander("➕ REGISTRAR NUEVA EVALUACIÓN", expanded=True):
        with st.form("form_evaluacion"):
            c1, c2 = st.columns(2)
            with c1: tipo_eval = st.selectbox("Tipo de Evaluación:", get_tipos_evaluacion())
            with c2: estado = st.selectbox("Estado Resultante:", get_cat_estados_aptitud())
            notas_eval = st.text_area("Resultados / Observaciones:")
            if st.form_submit_button("Guardar Evaluación en AWS"):
                if save_medical_evaluation(player_id_real, tipo_eval, estado, notas_eval):
                    st.success("Guardado correctamente.")
                else:
                    st.error("Error al guardar en AWS.")

    # 2. SECCIÓN CIRUGÍAS (Restaurada)
    with st.expander("✂️ HISTORIAL QUIRÚRGICO", expanded=False):
        with st.form("form_cirugias"):
            col1, col2 = st.columns(2)
            with col1:
                tipo_ciru = st.selectbox("Clasificación:", get_clasificacion_cirugias())
                fecha_ciru = st.date_input("Fecha de Cirugía:", date.today())
            with col2:
                proc_ciru = st.text_input("Procedimiento Realizado:")
            
            if st.form_submit_button("Registrar Cirugía"):
                if save_surgery_record(player_id_real, fecha_ciru, tipo_ciru, proc_ciru):
                    st.success("Cirugía registrada exitosamente.")
                else:
                    st.error("Error al registrar cirugía.")

    # 3. SECCIÓN DOCUMENTOS (Restaurada)
    with st.expander("📁 GESTIÓN DOCUMENTAL", expanded=False):
        st.write("Suba exámenes médicos o analíticas (PDF/JPG):")
        archivo = st.file_uploader("Seleccionar archivo", type=['pdf', 'jpg', 'png'], key="doc_med")
        if archivo:
            st.info("Archivo cargado temporalmente. La integración con S3 estará disponible pronto.")