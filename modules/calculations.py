# modules/calculations.py
import pandas as pd
from modules.data_manager import get_km_total_localidad

# 🔴 LISTA DE PROMOTORES QUE USAN PRECIO DE SUPERVISOR
PROMOTORES_PRECIO_SUPERVISOR = ['DUGO HERNAN', 'BUFFA GASTON']

def calcular_viaticos(visits_df, km_moto, km_auto, km_supervisor):
    """
    Calcula los viáticos de todas las visitas usando TOTAL KM.
    Los promotores en PROMOTORES_PRECIO_SUPERVISOR usan km_supervisor.
    """
    if visits_df.empty:
        return pd.DataFrame()
    
    resultados = []
    
    for promotor in visits_df['Promotor'].unique():
        df_promotor = visits_df[visits_df['Promotor'] == promotor]
        supervisor = df_promotor['Supervisor'].iloc[0]
        mes = df_promotor['Mes'].iloc[0] if 'Mes' in df_promotor.columns else ''
        
        # 🔴 DETERMINAR QUÉ PRECIO USAR PARA ESTE PROMOTOR
        if promotor.upper() in [p.upper() for p in PROMOTORES_PRECIO_SUPERVISOR]:
            precio_a_usar = km_supervisor
            tipo_precio = "Supervisor"
        else:
            precio_a_usar = km_moto  # Por defecto usamos el precio de moto
            tipo_precio = "Moto"
        
        km_moto_total = 0
        km_auto_total = 0
        total_peaje = 0
        total_km_extras = 0
        
        for _, row in df_promotor.iterrows():
            km_total = get_km_total_localidad(row['Localidad'], promotor)
            
            km_moto_total += row['Veces Moto'] * km_total
            km_auto_total += row['Veces Auto'] * km_total
            
            if 'Peajes' in row:
                total_peaje += row['Peajes'] if pd.notna(row['Peajes']) else 0
            
            if 'KM Extras' in row:
                total_km_extras += row['KM Extras'] if pd.notna(row['KM Extras']) else 0
        
        # 🔴 CALCULAR COSTOS USANDO EL PRECIO CORRESPONDIENTE
        # Para los promotores con precio supervisor, TODOS los km se pagan a precio supervisor
        if promotor.upper() in [p.upper() for p in PROMOTORES_PRECIO_SUPERVISOR]:
            # Ambos (moto y auto) se pagan a precio supervisor
            costo_moto = km_moto_total * km_supervisor
            costo_auto = km_auto_total * km_supervisor
            costo_km_extras = total_km_extras * km_supervisor
        else:
            # Precio normal: moto a precio moto, auto a precio auto
            costo_moto = km_moto_total * km_moto
            costo_auto = km_auto_total * km_auto
            costo_km_extras = total_km_extras * km_moto
        
        total_viaticos = costo_moto + costo_auto + costo_km_extras + total_peaje
        
        resultados.append({
            'Supervisor': supervisor,
            'Promotor': promotor,
            'Mes': mes,
            'Tipo Precio': tipo_precio,  # 🔴 NUEVO: indicar qué precio se usó
            'KM MOTO': km_moto_total,
            '$ MOTO': costo_moto,
            'KM AUTO': km_auto_total,
            '$ AUTO': costo_auto,
            'KM TOTAL': km_moto_total + km_auto_total,
            'KM EXTRAS': total_km_extras,
            '$ KM EXTRAS': costo_km_extras,
            'PEAJE': total_peaje,
            '$ VIATICOS': total_viaticos
        })
    
    return pd.DataFrame(resultados)

def calcular_resumen_por_supervisor(resultados):
    """Calcula el resumen por supervisor"""
    if resultados.empty:
        return pd.DataFrame()
    return resultados.groupby('Supervisor').agg({
        '$ VIATICOS': 'sum',
        'KM TOTAL': 'sum',
        'Promotor': 'count'
    }).reset_index().rename(columns={'Promotor': 'Cantidad'})

def calcular_total_general(resultados):
    """Calcula el total general de viáticos"""
    if resultados.empty:
        return 0
    return resultados['$ VIATICOS'].sum()

def preparar_tabla_para_mostrar(resultados):
    """Prepara el DataFrame para mostrar en la interfaz"""
    if resultados.empty:
        return pd.DataFrame()
    
    display_df = resultados.copy()
    display_df['$ MOTO'] = display_df['$ MOTO'].apply(lambda x: f"${x:,.0f}")
    display_df['$ AUTO'] = display_df['$ AUTO'].apply(lambda x: f"${x:,.0f}")
    display_df['$ KM EXTRAS'] = display_df['$ KM EXTRAS'].apply(lambda x: f"${x:,.0f}")
    display_df['PEAJE'] = display_df['PEAJE'].apply(lambda x: f"${x:,.0f}")
    display_df['$ VIATICOS'] = display_df['$ VIATICOS'].apply(lambda x: f"${x:,.0f}")
    
    return display_df