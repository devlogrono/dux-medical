import streamlit as st
import pandas as pd
from datetime import date
import sys
import os

# --- CONEXIÓN CON LA ESTRUCTURA ---
current_dir = os.path.dirname(__file__)
modules_dir = os.path.abspath(os.path.join(current_dir, ".."))
if modules_dir not in sys.path:
    sys.path.append(modules_dir)

from db.db_players import load_players_db
from db.db_medical import (
    get_tipos_evaluacion, 
    get_cat_estados_aptitud, 
    get_clasificacion_cirugias,
    save_medical_evaluation,
    save_surgery_record
)

try:
    from reports.ui_individual import player_block_dux
except ImportError:
    from modules.reports.ui_individual import player_block_dux

def render_registros_module():
    st.title("📋 Historial Médico: Perfil de Jugadora")

    jug_df = load_players_db()
    
    if jug_df is not None and not jug_df.empty:
        col_nombre = 'nombre_jugadora'
        listado_jugadoras = ["Seleccionar..."] + sorted(jug_df[col_nombre].dropna().unique().tolist())
        jugadora_sel = st.selectbox("👤 Seleccione la Jugadora:", listado_jugadoras)
        
        st.divider()

        if jugadora_sel != "Seleccionar...":
            fila_jugadora = jug_df[jug_df[col_nombre] == jugadora_sel].iloc[0]
            datos_jugadora = fila_jugadora.to_dict()
            player_id = datos_jugadora.get('id_jugadora')

            # --- LÓGICA DE FOTOS ---
            url_final = datos_jugadora.get("foto_url_drive") if pd.notna(datos_jugadora.get("foto_url_drive")) else datos_jugadora.get("foto_url")
            datos_jugadora["foto_url"] = url_final if url_final and not pd.isna(url_final) else None

            # Componente visual de José
            player_block_dux(datos_jugadora)

            st.divider()

            c1, c2 = st.columns(2)
            
            with c1:
                with st.expander("➕ NUEVA EVALUACIÓN MÉDICA", expanded=True):
                    # El cargador de archivos debe estar fuera del formulario
                    archivo_pdf = st.file_uploader("1. Adjuntar Informe (PDF)", type=["pdf"], key="pdf_uploader_registros")
                    
                    with st.form("eval_form", clear_on_submit=True):
                        st.write("2. Detalles de la Evaluación")
                        tipo = st.selectbox("Tipo de Evaluación", get_tipos_evaluacion())
                        estado = st.selectbox("Estado de Aptitud", get_cat_estados_aptitud())
                        obs = st.text_area("Resultados y Observaciones", placeholder="Escriba aquí los detalles...")
                        
                        if st.form_submit_button("Guardar Evaluación", use_container_width=True):
                            # 1. Intentar guardar datos en AWS
                            if save_medical_evaluation(player_id, tipo, estado, obs):
                                st.success("✅ Datos guardados en AWS")
                                
                                # 2. Lógica de guardado físico del archivo
                                if archivo_pdf:
                                    try:
                                        save_path = os.path.join("assets", "documents", "evaluaciones")
                                        # Creamos un nombre único: ID_FECHA_NOMBRE.pdf
                                        file_name = f"{player_id}_{date.today()}_{archivo_pdf.name}"
                                        full_path = os.path.join(save_path, file_name)
                                        
                                        with open(full_path, "wb") as f:
                                            f.write(archivo_pdf.getbuffer())
                                        
                                        st.info(f"📎 Archivo guardado físicamente en: {file_name}")
                                    except Exception as e:
                                        st.error(f"❌ Error al guardar el archivo físico: {e}")
                                else:
                                    st.warning("⚠️ Registro creado sin archivo adjunto.")

            with c2:
                with st.expander("✂️ REGISTRO DE CIRUGÍAS", expanded=True):
                    with st.form("ciru_form", clear_on_submit=True):
                        tipo_c = st.selectbox("Clasificación de la Cirugía", get_clasificacion_cirugias())
                        fecha = st.date_input("Fecha", date.today())
                        proc = st.text_input("Procedimiento", placeholder="Ej: Plastia de LCA")
                        
                        if st.form_submit_button("Registrar Cirugía", use_container_width=True):
                            if save_surgery_record(player_id, fecha, tipo_c, proc):
                                st.success("✅ Cirugía registrada correctamente")
    else:
        st.error("Error al cargar la base de datos de jugadoras.")