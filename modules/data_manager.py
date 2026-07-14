# modules/data_manager.py
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.config import BASE_VALUES, VISITS_COLUMNS, MESES
from modules.sheets import (
    cargar_datos_base, cargar_visitas_guardadas, guardar_visitas_en_sheets,
    guardar_ajuste_en_sheets, cargar_ajuste_por_mes, cargar_todos_los_ajustes
)

def init_session_state():
    """Inicializa las variables de sesión"""
    if 'data_base' not in st.session_state:
        st.session_state.data_base = None
    
    if 'visits' not in st.session_state:
        st.session_state.visits = pd.DataFrame(columns=VISITS_COLUMNS)
    
    if 'km_moto' not in st.session_state:
        st.session_state.km_moto = BASE_VALUES['km_moto']
    
    if 'km_auto' not in st.session_state:
        st.session_state.km_auto = BASE_VALUES['km_auto']
    
    if 'km_supervisor' not in st.session_state:
        st.session_state.km_supervisor = BASE_VALUES['km_supervisor']
    
    if 'km_supervisor_extra' not in st.session_state:
        st.session_state.km_supervisor_extra = {}
    
    if 'last_update' not in st.session_state:
        st.session_state.last_update = datetime.now().strftime('%d/%m/%Y %H:%M')
    
    # Variables para ajustes
    if 'ajuste_actual' not in st.session_state:
        st.session_state.ajuste_actual = 0
    if 'ajustes_data' not in st.session_state:
        st.session_state.ajustes_data = pd.DataFrame()

def cargar_datos_iniciales():
    """Carga datos base y visitas guardadas al iniciar"""
    try:
        data, msg = cargar_datos_base()
        if data:
            st.session_state.data_base = data
            
            visitas_df = data.get('visitas_guardadas', pd.DataFrame())
            if not visitas_df.empty:
                st.session_state.visits = visitas_df
            
            # Cargar ajustes
            ajustes_df = data.get('ajustes', pd.DataFrame())
            if not ajustes_df.empty:
                st.session_state.ajustes_data = ajustes_df
                
                # Aplicar ajuste del mes actual
                mes_actual = MESES[datetime.now().month - 1]
                ajuste_mes = ajustes_df[ajustes_df['Mes'] == mes_actual]
                if not ajuste_mes.empty:
                    st.session_state.km_moto = float(ajuste_mes['KM Moto'].iloc[0])
                    st.session_state.km_auto = float(ajuste_mes['KM Auto'].iloc[0])
                    st.session_state.km_supervisor = float(ajuste_mes['KM Supervisor'].iloc[0])
                    st.session_state.ajuste_actual = float(ajuste_mes['% Ajuste'].iloc[0])
            
            return True
        else:
            st.error(f"Error al cargar datos: {msg}")
            return False
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return False

def guardar_datos_actuales():
    """Guarda los datos actuales en Sheets"""
    try:
        success, msg = guardar_visitas_en_sheets(st.session_state.visits)
        return success, msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def guardar_ajuste(mes, porcentaje):
    """Guarda un ajuste para un mes específico y actualiza los valores"""
    try:
        # Calcular nuevos valores basados en los valores BASE
        km_moto = BASE_VALUES['km_moto'] * (1 + porcentaje / 100)
        km_auto = BASE_VALUES['km_auto'] * (1 + porcentaje / 100)
        km_supervisor = BASE_VALUES['km_supervisor'] * (1 + porcentaje / 100)
        
        # Guardar en Sheets
        success, msg = guardar_ajuste_en_sheets(mes, porcentaje, km_moto, km_auto, km_supervisor)
        
        if success:
            # Actualizar session_state SOLO si es el mes actual
            mes_actual = MESES[datetime.now().month - 1]
            if mes == mes_actual:
                st.session_state.km_moto = km_moto
                st.session_state.km_auto = km_auto
                st.session_state.km_supervisor = km_supervisor
                st.session_state.ajuste_actual = porcentaje
                st.session_state.last_update = datetime.now().strftime('%d/%m/%Y %H:%M')
            
            # Actualizar datos de ajustes
            ajustes_df, _ = cargar_todos_los_ajustes()
            if not ajustes_df.empty:
                st.session_state.ajustes_data = ajustes_df
        
        return success, msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_supervisores():
    """Obtiene la lista de supervisores desde Tabla KM"""
    if st.session_state.data_base:
        return st.session_state.data_base.get('supervisores', {})
    return {}

def get_promotores(supervisor):
    """Obtiene los promotores de un supervisor"""
    supervisores = get_supervisores()
    return supervisores.get(supervisor, [])

