# modules/dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from modules.data_manager import (
    get_tabla_km, 
    get_km_total_localidad,
    get_km_solo_localidad,
    get_km_dentro_localidad
)
from modules.calculations import (
    calcular_viaticos, preparar_tabla_para_mostrar, 
    calcular_total_general
)
from modules.config import MESES

def to_excel_download(df_list, sheet_names, filename):
    """Convierte DataFrames a Excel para descarga"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for df, sheet_name in zip(df_list, sheet_names):
            if not df.empty:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output

def to_excel_single(df, filename, sheet_name='Sheet1'):
    """Convierte un DataFrame a Excel para descarga"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if not df.empty:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    output.seek(0)
    return output

def show_dashboard():
    """Panel de Dashboard"""
    st.markdown("## 📊 Dashboard de Viáticos")
    
    # ============================================
    # 1. BLOQUE DE AJUSTE (INDEPENDIENTE)
    # ============================================
    st.markdown("### 💰 Configuración de Ajuste")
    st.caption("Define el porcentaje de ajuste para cada mes. Los valores se guardan en la hoja AJUSTES.")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        mes_ajuste = st.selectbox(
            "📅 Mes Ajuste",
            MESES,
            index=datetime.now().month - 1,
            key="mes_ajuste"
        )
    
    with col2:
        # Obtener el ajuste actual del mes seleccionado (para mostrar si existe)
        ajuste_actual_mes = 0.0
        existe_ajuste = False
        if hasattr(st.session_state, 'ajustes_data') and not st.session_state.ajustes_data.empty:
            ajuste_mes = st.session_state.ajustes_data[st.session_state.ajustes_data['Mes'] == mes_ajuste]
            if not ajuste_mes.empty and '% Ajuste' in ajuste_mes.columns:
                ajuste_actual_mes = float(ajuste_mes['% Ajuste'].iloc[0])
                existe_ajuste = True
        
        # 🔴 CORREGIDO: value=None para que inicie vacío
        porcentaje_ajuste = st.number_input(
            "% Ajuste",
            min_value=-100.0,
            max_value=100.0,
            value=None,  # ← Inicia vacío
            step=0.5,
            key="porcentaje_ajuste",
            help="Ingresa el porcentaje de ajuste para el mes seleccionado",
            placeholder="Ej: 2.5"  # Placeholder como referencia
        )
        
        # Si hay un ajuste guardado y el campo está vacío, mostrar el valor guardado como referencia
        if existe_ajuste and porcentaje_ajuste is None:
            st.caption(f"💡 Ajuste actual: {ajuste_actual_mes}%")
        
        if st.button("💾 Guardar Ajuste", key="save_ajuste", use_container_width=True):
            from modules.data_manager import guardar_ajuste
            
            # Si el campo está vacío, usar el valor actual (0) o el que tenía
            valor_a_guardar = porcentaje_ajuste if porcentaje_ajuste is not None else ajuste_actual_mes
            
            success, msg = guardar_ajuste(mes_ajuste, valor_a_guardar)
            if success:
                st.success(f"✅ Ajuste de {valor_a_guardar}% aplicado para {mes_ajuste}")
                st.rerun()
            else:
                st.error(f"❌ Error: {msg}")
    
    with col3:
        st.markdown("**📅 Última actualización**")
        fecha_ajuste = "Sin registro"
        if hasattr(st.session_state, 'ajustes_data') and not st.session_state.ajustes_data.empty:
            ajuste_mes = st.session_state.ajustes_data[st.session_state.ajustes_data['Mes'] == mes_ajuste]
            if not ajuste_mes.empty:
                for col in ajuste_mes.columns:
                    if 'Fecha' in col or 'fecha' in col.lower():
                        valor = ajuste_mes[col].iloc[0]
                        if pd.notna(valor) and str(valor).strip() != '':
                            fecha_ajuste = str(valor)
                        break
        st.info(f"📅 {fecha_ajuste}")
    
    # Mostrar los valores de KM del mes de ajuste con su % aplicado
    st.markdown("---")
    st.markdown("**📊 Valores para el mes seleccionado**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        km_moto_ajuste = st.session_state.km_moto
        if hasattr(st.session_state, 'ajustes_data') and not st.session_state.ajustes_data.empty:
            ajuste_mes = st.session_state.ajustes_data[st.session_state.ajustes_data['Mes'] == mes_ajuste]
            if not ajuste_mes.empty and 'KM Moto' in ajuste_mes.columns:
                km_moto_ajuste = float(ajuste_mes['KM Moto'].iloc[0])
        st.metric("🏍️ KM Moto", f"${km_moto_ajuste:.2f}")
    
    with col2:
        km_auto_ajuste = st.session_state.km_auto
        if hasattr(st.session_state, 'ajustes_data') and not st.session_state.ajustes_data.empty:
            ajuste_mes = st.session_state.ajustes_data[st.session_state.ajustes_data['Mes'] == mes_ajuste]
            if not ajuste_mes.empty and 'KM Auto' in ajuste_mes.columns:
                km_auto_ajuste = float(ajuste_mes['KM Auto'].iloc[0])
        st.metric("🚗 KM Auto", f"${km_auto_ajuste:.2f}")
    
    with col3:
        km_supervisor_ajuste = st.session_state.km_supervisor
        if hasattr(st.session_state, 'ajustes_data') and not st.session_state.ajustes_data.empty:
            ajuste_mes = st.session_state.ajustes_data[st.session_state.ajustes_data['Mes'] == mes_ajuste]
            if not ajuste_mes.empty and 'KM Supervisor' in ajuste_mes.columns:
                km_supervisor_ajuste = float(ajuste_mes['KM Supervisor'].iloc[0])
        st.metric("👔 KM Supervisor", f"${km_supervisor_ajuste:.2f}")
    
    with col4:
        # Mostrar el % de ajuste aplicado
        porcentaje_aplicado = ajuste_actual_mes if existe_ajuste else 0.0
        st.metric(
            "📊 % Ajuste Aplicado",
            f"{porcentaje_aplicado:.1f}%",
            delta=f"{'Ajustado' if porcentaje_aplicado != 0 else 'Base'}"
        )
    
    st.divider()
    
    # ============================================
    # 2. SELECCIÓN DE MES PARA DATOS (CONTROLA EL DASHBOARD)
    # ============================================
    st.markdown("### 📊 Seleccionar Mes para Datos")
    st.caption("Los datos que se muestran abajo corresponden al mes seleccionado.")
    
    if not st.session_state.visits.empty and 'Mes' in st.session_state.visits.columns:
        meses_disponibles = sorted(st.session_state.visits['Mes'].unique())
    else:
        meses_disponibles = MESES
    
    mes_datos = st.selectbox(
        "📅 Seleccionar Mes para Datos",
        meses_disponibles,
        index=len(meses_disponibles) - 1 if meses_disponibles else 0,
        key="mes_datos"
    )
    
    st.divider()
    
    # ============================================
    # 3. FILTRAR DATOS POR MES DE DATOS
    # ============================================
    visits_filtradas = st.session_state.visits[
        (st.session_state.visits['Mes'] == mes_datos) &
        (st.session_state.visits['Promotor'] != 'SUPERVISOR')
    ]
    
    visits_supervisor = st.session_state.visits[
        (st.session_state.visits['Mes'] == mes_datos) &
        (st.session_state.visits['Promotor'] == 'SUPERVISOR')
    ]
    
    # Obtener los valores de KM para el mes de datos
    km_moto_datos = st.session_state.km_moto
    km_auto_datos = st.session_state.km_auto
    km_supervisor_datos = st.session_state.km_supervisor
    
    if hasattr(st.session_state, 'ajustes_data') and not st.session_state.ajustes_data.empty:
        ajuste_mes_datos = st.session_state.ajustes_data[st.session_state.ajustes_data['Mes'] == mes_datos]
        if not ajuste_mes_datos.empty:
            if 'KM Moto' in ajuste_mes_datos.columns:
                km_moto_datos = float(ajuste_mes_datos['KM Moto'].iloc[0])
            if 'KM Auto' in ajuste_mes_datos.columns:
                km_auto_datos = float(ajuste_mes_datos['KM Auto'].iloc[0])
            if 'KM Supervisor' in ajuste_mes_datos.columns:
                km_supervisor_datos = float(ajuste_mes_datos['KM Supervisor'].iloc[0])
    
    # ============================================
    # 4. CALCULAR VIÁTICOS DE PROMOTORES
    # ============================================
    if not visits_filtradas.empty:
        resultados_promotores = calcular_viaticos(
            visits_filtradas,
            km_moto_datos,
            km_auto_datos,
            km_supervisor_datos
        )
    else:
        resultados_promotores = pd.DataFrame()
    
    # ============================================
    # 5. CALCULAR VIÁTICOS DE SUPERVISORES
    # ============================================
    resultados_supervisores = []
    
    if not visits_supervisor.empty:
        for _, row in visits_supervisor.iterrows():
            km = row['KM Supervisor'] if pd.notna(row['KM Supervisor']) else 0
            supervisor = row['Supervisor']
            if km > 0:
                resultados_supervisores.append({
                    'Supervisor': supervisor,
                    'KM SUPERVISOR': km,
                    '$ SUPERVISOR': km * km_supervisor_datos
                })
    
    df_supervisores = pd.DataFrame(resultados_supervisores) if resultados_supervisores else pd.DataFrame()
    
    # ============================================
    # 6. MÉTRICAS - SUPERVISORES
    # ============================================
    if not df_supervisores.empty:
        st.markdown("### 📊 Resumen Supervisores")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Supervisores", len(df_supervisores))
        with col2:
            st.metric("📏 KM Totales", f"{df_supervisores['KM SUPERVISOR'].sum():,.0f}")
        with col3:
            st.metric("💰 Total a Pagar", f"${df_supervisores['$ SUPERVISOR'].sum():,.0f}")
        
        st.divider()
    
    # ============================================
    # 7. TABLA - SUPERVISORES
    # ============================================
    if not df_supervisores.empty:
        st.markdown("### 📋 Resumen por Supervisor")
        
        display_super = df_supervisores.copy()
        display_super['$ SUPERVISOR'] = display_super['$ SUPERVISOR'].apply(lambda x: f"${x:,.0f}")
        
        altura = min(len(display_super) * 35 + 40, 400)
        
        st.dataframe(
            display_super,
            use_container_width=True,
            hide_index=True,
            height=altura,
            column_config={
                "Supervisor": "Supervisor",
                "KM SUPERVISOR": "KM",
                "$ SUPERVISOR": "$ Viáticos"
            }
        )
        
        st.caption(f"💰 **Total Viáticos Supervisores: ${df_supervisores['$ SUPERVISOR'].sum():,.0f}**")
        st.divider()
    
    # ============================================
    # 8. MÉTRICAS - PROMOTORES
    # ============================================
    if not resultados_promotores.empty:
        st.markdown("### 📊 Resumen Promotores")
        col1, col2, col3, col4 = st.columns(4)
        
        df_metricas = resultados_promotores.groupby('Promotor').agg({
            '$ VIATICOS': 'sum',
            'KM TOTAL': 'sum'
        }).reset_index()
        
        with col1:
            st.metric("👥 Promotores", len(df_metricas['Promotor'].unique()))
        with col2:
            st.metric("📋 Visitas", len(visits_filtradas))
        with col3:
            st.metric("📏 KM Totales", f"{df_metricas['KM TOTAL'].sum():,.0f}")
        with col4:
            st.metric("💰 Total a Pagar", f"${df_metricas['$ VIATICOS'].sum():,.0f}")
        
        st.divider()
    
    # ============================================
    # 9. TABLA - RESUMEN POR PROMOTOR (COMPLETO)
    # ============================================
    if not resultados_promotores.empty:
        st.markdown("### 📋 Resumen por Promotor")
        
        df_consolidado = resultados_promotores.groupby('Promotor', as_index=False).agg({
            'KM MOTO': 'sum',
            '$ MOTO': 'sum',
            'KM AUTO': 'sum',
            '$ AUTO': 'sum',
            'KM TOTAL': 'sum',
            'KM EXTRAS': 'sum',
            '$ KM EXTRAS': 'sum',
            'PEAJE': 'sum',
            '$ VIATICOS': 'sum'
        })
        
        df_consolidado = df_consolidado.sort_values('$ VIATICOS', ascending=False)
        
        # Formatear para mostrar
        display_df = df_consolidado.copy()
        display_df['$ MOTO'] = display_df['$ MOTO'].apply(lambda x: f"${x:,.0f}")
        display_df['$ AUTO'] = display_df['$ AUTO'].apply(lambda x: f"${x:,.0f}")
        display_df['$ KM EXTRAS'] = display_df['$ KM EXTRAS'].apply(lambda x: f"${x:,.0f}")
        display_df['PEAJE'] = display_df['PEAJE'].apply(lambda x: f"${x:,.0f}")
        display_df['$ VIATICOS'] = display_df['$ VIATICOS'].apply(lambda x: f"${x:,.0f}")
        
        altura = min(len(display_df) * 35 + 40, 400)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=altura
        )
        
        # 🔴 CORREGIDO: Botón de exportación a Excel (ancho completo)
        st.markdown("---")
        excel_promotores = to_excel_single(
            df_consolidado,
            f"resumen_promotores_{mes_datos}.xlsx"
        )
        st.download_button(
            label="📥 Exportar Promotores a Excel",
            data=excel_promotores,
            file_name=f"resumen_promotores_{mes_datos}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.divider()
    
    # ============================================
    # 10. BOTÓN EXPORTAR - SOLO NOMBRE Y TOTAL
    # ============================================
    st.markdown("### 📥 Exportar Resumen (Nombre y Total)")
    
    totales_por_nombre = {}
    
    if not resultados_promotores.empty:
        for _, row in resultados_promotores.iterrows():
            nombre = row['Promotor']
            total = row['$ VIATICOS']
            if nombre in totales_por_nombre:
                totales_por_nombre[nombre] += total
            else:
                totales_por_nombre[nombre] = total
    
    if not df_supervisores.empty:
        for _, row in df_supervisores.iterrows():
            nombre = row['Supervisor']
            total = row['$ SUPERVISOR']
            if nombre in totales_por_nombre:
                totales_por_nombre[nombre] += total
            else:
                totales_por_nombre[nombre] = total
    
    if totales_por_nombre:
        df_export_unificado = pd.DataFrame([
            {'Nombre': nombre, 'Total $': total}
            for nombre, total in totales_por_nombre.items()
        ])
        
        df_export_unificado = df_export_unificado.sort_values('Total $', ascending=False)
        
        # 🔴 CORREGIDO: Formato contable y centrado
        # Crear una copia para mostrar con formato
        display_export = df_export_unificado.copy()
        display_export['Total $'] = display_export['Total $'].apply(lambda x: f"${x:,.0f}")
        
        altura = min(len(display_export) * 35 + 40, 400)
        
        st.dataframe(
            display_export,
            use_container_width=True,
            hide_index=True,
            height=altura,
            column_config={
                "Nombre": st.column_config.TextColumn(
                    "Nombre",
                    help="Nombre del promotor o supervisor",
                    width="medium"
                ),
                "Total $": st.column_config.TextColumn(
                    "Total $",
                    help="Total a pagar en formato contable",
                    width="medium"
                )
            }
        )
        
        # Aplicar CSS para centrar las celdas
        st.markdown(
            """
            <style>
            .stDataFrame td {
                text-align: center !important;
            }
            .stDataFrame th {
                text-align: center !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        
        # Botón de exportación con el formato original (sin formato para el Excel)
        excel_unificado = to_excel_single(
            df_export_unificado,
            f"resumen_nombre_total_{mes_datos}.xlsx"
        )
        st.download_button(
            label="📥 Exportar Nombre y Total a Excel",
            data=excel_unificado,
            file_name=f"resumen_nombre_total_{mes_datos}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.divider()
    
    # ============================================
    # 11. TABLA DE DETALLE COMPLETO POR LOCALIDAD
    # ============================================
    st.markdown("### 📋 Detalle Completo por Localidad")
    st.caption("Desglose de todas las visitas con kilómetros y costos")
    
    df_detalle = pd.DataFrame()
    
    if not visits_filtradas.empty:
        tabla_km = get_tabla_km()
        
        detalle = []
        
        for _, row in visits_filtradas.iterrows():
            localidad = row['Localidad']
            promotor = row['Promotor']
            supervisor = row['Supervisor']
            veces_moto = int(row['Veces Moto']) if pd.notna(row['Veces Moto']) else 0
            veces_auto = int(row['Veces Auto']) if pd.notna(row['Veces Auto']) else 0
            peajes = int(row['Peajes']) if pd.notna(row['Peajes']) else 0
            km_extras = int(row['KM Extras']) if pd.notna(row['KM Extras']) else 0
            
            km_solo = get_km_solo_localidad(localidad, promotor)
            km_dentro = get_km_dentro_localidad(localidad, promotor)
            km_total = get_km_total_localidad(localidad, promotor)
            
            km_moto_total = veces_moto * km_total
            km_auto_total = veces_auto * km_total
            
            # Usar los valores de KM del mes de datos
            costo_moto = km_moto_total * km_moto_datos
            costo_auto = km_auto_total * km_auto_datos
            costo_km_extras = km_extras * km_moto_datos
            
            detalle.append({
                'Mes': mes_datos,
                'Supervisor': supervisor,
                'Promotor': promotor,
                'Localidad': localidad,
                'KM': km_solo,
                'KM DENTRO': km_dentro,
                'TOTAL KM': km_total,
                'Veces Moto': veces_moto,
                'KM Moto': km_moto_total,
                'Costo Moto': costo_moto,
                'Veces Auto': veces_auto,
                'KM Auto': km_auto_total,
                'Costo Auto': costo_auto,
                'KM Extras': km_extras,
                'Costo KM Extras': costo_km_extras,
                'Peajes': peajes,
                'Total Localidad': costo_moto + costo_auto + costo_km_extras + peajes
            })
        
        df_detalle = pd.DataFrame(detalle)
        
        display_detalle = df_detalle.copy()
        display_detalle['Costo Moto'] = display_detalle['Costo Moto'].apply(lambda x: f"${x:,.0f}")
        display_detalle['Costo Auto'] = display_detalle['Costo Auto'].apply(lambda x: f"${x:,.0f}")
        display_detalle['Costo KM Extras'] = display_detalle['Costo KM Extras'].apply(lambda x: f"${x:,.0f}")
        display_detalle['Peajes'] = display_detalle['Peajes'].apply(lambda x: f"${x:,.0f}")
        display_detalle['Total Localidad'] = display_detalle['Total Localidad'].apply(lambda x: f"${x:,.0f}")
        
        altura = min(len(display_detalle) * 35 + 40, 400)
        
        st.dataframe(
            display_detalle,
            use_container_width=True,
            hide_index=True,
            height=altura,
            column_config={
                "Mes": "Mes",
                "Supervisor": "Supervisor",
                "Promotor": "Promotor",
                "Localidad": "Localidad",
                "KM": "KM",
                "KM DENTRO": "KM Dentro",
                "TOTAL KM": "Total KM",
                "Veces Moto": "Veces Moto",
                "KM Moto": "KM Moto",
                "Costo Moto": "Costo Moto",
                "Veces Auto": "Veces Auto",
                "KM Auto": "KM Auto",
                "Costo Auto": "Costo Auto",
                "KM Extras": "KM Extras",
                "Costo KM Extras": "Costo KM Extras",
                "Peajes": "Peajes",
                "Total Localidad": "Total Localidad"
            }
        )
        
        # ============================================
        # 12. BOTÓN EXPORTAR DETALLE COMPLETO
        # ============================================
        
        excel_detalle = to_excel_single(
            df_detalle,
            f"detalle_viaticos_{mes_datos}.xlsx"
        )
        st.download_button(
            label="📥 Exportar Detalle Completo a Excel",
            data=excel_detalle,
            file_name=f"detalle_viaticos_{mes_datos}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )