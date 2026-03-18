import streamlit as st
from modules.ui import ui_app

# 1. Configuración de página global
st.set_page_config(
    page_title="DUX Medical System", 
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Inyección del layout maestro
# Asumo que ui_app.py contiene la función que gestiona toda la navegación
# y los estilos visuales que perdiste.
def main():
    # Si ui_app tiene una función para renderizar todo el layout, la llamamos aquí:
    if hasattr(ui_app, 'render_main_layout'):
        ui_app.render_main_layout()
    else:
        # Fallback por si la función tiene otro nombre (ej. main o run)
        st.error("No se encontró la función 'render_main_layout' en ui_app.py")
        st.write("Verifica el nombre de la función principal en modules/ui/ui_app.py")

if __name__ == "__main__":
    main()