def get_localidades():
    """Obtiene la lista de localidades desde Tabla KM"""
    if st.session_state.data_base:
        tabla_km = st.session_state.data_base.get('tabla_km', pd.DataFrame())
        if not tabla_km.empty:
            for col in tabla_km.columns:
                if col.upper() == 'LOCALIDAD':
                    return tabla_km[col].tolist()
        return []
    return []

def get_tabla_km():
    """Obtiene la tabla de kilómetros"""
    if st.session_state.data_base:
        return st.session_state.data_base.get('tabla_km', pd.DataFrame())
    return pd.DataFrame()

def get_km_total_localidad(localidad, promotor=None):
    """Obtiene el TOTAL KM de una localidad para un promotor específico"""
    tabla_km = get_tabla_km()
    if tabla_km.empty:
        return 0
    
    col_localidad = None
    col_promotor = None
    for col in tabla_km.columns:
        if col.upper() == 'LOCALIDAD':
            col_localidad = col
        elif col.upper() == 'PROMOTOR':
            col_promotor = col
    
    if not col_localidad:
        return 0
    
    df_filtrado = tabla_km[tabla_km[col_localidad].astype(str).str.upper() == localidad.upper()]
    
    if promotor and col_promotor:
        df_filtrado = df_filtrado[df_filtrado[col_promotor].astype(str).str.upper() == promotor.upper()]
    
    if df_filtrado.empty:
        return 0
    
    for col in df_filtrado.columns:
        if col.upper() == 'TOTAL KM':
            valor = df_filtrado[col].iloc[0]
            return float(valor) if pd.notna(valor) else 0
    
    km = 0
    km_dentro = 0
    
    for col in df_filtrado.columns:
        if col.upper() == 'KM':
            km = float(df_filtrado[col].iloc[0]) if pd.notna(df_filtrado[col].iloc[0]) else 0
        elif col.upper() == 'KM DENTRO':
            km_dentro = float(df_filtrado[col].iloc[0]) if pd.notna(df_filtrado[col].iloc[0]) else 0
    
    return km + km_dentro

def get_km_solo_localidad(localidad, promotor=None):
    """Obtiene solo el KM de una localidad para un promotor específico"""
    tabla_km = get_tabla_km()
    if tabla_km.empty:
        return 0
    
    col_localidad = None
    col_promotor = None
    for col in tabla_km.columns:
        if col.upper() == 'LOCALIDAD':
            col_localidad = col
        elif col.upper() == 'PROMOTOR':
            col_promotor = col
    
    if not col_localidad:
        return 0
    
    df_filtrado = tabla_km[tabla_km[col_localidad].astype(str).str.upper() == localidad.upper()]
    
    if promotor and col_promotor:
        df_filtrado = df_filtrado[df_filtrado[col_promotor].astype(str).str.upper() == promotor.upper()]
    
    if df_filtrado.empty:
        return 0
    
    for col in df_filtrado.columns:
        if col.upper() == 'KM':
            valor = df_filtrado[col].iloc[0]
            return float(valor) if pd.notna(valor) else 0
    
    return 0

def get_km_dentro_localidad(localidad, promotor=None):
    """Obtiene solo el KM DENTRO de una localidad para un promotor específico"""
    tabla_km = get_tabla_km()
    if tabla_km.empty:
        return 0
    
    col_localidad = None
    col_promotor = None
    for col in tabla_km.columns:
        if col.upper() == 'LOCALIDAD':
            col_localidad = col
        elif col.upper() == 'PROMOTOR':
            col_promotor = col
    
    if not col_localidad:
        return 0
    
    df_filtrado = tabla_km[tabla_km[col_localidad].astype(str).str.upper() == localidad.upper()]
    
    if promotor and col_promotor:
        df_filtrado = df_filtrado[df_filtrado[col_promotor].astype(str).str.upper() == promotor.upper()]
    
    if df_filtrado.empty:
        return 0
    
    for col in df_filtrado.columns:
        if col.upper() == 'KM DENTRO':
            valor = df_filtrado[col].iloc[0]
            return float(valor) if pd.notna(valor) else 0
    
    return 0

def get_visits_by_supervisor_mes(supervisor, mes):
    """Obtiene las visitas de un supervisor en un mes específico"""
    if st.session_state.visits.empty:
        return pd.DataFrame()
    
    if 'Supervisor' not in st.session_state.visits.columns:
        return pd.DataFrame()
    
    if 'Mes' not in st.session_state.visits.columns:
        return pd.DataFrame()
    
    if supervisor is None:
        return st.session_state.visits[st.session_state.visits['Mes'] == mes]
    
    return st.session_state.visits[
        (st.session_state.visits['Supervisor'] == supervisor) & 
        (st.session_state.visits['Mes'] == mes)
    ]

def update_visits(visits_df):
    """Actualiza el DataFrame de visitas"""
    st.session_state.visits = visits_df
    success, msg = guardar_datos_actuales()
    return success, msg