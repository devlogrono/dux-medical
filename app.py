import streamlit as st

# --- NUEVO IMPORT PARA EL MÓDULO MÉDICO (Punto de Integración) ---
import modules.ui.medical_ui as medical_ui

from modules.db.db_absences import load_active_absences_db
from modules.db.db_competitions import load_competitions_db
from modules.db.db_players import load_players_db
from modules.db.db_records import get_records_db
from modules.util.util import clean_df, data_format
from modules.ui.ui_app import (
    get_default_period,
    filter_df_by_period,
    calc_metric_block,
    calc_alertas,
    render_metric_cards,
    generar_resumen_periodo,
    show_interpretation,
    mostrar_resumen_tecnico,
    get_pendientes_check
)

from modules.i18n.i18n import t
import modules.app_config.config as config
config.init_config()

# ============================================================
# 🏥 MENU DE NAVEGACIÓN (Estrategia Profesional)
# ============================================================
# Aquí creamos el menú para que el usuario pueda elegir entre 
# el Resumen actual o el nuevo Módulo Médico.
# Esto cumple con el objetivo de centralizar todo en un solo entorno[cite: 12].

opcion_menu = st.sidebar.selectbox(
    t("Seleccione Módulo"),
    [t("Resumen General"), t("Módulo Médico Integral")]
)

if opcion_menu == t("Módulo Médico Integral"):
    # Si elige médico, llamamos a la pantalla que creamos antes
    medical_ui.render_medical_module()
    st.stop() # Detenemos el resto del código para que no se mezcle

# ============================================================
# 📊 CÓDIGO ORIGINAL (Resumen de 1er Equipo)
# ============================================================
st.header(t("Resumen de :red[1er Equipo]"), divider="red")

df = get_records_db()

if df.empty:
    st.warning(t("No hay registros disponibles."))
    st.stop()

df = data_format(df)
jug_df = load_players_db()
comp_df = load_competitions_db()
ausencias_df = load_active_absences_db()

# ... (El resto de tu código original continúa exactamente igual aquí abajo)
