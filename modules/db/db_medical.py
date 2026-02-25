import pandas as pd

# ==========================================
# CATÁLOGOS Y TABLAS MAESTRAS (Punto 14)
# ==========================================
CAT_ESTADOS = ["Apto", "Apto con limitaciones", "No Apto", "En observación"]
CAT_TIPOS_PRUEBA = ["Analítica Sangre", "Antropometría", "Cardiología", "Podología", "Psicología"]
CAT_SANGRE = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

# ==========================================
# FUNCIONES DE CONSULTA (MOCK DATA)
# ==========================================

def get_medical_history_mock(player_id):
    """
    Simula la Entidad Ficha Médica Permanente (Punto 13).
    Relaciona datos fijos con el ID de la jugadora.
    """
    data = {
        "Jugadora A": {
            "sangre": "A+", 
            "alergias": "Penicilina, Polen", 
            "cirugias": "Ligamento Cruzado Anterior (2022)"
        },
        "Jugadora B": {
            "sangre": "O-", 
            "alergias": "Ninguna conocida", 
            "cirugias": "Artroscopia rodilla izquierda (2023)"
        }
    }
    return data.get(player_id, {"sangre": "N/A", "alergias": "N/A", "cirugias": "N/A"})

def get_evaluations_mock(player_id):
    """
    Simula la Entidad Evaluaciones (Relación 1 a Muchos).
    Muestra el histórico de pruebas de la jugadora.
    """
    evals = [
        {"Fecha": "2026-01-10", "Tipo": "Analítica Sangre", "Resultado": "Óptimo", "Hierro": 45},
        {"Fecha": "2026-02-15", "Tipo": "Antropometría", "Resultado": "Apto", "Hierro": 38}
    ]
    return pd.DataFrame(evals)