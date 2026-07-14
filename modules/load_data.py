# modules/load_data.py
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.data_manager import (
    get_supervisores, get_promotores, get_localidades, get_tabla_km,
    get_visits_by_supervisor_mes, guardar_datos_actuales
)
from modules.config import MESES

def show_load_visits():
    """Panel de Carga de Visitas"""
    st.markdown("## ✏️ Carga de Datos")
    
    # ============================================
    # VERIFICAR QUE HAY DATOS CARGADOS
    # ============================================
    if not st.session_state.data_base:
        st.warning("⚠️ No hay datos cargados. Ve a la barra lateral y haz clic en 'Cargar Datos'")
        return
    
    # ============================================
    # 1. SELECCIÓN DE MES
    # ============================================
    mes_carga = st.selectbox(
        "📅 Seleccionar Mes",
        MESES,
        index=datetime.now().month - 1,
        key="load_mes"
    )
    
    # ============================================
    # 2. SELECCIÓN DE SUPERVISOR Y KM SUPERVISOR
    # ============================================
    supervisores_dict = get_supervisores()
    supervisores_list = list(supervisores_dict.keys()) if supervisores_dict else []
    
    if not supervisores_list:
        st.warning("⚠️ No se encontraron supervisores en Tabla KM")
        
        tabla_km = get_tabla_km()
        if not tabla_km.empty:
            with st.expander("🔍 Ver datos de Tabla KM"):
                st.write("Columnas disponibles:", tabla_km.columns.tolist())
                st.dataframe(tabla_km.head(10))
        
        if st.button("🔄 Recargar datos", use_container_width=True):
            from modules.data_manager import cargar_datos_iniciales
            with st.spinner("Recargando datos..."):
                if cargar_datos_iniciales():
                    st.success("✅ Datos recargados")
                    st.rerun()
                else:
                    st.error("❌ Error al recargar")
        return
    
    opciones_supervisor = [""] + supervisores_list
    
    col1, col2 = st.columns(2)
    
    with col1:
        supervisor = st.selectbox(
            "👔 Seleccionar Supervisor",
            opciones_supervisor,
            index=0,
            key="load_supervisor"
        )
    
    with col2:
        km_supervisor = st.number_input(
            "📏 KM del Supervisor",
            min_value=0,
            value=0,
            step=1,
            help="Kilómetros que realizó el supervisor en el mes",
            key="km_supervisor_input"
        )
    
    # ============================================
    # 3. MOSTRAR TABLA DE PROMOTORES CON LOCALIDADES
    # ============================================
    if not supervisor:
        st.info("👈 Selecciona un supervisor para comenzar")
        return
    
    tabla_km = get_tabla_km()
    if tabla_km.empty:
        st.warning("No hay datos en Tabla KM")
        return
    
    col_supervisor = None
    for col in tabla_km.columns:
        if col.upper() == 'SUPERVISOR':
            col_supervisor = col
            break
    
    if not col_supervisor:
        st.warning("No se encontró columna 'Supervisor' en Tabla KM")
        return
    
    df_supervisor = tabla_km[tabla_km[col_supervisor] == supervisor]
    
    if df_supervisor.empty:
        st.warning(f"No hay localidades asignadas a {supervisor}")
        return
    
    col_promotor = None
    for col in df_supervisor.columns:
        if col.upper() == 'PROMOTOR':
            col_promotor = col
            break
    
    if not col_promotor:
        st.warning("No se encontró columna 'Promotor' en Tabla KM")
        return
    
    col_localidad = None
    for col in df_supervisor.columns:
        if col.upper() == 'LOCALIDAD':
            col_localidad = col
            break
    
    if not col_localidad:
        st.warning("No se encontró columna 'Localidad' en Tabla KM")
        return
    
    st.markdown(f"### 📋 Carga para **{supervisor}** - **{mes_carga}**")
    
    # ============================================
    # 4. TABLA EDITABLE
    # ============================================
    # Obtener visitas existentes para este supervisor y mes
    visits_existentes = get_visits_by_supervisor_mes(supervisor, mes_carga)
    
    # Filtrar para excluir la fila de SUPERVISOR
    if not visits_existentes.empty:
        visits_existentes = visits_existentes[visits_existentes['Promotor'] != 'SUPERVISOR']
    
    visit_data = []
    
    for _, row in df_supervisor.iterrows():
        promotor = row[col_promotor]
        localidad = row[col_localidad]
        
        if not visits_existentes.empty and 'Promotor' in visits_existentes.columns and 'Localidad' in visits_existentes.columns:
            existente = visits_existentes[
                (visits_existentes['Promotor'] == promotor) & 
                (visits_existentes['Localidad'] == localidad)
            ]
        else:
            existente = pd.DataFrame()
        
        if not existente.empty:
            for _, row_existente in existente.iterrows():
                visit_data.append({
                    'Promotor': promotor,
                    'Localidad': localidad,
                    'Veces Moto': int(row_existente['Veces Moto']) if 'Veces Moto' in row_existente and pd.notna(row_existente['Veces Moto']) else 0,
                    'Veces Auto': int(row_existente['Veces Auto']) if 'Veces Auto' in row_existente and pd.notna(row_existente['Veces Auto']) else 0,
                    'Peajes': int(row_existente['Peajes']) if 'Peajes' in row_existente and pd.notna(row_existente['Peajes']) else 0,
                    'KM Extras': int(row_existente['KM Extras']) if 'KM Extras' in row_existente and pd.notna(row_existente['KM Extras']) else 0
                })
        else:
            visit_data.append({
                'Promotor': promotor,
                'Localidad': localidad,
                'Veces Moto': 0,
                'Veces Auto': 0,
                'Peajes': 0,
                'KM Extras': 0
            })
    
    df_editable = pd.DataFrame(visit_data)
    df_editable = df_editable.sort_values(by=['Promotor', 'Localidad']).reset_index(drop=True)
    
    st.caption(f"📌 {len(df_editable)} localidades asignadas a {len(df_supervisor[col_promotor].unique())} promotores")
    
    edited_df = st.data_editor(
        df_editable,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "Promotor": st.column_config.TextColumn("Promotor", disabled=True),
            "Localidad": st.column_config.TextColumn("Localidad", disabled=True),
            "Veces Moto": st.column_config.NumberColumn("Veces en Moto", min_value=0, max_value=50, step=1),
            "Veces Auto": st.column_config.NumberColumn("Veces en Auto", min_value=0, max_value=50, step=1),
            "Peajes": st.column_config.NumberColumn("Peajes ($)", min_value=0, step=100),
            "KM Extras": st.column_config.NumberColumn("KM Extras", min_value=0, step=1)
        },
        hide_index=True
    )
    
    # ============================================
    # 5. BOTÓN DE GUARDADO
    # ============================================
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("💾 Guardar", use_container_width=True, type="primary"):
            
            # 🔴 CORREGIDO: Eliminar SOLO los datos de este supervisor y mes (no todos los del promotor)
            st.session_state.visits = st.session_state.visits[
                ~((st.session_state.visits['Supervisor'] == supervisor) & 
                  (st.session_state.visits['Mes'] == mes_carga) &
                  (st.session_state.visits['Promotor'] != 'SUPERVISOR'))
            ]
            
            # Eliminar fila de KM del supervisor si existe
            st.session_state.visits = st.session_state.visits[
                ~((st.session_state.visits['Supervisor'] == supervisor) & 
                  (st.session_state.visits['Mes'] == mes_carga) &
                  (st.session_state.visits['Promotor'] == 'SUPERVISOR'))
            ]
            
            nuevos = []
            fecha_actual = datetime.now().strftime('%Y-%m-%d')
            
            for _, row in edited_df.iterrows():
                nuevos.append({
                    'Mes': mes_carga,
                    'Promotor': row['Promotor'],
                    'Localidad': row['Localidad'],
                    'Veces Moto': int(row['Veces Moto']),
                    'Veces Auto': int(row['Veces Auto']),
                    'Peajes': int(row['Peajes']) if pd.notna(row['Peajes']) else 0,
                    'KM Extras': int(row['KM Extras']) if pd.notna(row['KM Extras']) else 0,
                    'Supervisor': supervisor,
                    'KM Supervisor': 0,
                    'Fecha': fecha_actual
                })
            
            # Una sola fila para los KM del Supervisor
            if km_supervisor > 0:
                nuevos.append({
                    'Mes': mes_carga,
                    'Promotor': 'SUPERVISOR',
                    'Localidad': '',
                    'Veces Moto': 0,
                    'Veces Auto': 0,
                    'Peajes': 0,
                    'KM Extras': 0,
                    'Supervisor': supervisor,
                    'KM Supervisor': int(km_supervisor),
                    'Fecha': fecha_actual
                })
            
            if nuevos:
                df_nuevos = pd.DataFrame(nuevos)
                
                columnas_requeridas = ['Mes', 'Promotor', 'Localidad', 'Veces Moto', 
                                      'Veces Auto', 'Peajes', 'KM Extras', 'Supervisor', 
                                      'KM Supervisor', 'Fecha']
                for col in columnas_requeridas:
                    if col not in df_nuevos.columns:
                        df_nuevos[col] = ''
                
                st.session_state.visits = pd.concat(
                    [st.session_state.visits, df_nuevos],
                    ignore_index=True
                )
                
                success, msg = guardar_datos_actuales()
                if success:
                    st.success(f"✅ {len(nuevos)} registros guardados para {mes_carga} - {supervisor}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ Error al guardar: {msg}")
            else:
                st.warning("No hay datos para guardar")
    
    with col2:
        if st.button("🗑️ Limpiar Mes", use_container_width=True):
            st.session_state.visits = st.session_state.visits[
                ~((st.session_state.visits['Supervisor'] == supervisor) & 
                  (st.session_state.visits['Mes'] == mes_carga))
            ]
            guardar_datos_actuales()
            st.success(f"✅ Datos de {mes_carga} - {supervisor} eliminados")
            st.rerun()
    
    # ============================================
    # 6. RESUMEN
    # ============================================
    st.divider()
    st.markdown("### 📊 Resumen de la Carga")
    
    total_moto = edited_df['Veces Moto'].sum()
    total_auto = edited_df['Veces Auto'].sum()
    total_peajes = edited_df['Peajes'].sum()
    total_km_extras = edited_df['KM Extras'].sum()
    filas_validas = len(edited_df[
        (edited_df['Veces Moto'] > 0) | 
        (edited_df['Veces Auto'] > 0) | 
        (edited_df['KM Extras'] > 0)
    ])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Localidades", len(edited_df))
    with col2:
        st.metric("Con Datos", filas_validas)
    with col3:
        st.metric("Total Moto", total_moto)
    with col4:
        st.metric("Total Auto", total_auto)
    with col5:
        st.metric("KM Extras", total_km_extras)
    
    st.caption(f"💰 Total Peajes: ${total_peajes:,.0f}")