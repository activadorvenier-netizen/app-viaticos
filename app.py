# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import sys

# Agregar la ruta del proyecto al path si es necesario
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
        # ============================================
        # LOGO DE LA EMPRESA - VERSIÓN CORREGIDA
        # ============================================
        # Buscar el logo en diferentes ubicaciones y formatos
        logo_paths = [
            "assets/logo.png",
            "assets/logo.PNG", 
            "assets/logo.jpg",
            "assets/logo.jpeg",
            "assets/logo.webp",
            "logo.png",
            "static/logo.png",
            "images/logo.png",
            "../assets/logo.png"  # En caso de que la app esté en subcarpeta
        ]
        
        logo_encontrado = None
        for path in logo_paths:
            # 🔴 CORREGIDO: Usar abspath para resolver rutas correctamente
            full_path = os.path.abspath(path)
            if os.path.exists(full_path):
                logo_encontrado = full_path
                break
        
        if logo_encontrado:
            # 🔴 CORREGIDO: Usar la ruta absoluta
            try:
                st.image(logo_encontrado, use_container_width=True)
            except Exception as e:
                st.image("https://img.icons8.com/color/96/000000/company.png", width=80)
                st.caption(f"⚠️ Error al cargar logo: {e}")
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
        
        # Mostrar información de la versión (opcional)
        st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
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