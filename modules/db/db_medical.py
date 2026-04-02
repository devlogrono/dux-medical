import streamlit as st
import pandas as pd
from modules.db.db_connection import get_connection 
from modules.db.db_players import load_players_db

# --- FUNCIONES DE LECTURA ---

def get_cat_estados_aptitud():
    return ["Apto", "Apto con Limitaciones", "No Apto", "En Observación"]

def get_clasificacion_cirugias():
    return ["Traumatológica (MI)", "Traumatológica (MS)", "General", "Ginecológica"]

def get_tipos_evaluacion():
    return ["Analítica", "Nutrición", "Cardiología", "Ginecología", "Odontología"]

# --- FUNCIONES DE ESCRITURA (Sincronizadas con el SQL de José) ---

def save_medical_evaluation(player_id, eval_type, status, notes):
    try:
        conn = get_connection()
        if conn is None: return False
        
        cursor = conn.cursor()
        # Ajustamos los nombres de columnas al SQL enviado a José
        query = """
            INSERT INTO medical_evaluations (id_jugadora, tipo_evaluacion, estado_aptitud, observaciones, fecha_evaluacion)
            VALUES (%s, %s, %s, %s, CURDATE())
        """
        cursor.execute(query, (player_id, eval_type, status, notes))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error al guardar evaluación en AWS: {e}")
        return False

def save_surgery_record(player_id, surgery_date, classification, procedure_name):
    try:
        conn = get_connection()
        if conn is None: return False
        
        cursor = conn.cursor()
        # Ajustamos los nombres de columnas al SQL enviado a José
        query = """
            INSERT INTO surgery_records (id_jugadora, fecha_cirugia, clasificacion, procedimiento)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (player_id, surgery_date, classification, procedure_name))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error al guardar cirugía en AWS: {e}")
        return False