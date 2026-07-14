# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Importar módulos
from modules.config import MESES
from modules.data_manager import init_session_state, cargar_datos_iniciales, guardar_datos_actuales
from modules.dashboard import show_dashboard
from modules.load_data import show_load_visits
from modules.admin import show_admin

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Viáticos",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Función principal"""
    
    # Inicializar
    init_session_state()
    
    # Cargar datos automáticamente
    if st.session_state.data_base is None:
        with st.spinner("Cargando datos desde Google Sheets..."):
            if cargar_datos_iniciales():
                st.success("✅ Datos cargados")
            else:
                st.error("❌ Error al cargar datos. Verifica la conexión con Sheets.")
    
    # Sidebar - Navegación
    with st.sidebar:
        # 🔴 LOGO DE LA EMPRESA - ANCHO COMPLETO
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            # use_container_width=True hace que ocupe todo el ancho
            st.image(logo_path, use_container_width=True)
        else:
            # Fallback: ícono genérico
            st.image("https://img.icons8.com/color/96/000000/company.png", width=80)
            st.caption("💡 Coloca tu logo en: assets/logo.png")
        
        st.markdown("### 💰 Viáticos")
        st.markdown("---")
        
        # Navegación
        page = st.radio(
            "📋 Menú",
            ["📊 Dashboard", "✏️ Carga de Datos", "⚙️ Administración"],
            index=0
        )
        
        st.markdown("---")
        
        # Firma
        st.markdown(
            """
            <div style="text-align: center; color: #666; font-size: 0.8em; padding-top: 20px;">
                <hr style="border: none; border-top: 1px solid #ddd; margin: 10px 0;">
                <span>Desarrollado por</span><br>
                <strong>Pato Frangi</strong>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Mostrar página seleccionada
    if page == "📊 Dashboard":
        show_dashboard()
    elif page == "✏️ Carga de Datos":
        show_load_visits()
    elif page == "⚙️ Administración":
        show_admin()

if __name__ == "__main__":
    main()