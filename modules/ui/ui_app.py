import streamlit as st
import pandas as pd
from datetime import date, timedelta
from modules.app_config.styles import template_COLOR_NORMAL, template_COLOR_INVERTIDO, get_color_template
from modules.util.util import ordenar_df
from modules.i18n.i18n import t
from modules.ui import medical_ui, registros_ui

W_COLS = ["recuperacion", "energia", "sueno", "stress", "dolor"]

# ============================================================
# ⚙️ FUNCIONES BASE
# ============================================================

def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out

def compute_player_template_means(df_in_period_checkin: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve por nombre_jugadora:
      - prom_w_1_5: promedio (1-5) de las 5 variables template
      - dolor_mean: promedio de dolor (1-5)
      - en_riesgo: bool con la lógica consensuada (escala 1 = mejor, 5 = peor)
    """
    if df_in_period_checkin.empty:
        return pd.DataFrame(columns=["nombre_jugadora", "prom_w_1_5", "dolor_mean", "en_riesgo"])

    df = df_in_period_checkin.copy()
    df = _coerce_numeric(df, W_COLS)

    g = df.groupby("nombre_jugadora", as_index=False)[W_COLS].mean(numeric_only=True)
    g["prom_w_1_5"] = g[W_COLS].mean(axis=1, skipna=True)
    g["dolor_mean"] = g["dolor"]

    # 🔴 Riesgo con escala actual: 1 = mejor, 5 = peor
    g["en_riesgo"] = (g["prom_w_1_5"] > 3) | (g["dolor_mean"] > 3)
    return g[["nombre_jugadora", "prom_w_1_5", "dolor_mean", "en_riesgo"]]

# ============================================================
# 📅 GESTIÓN DE PERIODOS
# ============================================================

def get_default_period(df: pd.DataFrame) -> str:
    hoy = date.today()
    dias_disponibles = df["fecha_dia"].unique()
    if hoy in dias_disponibles:
        return "Hoy"
    elif (hoy - timedelta(days=1)) in dias_disponibles:
        return "Último día"
    elif any((hoy - timedelta(days=i)) in dias_disponibles for i in range(2, 8)):
        return "Semana"
    else:
        return "Mes"

def filter_df_by_period(df: pd.DataFrame, periodo: str):
    fecha_max = df["fecha_sesion"].max()
    if periodo == "Hoy":
        filtro = df["fecha_dia"] == date.today()
        texto = t("el día de hoy")
    elif periodo == "Último día":
        filtro = df["fecha_dia"] == fecha_max
        texto = t("el último día")
    elif periodo == "Semana":
        filtro = df["fecha_sesion"] >= (fecha_max - pd.Timedelta(days=7))
        texto = t("la última semana")
    else:
        filtro = df["fecha_sesion"] >= (fecha_max - pd.Timedelta(days=30))
        texto = t("el último mes")

    df_filtrado = df[filtro].copy()
    df_filtrado = df_filtrado.sort_values(by="fecha_sesion", ascending=False).reset_index(drop=True)
    if "id" in df_filtrado.columns:
        df_filtrado.drop(columns=["id"], inplace=True)
    return df_filtrado, texto

# ============================================================
# 📈 FUNCIONES AUXILIARES
# ============================================================

def calc_delta(values):
    if len(values) < 2 or values[-2] == 0:
        return 0
    return round(((values[-1] - values[-2]) / values[-2]) * 100, 1)

def calc_trend(df, by_col, target_col, agg="mean"):
    if agg == "sum":
        g = df.groupby(by_col)[target_col].sum().reset_index(name="valor")
    else:
        g = df.groupby(by_col)[target_col].mean().reset_index(name="valor")
    return g.sort_values(by_col)["valor"].tolist()

def calc_metric_block(df, periodo, var, agg="mean"):
    if periodo in ["Hoy", "Último día"]:
        valor = round(df[var].mean(), 1) if agg == "mean" else int(df[var].sum())
        chart, delta = [valor], 0
    elif periodo == "Semana":
        vals = calc_trend(df, "semana", var, agg)
        valor = round(vals[-1], 1) if vals else 0
        chart, delta = vals, calc_delta(vals)
    else:
        vals = calc_trend(df, "mes", var, agg)
        valor = round(vals[-1], 1) if vals else 0
        chart, delta = vals, calc_delta(vals)
    return valor, chart, delta

def calc_alertas(df_periodo: pd.DataFrame, df_completo: pd.DataFrame, periodo: str):
    if df_periodo.empty:
        return 0, 0, 0, [], 0

    if "tipo" in df_periodo.columns:
        df_in = df_periodo[df_periodo["tipo"].str.lower() == "checkin"].copy()
    else:
        df_in = pd.DataFrame()

    base_df = df_in if not df_in.empty else df_periodo.copy()
    try:
        riesgo_df = compute_player_template_means(base_df)
        if riesgo_df.empty or "en_riesgo" not in riesgo_df.columns:
            alertas_count = 0
            total_jugadoras = len(base_df["id_jugadora"].unique())
        else:
            alertas_count = int(riesgo_df["en_riesgo"].sum())
            total_jugadoras = int(riesgo_df.shape[0])
    except Exception as e:
        st.warning(f"No se pudo calcular el riesgo: {e}")
        alertas_count = 0
        total_jugadoras = len(base_df["id_jugadora"].unique())

    alertas_pct = round((alertas_count / total_jugadoras) * 100, 1) if total_jugadoras > 0 else 0
    return alertas_count, total_jugadoras, alertas_pct, [alertas_pct], 0

# ============================================================
# 💠 TARJETAS DE MÉTRICAS
# ============================================================

def render_metric_cards(template_prom, delta_template, chart_template, rpe_prom, delta_rpe, chart_rpe, ua_total,
                        delta_ua, chart_ua, alertas_count, total_jugadoras, alertas_pct, chart_alertas, delta_alertas, articulo):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(t("Bienestar promedio del grupo"), f"{template_prom if not pd.isna(template_prom) else 0}/25",
                  f"{delta_template:+.1f}%", chart_data=chart_template, chart_type="area", border=True,
                  help=f"{t('Promedio de bienestar global')} ({articulo}).")
    with col2:
        st.metric(t("Esfuerzo percibido promedio (RPE)"), f"{rpe_prom if not pd.isna(rpe_prom) else 0}",
                  f"{delta_rpe:+.1f}%", chart_data=chart_rpe, chart_type="line", border=True, delta_color="inverse")
    with col3:
        st.metric(t("Carga interna total (UA)"), ua_total, f"{delta_ua:+.1f}%", chart_data=chart_ua, chart_type="area", border=True)
    with col4:
        st.metric(t("Jugadoras en Zona Roja"), f"{alertas_count}/{total_jugadoras}", f"{delta_alertas:+.1f}%",
                  chart_data=chart_alertas, chart_type="bar", border=True, delta_color="inverse",
                  help=f"{alertas_count} {t('de')} {total_jugadoras} {t('jugadoras')} ({alertas_pct}%) "
                       f"{t('con bienestar promedio <15 o dolor >3')} ({articulo}).")

def mostrar_resumen_tecnico(template_prom: float, rpe_prom: float, ua_total: float, alertas_count: int, total_jugadoras: int):
    estado_bienestar = t("óptimo") if template_prom > 20 else t("moderado") if template_prom >= 15 else t("en fatiga")
    if pd.isna(rpe_prom) or rpe_prom == 0: nivel_rpe = t("sin datos")
    elif rpe_prom < 5: nivel_rpe = t("bajo")
    elif rpe_prom <= 7: nivel_rpe = t("moderado")
    else: nivel_rpe = t("alto")

    if alertas_count == 0: estado_alertas = t("sin jugadoras en zona roja")
    elif alertas_count == 1: estado_alertas = t("1 jugadora en seguimiento")
    else: estado_alertas = f"{alertas_count} {t('jugadoras en zona roja')}"

    st.markdown(f":material/description: **{t('Resumen técnico')}:** "
                f"{t('El grupo muestra un estado de bienestar')} **{estado_bienestar}** ({template_prom}/25) "
                f"{t('con un esfuerzo percibido')} **{nivel_rpe}** (RPE {rpe_prom}). "
                f"{t('La carga interna total es de')} **{ua_total} UA** {t('y actualmente hay')} **{estado_alertas}**, "
                f"{t('debido a que el promedio de bienestar x 5 es menor a 15 puntos')} {t('(escala 25)')}, "
                f"{t('indicando fatiga, sobrecarga o molestias significativas que aumentan el riesgo de lesión o bajo rendimiento')}.")

def show_interpretation(template_prom, rpe_prom, ua_total, alertas_count, alertas_pct, delta_ua, total_jugadoras):
    interpretacion_data = [
        {t("Métrica"): t("Índice de Bienestar Promedio"), t("Valor"): f"{template_prom if not pd.isna(template_prom) else 0}/25",
         t("Interpretación"): (t("🟢 Óptimo (>20)") if template_prom > 20 else t("🟡 Moderado (15-19)") if 15 <= template_prom <= 19 else t("🔴 Alerta (<15)"))},
        {t("Métrica"): t("RPE Promedio"), t("Valor"): f"{rpe_prom if not pd.isna(rpe_prom) else 0}",
         t("Interpretación"): (t("🟢 Controlado (<6)") if rpe_prom < 6 else t("🟡 Medio (6-7)") if 6 <= rpe_prom <= 7 else t("🔴 Alto (>7)"))},
        {t("Métrica"): t("Carga Total (UA)"), t("Valor"): f"{ua_total}",
         t("Interpretación"): (t("🟢 Estable") if abs(delta_ua) < 10 else t("🟡 Variación moderada") if 10 <= abs(delta_ua) <= 20 else t("🔴 Variación fuerte"))},
        {t("Métrica"): t("Jugadoras en Zona Roja"), t("Valor"): f"{alertas_count}/{total_jugadoras} ({alertas_pct}%)",
         t("Interpretación"): (t("🟢 Grupo estable") if alertas_pct == 0 else t("🟡 Seguimiento leve") if alertas_pct <= 15 else t("🔴 Riesgo elevado"))}
    ]
    with st.expander(t("Interpretación de las métricas")):
        st.dataframe(pd.DataFrame(interpretacion_data), hide_index=True)
        st.caption(t("🟢 / 🔴 Los colores en los gráficos muestran variaciones, en la tabla niveles fisiológicos."))

# ============================================================
# 📋 TABLA RESUMEN DEL PERIODO
# ============================================================

def generar_resumen_periodo(df: pd.DataFrame):
    df_periodo = df.copy()
    if df_periodo.empty:
        st.info("No hay registros disponibles en este periodo.")
        return

    cols_template = ["recuperacion", "energia", "sueno", "stress", "dolor"]
    for c in cols_template + ["rpe", "ua"]:
        if c in df_periodo.columns:
            df_periodo[c] = pd.to_numeric(df_periodo[c], errors="coerce")

    resumen = (df_periodo.groupby("nombre_jugadora", as_index=False).agg({
        "recuperacion": "mean", "energia": "mean", "sueno": "mean", "stress": "mean", "dolor": "mean", "rpe": "mean", "ua": "mean"
    }).rename(columns={"recuperacion": "Recuperación", "energia": "Energía", "sueno": "Sueño", "stress": "Estrés", "dolor": "Dolor", "rpe": "RPE_promedio", "ua": "UA_total"}))

    registros_por_jugadora = df_periodo.groupby("nombre_jugadora", as_index=False).agg(Registros_periodo=("fecha_sesion", "count"))
    dias_periodo = df_periodo["fecha_sesion"].nunique()
    registros_por_jugadora["Dias_periodo"] = dias_periodo
    resumen = resumen.merge(registros_por_jugadora, on="nombre_jugadora", how="left")
    resumen["Registros/Días"] = resumen["Registros_periodo"].astype(int).astype(str) + " / " + resumen["Dias_periodo"].astype(int).astype(str)
    
    col_reg = resumen.pop("Registros/Días")
    resumen.insert(1, "Registros/Días", col_reg)
    resumen.drop(columns=["Registros_periodo", "Dias_periodo"], inplace=True)
    resumen["Promedio_template"] = resumen[["Recuperación", "Energía", "Sueño", "Estrés", "Dolor"]].mean(axis=1, skipna=True)

    try:
        riesgo_df = compute_player_template_means(df_periodo)
        if "en_riesgo" in riesgo_df.columns:
            resumen = pd.merge(resumen, riesgo_df[["nombre_jugadora", "en_riesgo"]], on="nombre_jugadora", how="left")
            resumen["En_riesgo"] = resumen["en_riesgo"].fillna(False).apply(lambda x: "Sí" if x else "No")
            resumen.drop(columns=["en_riesgo"], inplace=True)
    except: resumen["En_riesgo"] = "No"

    resumen = resumen.fillna(0)
    
    # --- Estilos de Color ---
    def color_por_variable(col):
        if col.name not in ["Recuperación", "Energía", "Sueño", "Estrés", "Dolor"]: return [""] * len(col)
        return [f"background-color:{get_color_template(v, col.name)}; color:white; font-weight:bold;" for v in col]

    def color_promedios(col):
        return ["background-color:#27AE60; color:white;" if v < 3 else "background-color:#F1C40F;" if v == 3 else "background-color:#E74C3C; color:white;" for v in col]

    resumen = resumen.rename(columns={"nombre_jugadora": t("Jugadora"), "Registros/Días": t("Registros/Días"), "Recuperación": t("Recuperación"), "Energía": t("Energía"), "Sueño": t("Sueño"), "Estrés": t("Estrés"), "Dolor": t("Dolor"), "Promedio_template": t("Promedio template"), "RPE_promedio": t("RPE promedio"), "UA_total": t("UA total"), "En_riesgo": t("En riesgo")})
    
    styled = (resumen.style.apply(color_por_variable, subset=[t("Recuperación"), t("Energía"), t("Sueño"), t("Estrés"), t("Dolor")])
              .apply(color_promedios, subset=[t("Promedio template")])
              .format(precision=2, na_rep=""))
    st.dataframe(styled, hide_index=True)

# ============================================================
# 📋 GESTIÓN DE PENDIENTES
# ============================================================

def _filtrar_pendientes(df_periodo: pd.DataFrame, df_jugadoras: pd.DataFrame, tipo: str) -> pd.DataFrame:
    tipo = tipo.lower().strip()
    df_periodo = df_periodo.copy()
    df_periodo["tipo"] = df_periodo["tipo"].astype(str).str.lower()
    ids_checkin = df_periodo[df_periodo["tipo"] == "checkin"]["id_jugadora"].unique()
    ids_checkout = df_periodo[df_periodo["tipo"] == "checkout"]["id_jugadora"].unique()

    if tipo == "checkin":
        pendientes_ids = [jid for jid in df_jugadoras["id_jugadora"].unique() if jid not in ids_checkin and jid not in ids_checkout]
    else:
        pendientes_ids = [jid for jid in df_jugadoras["id_jugadora"].unique() if (jid in ids_checkin and jid not in ids_checkout) or (jid not in ids_checkin and jid not in ids_checkout)]

    pendientes = df_jugadoras[df_jugadoras["id_jugadora"].isin(pendientes_ids)].copy()
    pendientes = ordenar_df(pendientes, "nombre_jugadora")
    return pendientes[["id_jugadora", "nombre_jugadora", "posicion", "plantel"]]

def get_pendientes_check(df_periodo: pd.DataFrame, df_jugadoras: pd.DataFrame):
    if "id_jugadora" not in df_periodo.columns or "id_jugadora" not in df_jugadoras.columns:
        return pd.DataFrame(), pd.DataFrame()
    return _filtrar_pendientes(df_periodo, df_jugadoras, "checkin"), _filtrar_pendientes(df_periodo, df_jugadoras, "checkout")

def render_main_layout():
    with st.sidebar:
        st.image("assets/images/logo.png", width=150)
        st.title("DUX Medical System")
        st.write("---")
        st.markdown("### :material/apps: Seleccione Módulo")
        modulo_activo = st.selectbox("Módulos:", ["Módulo Médico Integral", "Otros módulos..."], label_visibility="collapsed")
        st.write("---")
        st.markdown("### :material/monitoring: Análisis y Estadísticas")
        menu_analisis = st.radio("Navegación:", ["Individual", "Grupal"], key="radio_analisis", label_visibility="collapsed")
        st.write("---")
        st.markdown("### :material/settings: Administración")
        menu_admin = st.radio("Admin:", ["Registros", "Developer"], key="radio_admin", label_visibility="collapsed")
        if st.button(":material/refresh: Limpiar cache & reiniciar"):
            st.cache_data.clear()
            st.rerun()
        st.write("---")

    if modulo_activo == "Módulo Médico Integral":
        if menu_admin == "Registros": registros_ui.render_registros_module()
        elif menu_analisis == "Individual": medical_ui.render_medical_module()
        else: medical_ui.render_medical_module()
    else:
        st.info("Seleccione el Módulo Médico Integral en la barra lateral para comenzar.")