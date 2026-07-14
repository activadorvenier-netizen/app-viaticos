# modules/admin.py
import streamlit as st
import pandas as pd
from modules.data_manager import (
    get_supervisores, get_promotores, get_tabla_km,
    guardar_datos_actuales, cargar_datos_iniciales
)
from modules.sheets import guardar_visitas_en_sheets
from modules.config import VISITS_COLUMNS
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from modules.config import SHEET_URL, CREDENTIALS_PATHS

def get_sheets_client():
    """Conecta a Google Sheets para operaciones de escritura"""
    try:
        creds_path = None
        for path in CREDENTIALS_PATHS:
            if os.path.exists(path):
                creds_path = path
                break
        
        if not creds_path:
            return None, "No se encontró credentials.json"
        
        scope = ['https://spreadsheets.google.com/feeds', 
                 'https://www.googleapis.com/auth/drive']
        
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        return client, "Conectado"
    except Exception as e:
        return None, f"Error: {str(e)}"

def guardar_tabla_km_en_sheets(df):
    """Guarda la tabla KM completa en Google Sheets"""
    try:
        client, msg = get_sheets_client()
        if not client:
            return False, msg
        
        sheet = client.open_by_url(SHEET_URL)
        
        try:
            ws = sheet.worksheet("Tabla KM")
            ws.clear()
        except:
            ws = sheet.add_worksheet("Tabla KM", rows=1000, cols=20)
        
        columnas = ['Localidad', 'KM', 'KM DENTRO', 'TOTAL KM', 'Promotor', 'Supervisor']
        
        for col in columnas:
            if col not in df.columns:
                df[col] = ''
        
        if 'TOTAL KM' not in df.columns:
            df['TOTAL KM'] = df['KM'] + df['KM DENTRO']
        
        datos = [columnas] + df[columnas].values.tolist()
        ws.update(datos)
        
        return True, "✅ Tabla KM guardada correctamente"
    except Exception as e:
        return False, f"Error al guardar: {str(e)}"

def show_admin():
    """Panel de Administración"""
    st.markdown("## ⚙️ Administración")
    
    if not st.session_state.data_base:
        st.warning("Cargando datos...")
        return
    
    tabs = st.tabs(["🏷️ Supervisores", "👥 Promotores", "📍 Localidades", "🗑️ Eliminar Movimientos"])
    
    with tabs[0]:
        show_supervisores_admin()
    
    with tabs[1]:
        show_promotores_admin()
    
    with tabs[2]:
        show_localidades_admin()
    
    with tabs[3]:
        show_eliminar_movimientos()

# ============================================
# 1. ADMINISTRACIÓN DE SUPERVISORES
# ============================================
def show_supervisores_admin():
    """Administración de supervisores"""
    st.markdown("### Gestión de Supervisores")
    st.caption("Agrega, edita o elimina supervisores. Los cambios se guardan en la hoja Tabla KM.")
    
    supervisores_dict = get_supervisores()
    supervisores_list = list(supervisores_dict.keys()) if supervisores_dict else []
    
    if supervisores_list:
        df_supervisores = pd.DataFrame({
            'Supervisor': supervisores_list,
            'Promotores Asignados': [len(supervisores_dict[s]) for s in supervisores_list]
        })
        st.dataframe(df_supervisores, use_container_width=True, hide_index=True)
    else:
        st.info("No hay supervisores cargados")
    
    st.divider()
    
    # Agregar
    with st.expander("➕ Agregar Nuevo Supervisor", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            nuevo_supervisor = st.text_input("Nombre del Supervisor", key="new_supervisor")
        with col2:
            st.write("")
            st.write("")
            if st.button("Agregar Supervisor", use_container_width=True):
                if nuevo_supervisor and nuevo_supervisor.strip():
                    if nuevo_supervisor not in supervisores_list:
                        success, msg = agregar_supervisor_a_tabla_km(nuevo_supervisor)
                        if success:
                            st.success(f"✅ Supervisor {nuevo_supervisor} agregado")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {msg}")
                    else:
                        st.error("El supervisor ya existe")
                else:
                    st.error("Ingresa un nombre válido")
    
    # Editar
    if supervisores_list:
        with st.expander("✏️ Editar Supervisor", expanded=False):
            supervisor_a_editar = st.selectbox(
                "Seleccionar Supervisor a editar",
                supervisores_list,
                key="edit_supervisor"
            )
            
            nuevo_nombre = st.text_input(
                "Nuevo nombre del Supervisor",
                value=supervisor_a_editar if supervisor_a_editar else "",
                key="edit_supervisor_nombre"
            )
            
            if st.button("Guardar Cambios", use_container_width=True, type="primary"):
                if nuevo_nombre and nuevo_nombre.strip():
                    if nuevo_nombre != supervisor_a_editar:
                        if nuevo_nombre not in supervisores_list:
                            success, msg = editar_supervisor_en_tabla_km(supervisor_a_editar, nuevo_nombre)
                            if success:
                                st.success(f"✅ Supervisor {supervisor_a_editar} → {nuevo_nombre}")
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {msg}")
                        else:
                            st.error("El nuevo nombre ya existe")
                    else:
                        st.warning("El nombre no ha cambiado")
                else:
                    st.error("Ingresa un nombre válido")
    
    # Eliminar
    if supervisores_list:
        with st.expander("🗑️ Eliminar Supervisor", expanded=False):
            supervisor_a_eliminar = st.selectbox(
                "Seleccionar Supervisor a eliminar",
                supervisores_list,
                key="delete_supervisor"
            )
            
            st.warning(f"⚠️ Esto eliminará al supervisor **{supervisor_a_eliminar}** y todos sus datos asociados.")
            
            if st.button("Eliminar Supervisor", use_container_width=True, type="secondary"):
                success, msg = eliminar_supervisor_de_tabla_km(supervisor_a_eliminar)
                if success:
                    st.success(f"✅ Supervisor {supervisor_a_eliminar} eliminado")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {msg}")

def agregar_supervisor_a_tabla_km(nuevo_supervisor):
    """Agrega un nuevo supervisor a la tabla KM"""
    try:
        tabla_km = get_tabla_km()
        st.session_state.data_base['supervisores'][nuevo_supervisor] = []
        success, msg = guardar_tabla_km_en_sheets(tabla_km)
        if success:
            cargar_datos_iniciales()
            return True, "Supervisor agregado"
        return False, msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def editar_supervisor_en_tabla_km(supervisor_actual, nuevo_nombre):
    """Edita un supervisor en la tabla KM"""
    try:
        tabla_km = get_tabla_km()
        
        if 'Supervisor' in tabla_km.columns:
            tabla_km.loc[tabla_km['Supervisor'] == supervisor_actual, 'Supervisor'] = nuevo_nombre
        
        if supervisor_actual in st.session_state.data_base['supervisores']:
            st.session_state.data_base['supervisores'][nuevo_nombre] = st.session_state.data_base['supervisores'].pop(supervisor_actual)
        
        success, msg = guardar_tabla_km_en_sheets(tabla_km)
        if success:
            cargar_datos_iniciales()
            return True, "Supervisor editado"
        return False, msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def eliminar_supervisor_de_tabla_km(supervisor):
    """Elimina un supervisor de la tabla KM"""
    try:
        tabla_km = get_tabla_km()
        
        if 'Supervisor' in tabla_km.columns:
            tabla_km = tabla_km[tabla_km['Supervisor'] != supervisor]
        
        if supervisor in st.session_state.data_base['supervisores']:
            del st.session_state.data_base['supervisores'][supervisor]
        
        success, msg = guardar_tabla_km_en_sheets(tabla_km)
        if success:
            cargar_datos_iniciales()
            return True, "Supervisor eliminado"
        return False, msg
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============================================
# 2. ADMINISTRACIÓN DE PROMOTORES
# ============================================
def show_promotores_admin():
    """Administración de promotores"""
    st.markdown("### Gestión de Promotores")
    st.caption("Agrega, edita o elimina promotores. Los cambios se guardan en la hoja Tabla KM.")
    
    supervisores_dict = get_supervisores()
    supervisores_list = list(supervisores_dict.keys()) if supervisores_dict else []
    
    if not supervisores_list:
        st.info("Primero agrega supervisores")
        return
    
    supervisor_seleccionado = st.selectbox(
        "Seleccionar Supervisor",
        supervisores_list,
        key="admin_supervisor_promotores"
    )
    
    if not supervisor_seleccionado:
        return
    
    promotores = supervisores_dict.get(supervisor_seleccionado, [])
    
    if promotores:
        st.markdown(f"#### Promotores de {supervisor_seleccionado}")
        df_promotores = pd.DataFrame({'Promotor': promotores})
        st.dataframe(df_promotores, use_container_width=True, hide_index=True)
    else:
        st.info(f"No hay promotores para {supervisor_seleccionado}")
    
    st.divider()
    
    # Agregar
    with st.expander("➕ Agregar Promotor", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            nuevo_promotor = st.text_input("Nombre del Promotor", key="new_promotor")
            localidad_asignada = st.text_input("Localidad asignada (opcional)", key="new_promotor_localidad")
        with col2:
            st.write("")
            st.write("")
            if st.button("Agregar Promotor", use_container_width=True):
                if nuevo_promotor and nuevo_promotor.strip():
                    if nuevo_promotor not in promotores:
                        success, msg = agregar_promotor_a_tabla_km(
                            supervisor_seleccionado, 
                            nuevo_promotor, 
                            localidad_asignada if localidad_asignada else None
                        )
                        if success:
                            st.success(f"✅ Promotor {nuevo_promotor} agregado a {supervisor_seleccionado}")
                            st.rerun()
                        else:
                            st.error(f"❌ Error: {msg}")
                    else:
                        st.error("El promotor ya existe para este supervisor")
                else:
                    st.error("Ingresa un nombre válido")
    
    # Editar
    if promotores:
        with st.expander("✏️ Editar Promotor", expanded=False):
            promotor_a_editar = st.selectbox(
                "Seleccionar Promotor a editar",
                promotores,
                key="edit_promotor"
            )
            
            nuevo_nombre = st.text_input(
                "Nuevo nombre del Promotor",
                value=promotor_a_editar if promotor_a_editar else "",
                key="edit_promotor_nombre"
            )
            
            if st.button("Guardar Cambios Promotor", use_container_width=True, type="primary"):
                if nuevo_nombre and nuevo_nombre.strip():
                    if nuevo_nombre != promotor_a_editar:
                        if nuevo_nombre not in promotores:
                            success, msg = editar_promotor_en_tabla_km(
                                supervisor_seleccionado, 
                                promotor_a_editar, 
                                nuevo_nombre
                            )
                            if success:
                                st.success(f"✅ Promotor {promotor_a_editar} → {nuevo_nombre}")
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {msg}")
                        else:
                            st.error("El nuevo nombre ya existe para este supervisor")
                    else:
                        st.warning("El nombre no ha cambiado")
                else:
                    st.error("Ingresa un nombre válido")
    
    # Eliminar
    if promotores:
        with st.expander("🗑️ Eliminar Promotor", expanded=False):
            promotor_a_eliminar = st.selectbox(
                "Seleccionar Promotor a eliminar",
                promotores,
                key="delete_promotor"
            )
            
            st.warning(f"⚠️ Esto eliminará al promotor **{promotor_a_eliminar}** y todas sus localidades asignadas.")
            
            if st.button("Eliminar Promotor", use_container_width=True, type="secondary"):
                success, msg = eliminar_promotor_de_tabla_km(supervisor_seleccionado, promotor_a_eliminar)
                if success:
                    st.success(f"✅ Promotor {promotor_a_eliminar} eliminado")
                    st.rerun()
                else:
                    st.error(f"❌ Error: {msg}")

def agregar_promotor_a_tabla_km(supervisor, promotor, localidad=None):
    """Agrega un promotor a la tabla KM"""
    try:
        tabla_km = get_tabla_km()
        
        nueva_fila = pd.DataFrame({
            'Localidad': [localidad if localidad else 'NUEVA'],
            'KM': [0],
            'KM DENTRO': [0],
            'TOTAL KM': [0],
            'Promotor': [promotor],
            'Supervisor': [supervisor]
        })
        
        tabla_km = pd.concat([tabla_km, nueva_fila], ignore_index=True)
        
        if supervisor in st.session_state.data_base['supervisores']:
            if promotor not in st.session_state.data_base['supervisores'][supervisor]:
                st.session_state.data_base['supervisores'][supervisor].append(promotor)
        
        success, msg = guardar_tabla_km_en_sheets(tabla_km)
        if success:
            cargar_datos_iniciales()
            return True, "Promotor agregado"
        return False, msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def editar_promotor_en_tabla_km(supervisor, promotor_actual, nuevo_nombre):
    """Edita un promotor en la tabla KM"""
    try:
        tabla_km = get_tabla_km()
        
        if 'Supervisor' in tabla_km.columns and 'Promotor' in tabla_km.columns:
            tabla_km.loc[(tabla_km['Supervisor'] == supervisor) & 
                        (tabla_km['Promotor'] == promotor_actual), 'Promotor'] = nuevo_nombre
        
        if supervisor in st.session_state.data_base['supervisores']:
            promotores = st.session_state.data_base['supervisores'][supervisor]
            if promotor_actual in promotores:
                idx = promotores.index(promotor_actual)
                promotores[idx] = nuevo_nombre
        
        success, msg = guardar_tabla_km_en_sheets(tabla_km)
        if success:
            cargar_datos_iniciales()
            return True, "Promotor editado"
        return False, msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def eliminar_promotor_de_tabla_km(supervisor, promotor):
    """Elimina un promotor de la tabla KM"""
    try:
        tabla_km = get_tabla_km()
        
        if 'Supervisor' in tabla_km.columns and 'Promotor' in tabla_km.columns:
            tabla_km = tabla_km[~((tabla_km['Supervisor'] == supervisor) & 
                                  (tabla_km['Promotor'] == promotor))]
        
        if supervisor in st.session_state.data_base['supervisores']:
            if promotor in st.session_state.data_base['supervisores'][supervisor]:
                st.session_state.data_base['supervisores'][supervisor].remove(promotor)
        
        success, msg = guardar_tabla_km_en_sheets(tabla_km)
        if success:
            cargar_datos_iniciales()
            return True, "Promotor eliminado"
        return False, msg
    except Exception as e:
        return False, f"Error: {str(e)}"

# ============================================
# 3. ADMINISTRACIÓN DE LOCALIDADES
# ============================================
def show_localidades_admin():
    """Administración de localidades"""
    st.markdown("### Gestión de Localidades")
    st.caption("Agrega, edita o elimina localidades. Los cambios se guardan en la hoja Tabla KM.")
    
    tabla_km = get_tabla_km()
    
    if tabla_km.empty:
        st.info("No hay localidades cargadas")
        return
    
    st.markdown("#### Localidades actuales")
    st.caption("💡 Edita directamente las celdas para modificar valores. Las filas con Localidad vacía se eliminarán al guardar.")
    
    columnas_mostrar = ['Localidad', 'KM', 'KM DENTRO', 'TOTAL KM', 'Promotor', 'Supervisor']
    columnas_existentes = [col for col in columnas_mostrar if col in tabla_km.columns]
    
    edited_df = st.data_editor(
        tabla_km[columnas_existentes],
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Localidad": st.column_config.TextColumn("Localidad", required=True),
            "KM": st.column_config.NumberColumn("KM", min_value=0, format="%d"),
            "KM DENTRO": st.column_config.NumberColumn("KM Dentro", min_value=0, format="%d"),
            "TOTAL KM": st.column_config.NumberColumn("Total KM", min_value=0, format="%d"),
            "Promotor": st.column_config.TextColumn("Promotor"),
            "Supervisor": st.column_config.TextColumn("Supervisor")
        },
        hide_index=True
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Guardar Cambios", use_container_width=True, type="primary"):
            errores = []
            for idx, row in edited_df.iterrows():
                if pd.isna(row['Localidad']) or row['Localidad'] == '':
                    errores.append(f"Fila {idx+1}: Localidad vacía (se eliminará)")
                if pd.isna(row['KM']) or row['KM'] < 0:
                    errores.append(f"Fila {idx+1}: KM inválido")
                if pd.isna(row['KM DENTRO']) or row['KM DENTRO'] < 0:
                    errores.append(f"Fila {idx+1}: KM DENTRO inválido")
            
            if errores:
                st.warning("⚠️ Advertencias encontradas:")
                for error in errores:
                    st.write(f"- {error}")
            
            edited_df = edited_df[edited_df['Localidad'].notna() & (edited_df['Localidad'] != '')]
            edited_df['TOTAL KM'] = edited_df['KM'] + edited_df['KM DENTRO']
            
            success, msg = guardar_tabla_km_en_sheets(edited_df)
            if success:
                st.success("✅ Localidades actualizadas correctamente")
                cargar_datos_iniciales()
                st.rerun()
            else:
                st.error(f"❌ Error: {msg}")
    
    with col2:
        if st.button("➕ Agregar Localidad", use_container_width=True):
            st.session_state.show_add_localidad = True
    
    with col3:
        if st.button("🔄 Recargar Datos", use_container_width=True):
            cargar_datos_iniciales()
            st.success("✅ Datos recargados")
            st.rerun()
    
    if st.session_state.get('show_add_localidad', False):
        with st.expander("📝 Nueva Localidad", expanded=True):
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                nueva_localidad = st.text_input("Localidad")
            with col2:
                nuevo_km = st.number_input("KM", min_value=0, value=0)
            with col3:
                nuevo_km_dentro = st.number_input("KM Dentro", min_value=0, value=0)
            with col4:
                nuevo_promotor = st.text_input("Promotor")
            with col5:
                nuevo_supervisor = st.text_input("Supervisor")
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("✅ Agregar", use_container_width=True):
                    if nueva_localidad:
                        if nueva_localidad in tabla_km['Localidad'].values:
                            st.error("La localidad ya existe")
                        else:
                            nueva_fila = pd.DataFrame({
                                'Localidad': [nueva_localidad],
                                'KM': [nuevo_km],
                                'KM DENTRO': [nuevo_km_dentro],
                                'TOTAL KM': [nuevo_km + nuevo_km_dentro],
                                'Promotor': [nuevo_promotor],
                                'Supervisor': [nuevo_supervisor]
                            })
                            
                            tabla_km_actualizada = pd.concat([tabla_km, nueva_fila], ignore_index=True)
                            success, msg = guardar_tabla_km_en_sheets(tabla_km_actualizada)
                            if success:
                                st.success("✅ Localidad agregada")
                                st.session_state.show_add_localidad = False
                                cargar_datos_iniciales()
                                st.rerun()
                            else:
                                st.error(f"❌ Error: {msg}")
                    else:
                        st.error("Ingresa el nombre de la localidad")
            
            with col_btn2:
                if st.button("❌ Cancelar", use_container_width=True):
                    st.session_state.show_add_localidad = False
                    st.rerun()

# ============================================
# 4. ELIMINACIÓN MASIVA DE MOVIMIENTOS
# ============================================
def show_eliminar_movimientos():
    """Panel de eliminación masiva de movimientos"""
    st.markdown("### 🗑️ Eliminación Masiva de Movimientos")
    
    if st.session_state.visits.empty:
        st.info("No hay movimientos cargados")
        return
    
    # Estadísticas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Visitas", len(st.session_state.visits))
    with col2:
        meses = st.session_state.visits['Mes'].unique()
        st.metric("Meses", len(meses))
    with col3:
        supervisores = st.session_state.visits['Supervisor'].unique()
        st.metric("Supervisores", len(supervisores))
    
    st.divider()
    st.markdown("#### Selecciona qué eliminar")
    
    opcion = st.radio(
        "Tipo de eliminación:",
        ["Eliminar por Mes", "Eliminar por Supervisor", "Eliminar todo"]
    )
    
    if opcion == "Eliminar por Mes":
        mes_a_eliminar = st.selectbox(
            "Seleccionar Mes",
            sorted(st.session_state.visits['Mes'].unique())
        )
        
        if st.button(f"🗑️ Eliminar {mes_a_eliminar}", use_container_width=True, type="secondary"):
            st.session_state.visits = st.session_state.visits[
                st.session_state.visits['Mes'] != mes_a_eliminar
            ]
            guardar_datos_actuales()
            st.success(f"✅ Eliminados todos los movimientos de {mes_a_eliminar}")
            st.rerun()
    
    elif opcion == "Eliminar por Supervisor":
        supervisor_a_eliminar = st.selectbox(
            "Seleccionar Supervisor",
            sorted(st.session_state.visits['Supervisor'].unique())
        )
        
        if st.button(f"🗑️ Eliminar {supervisor_a_eliminar}", use_container_width=True, type="secondary"):
            st.session_state.visits = st.session_state.visits[
                st.session_state.visits['Supervisor'] != supervisor_a_eliminar
            ]
            guardar_datos_actuales()
            st.success(f"✅ Eliminados todos los movimientos de {supervisor_a_eliminar}")
            st.rerun()
    
    else:
        st.warning("⚠️ Esta acción eliminará TODOS los movimientos")
        if st.button("🗑️ Eliminar Todo", use_container_width=True, type="secondary"):
            st.session_state.visits = pd.DataFrame(columns=VISITS_COLUMNS)
            guardar_datos_actuales()
            st.success("✅ Eliminados todos los movimientos")
            st.rerun()
    
    # Mostrar datos
    st.divider()
    st.markdown("#### 📋 Movimientos Actuales")
    if not st.session_state.visits.empty:
        st.dataframe(st.session_state.visits, use_container_width=True)
    else:
        st.info("No hay movimientos")