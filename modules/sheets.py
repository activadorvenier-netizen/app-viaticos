# modules/sheets.py
import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime
from modules.config import SHEET_URL, CREDENTIALS_PATHS, BASE_VALUES

def get_sheets_client():
    """Conecta a Google Sheets"""
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

def cargar_datos_base():
    """Carga los datos base desde Google Sheets"""
    try:
        client, msg = get_sheets_client()
        if not client:
            return None, msg
        
        sheet = client.open_by_url(SHEET_URL)
        data = {}
        
        # 1. TABLA KM
        try:
            try:
                ws = sheet.worksheet("Tabla KM")
            except:
                try:
                    ws = sheet.worksheet("TABLA KM")
                except:
                    ws = sheet.worksheet("TablaKM")
            
            records = ws.get_all_records()
            df = pd.DataFrame(records)
            
            if 'TOTAL KM' not in df.columns:
                if 'KM' in df.columns and 'KM DENTRO' in df.columns:
                    df['TOTAL KM'] = df['KM'] + df['KM DENTRO']
                elif 'KM' in df.columns:
                    df['TOTAL KM'] = df['KM']
            
            data['tabla_km'] = df
            
        except Exception as e:
            data['tabla_km'] = pd.DataFrame()
            st.error(f"❌ No se encontró la hoja 'Tabla KM'")
        
        # 2. Obtener supervisores y promotores
        supervisores_dict = {}
        
        if not data['tabla_km'].empty:
            df = data['tabla_km']
            
            col_supervisor = None
            col_promotor = None
            
            for col in df.columns:
                if col == 'Supervisor':
                    col_supervisor = col
                elif col == 'Promotor':
                    col_promotor = col
            
            if col_supervisor and col_promotor:
                supervisores_unicos = df[col_supervisor].dropna().unique()
                supervisores_unicos = [s for s in supervisores_unicos if str(s).strip() != '']
                
                for supervisor in supervisores_unicos:
                    promotores = df[df[col_supervisor] == supervisor][col_promotor].dropna().unique().tolist()
                    promotores = [p for p in promotores if str(p).strip() != '']
                    
                    if promotores:
                        supervisores_dict[supervisor] = promotores
        
        data['supervisores'] = supervisores_dict
        
        # 3. VISITAS_GUARDADAS
        try:
            ws = sheet.worksheet("VISITAS_GUARDADAS")
            records = ws.get_all_records()
            data['visitas_guardadas'] = pd.DataFrame(records)
        except:
            ws = sheet.add_worksheet("VISITAS_GUARDADAS", rows=1000, cols=20)
            titulos = ['Mes', 'Promotor', 'Localidad', 'Veces Moto', 
                      'Veces Auto', 'Peajes', 'KM Extras', 'Supervisor', 
                      'KM Supervisor', 'Fecha']
            ws.update([titulos])
            data['visitas_guardadas'] = pd.DataFrame()
        
        # 4. AJUSTES
        try:
            ws = sheet.worksheet("AJUSTES")
            records = ws.get_all_records()
            data['ajustes'] = pd.DataFrame(records)
        except:
            ws = sheet.add_worksheet("AJUSTES", rows=100, cols=20)
            titulos = ['Mes', '% Ajuste', 'KM Moto', 'KM Auto', 'KM Supervisor', 'Fecha Ajuste']
            ws.update([titulos])
            
            from modules.config import MESES
            mes_actual = MESES[datetime.now().month - 1]
            fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
            ws.append_row([
                mes_actual,
                0,
                BASE_VALUES['km_moto'],
                BASE_VALUES['km_auto'],
                BASE_VALUES['km_supervisor'],
                fecha_actual
            ])
            
            data['ajustes'] = pd.DataFrame([{
                'Mes': mes_actual,
                '% Ajuste': 0,
                'KM Moto': BASE_VALUES['km_moto'],
                'KM Auto': BASE_VALUES['km_auto'],
                'KM Supervisor': BASE_VALUES['km_supervisor'],
                'Fecha Ajuste': fecha_actual
            }])
        
        return data, "Datos cargados correctamente"
    except Exception as e:
        return None, f"Error general: {str(e)}"

def guardar_visitas_en_sheets(visitas_df):
    """Guarda las visitas en Google Sheets"""
    try:
        client, msg = get_sheets_client()
        if not client:
            return False, msg
        
        sheet = client.open_by_url(SHEET_URL)
        
        try:
            ws = sheet.worksheet("VISITAS_GUARDADAS")
            ws.clear()
        except:
            ws = sheet.add_worksheet("VISITAS_GUARDADAS", rows=1000, cols=20)
        
        titulos = ['Mes', 'Promotor', 'Localidad', 'Veces Moto', 
                  'Veces Auto', 'Peajes', 'KM Extras', 'Supervisor', 
                  'KM Supervisor', 'Fecha']
        
        if not visitas_df.empty:
            for col in titulos:
                if col not in visitas_df.columns:
                    visitas_df[col] = ''
            
            datos = [titulos] + visitas_df[titulos].values.tolist()
            ws.update(datos)
            return True, f"✅ {len(visitas_df)} registros guardados"
        else:
            ws.update([titulos])
            return True, "✅ Hoja preparada"
            
    except Exception as e:
        return False, f"Error al guardar: {str(e)}"

def cargar_visitas_guardadas():
    """Carga las visitas guardadas desde Sheets"""
    try:
        client, msg = get_sheets_client()
        if not client:
            return pd.DataFrame(), msg
        
        sheet = client.open_by_url(SHEET_URL)
        
        try:
            ws = sheet.worksheet("VISITAS_GUARDADAS")
            records = ws.get_all_records()
            df = pd.DataFrame(records)
            return df, "Datos cargados"
        except:
            return pd.DataFrame(), "No hay datos guardados"
    except Exception as e:
        return pd.DataFrame(), f"Error: {str(e)}"

# 🔴 FUNCIONES PARA AJUSTES
def guardar_ajuste_en_sheets(mes, porcentaje, km_moto, km_auto, km_supervisor):
    """Guarda un ajuste en la hoja AJUSTES con fecha"""
    try:
        client, msg = get_sheets_client()
        if not client:
            return False, msg
        
        sheet = client.open_by_url(SHEET_URL)
        fecha_actual = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        try:
            ws = sheet.worksheet("AJUSTES")
        except:
            ws = sheet.add_worksheet("AJUSTES", rows=100, cols=20)
            titulos = ['Mes', '% Ajuste', 'KM Moto', 'KM Auto', 'KM Supervisor', 'Fecha Ajuste']
            ws.update([titulos])
        
        # Buscar si ya existe el mes
        registros = ws.get_all_records()
        df = pd.DataFrame(registros)
        
        if not df.empty and mes in df['Mes'].values:
            # Actualizar fila existente
            idx = df[df['Mes'] == mes].index[0] + 2  # +2 por el header y el 0-index
            ws.update(f'B{idx}:F{idx}', [[porcentaje, km_moto, km_auto, km_supervisor, fecha_actual]])
        else:
            # Agregar nueva fila
            ws.append_row([mes, porcentaje, km_moto, km_auto, km_supervisor, fecha_actual])
        
        return True, f"✅ Ajuste para {mes} guardado correctamente"
    except Exception as e:
        return False, f"Error: {str(e)}"

def cargar_ajuste_por_mes(mes):
    """Carga el ajuste de un mes específico"""
    try:
        client, msg = get_sheets_client()
        if not client:
            return None, msg
        
        sheet = client.open_by_url(SHEET_URL)
        
        try:
            ws = sheet.worksheet("AJUSTES")
            records = ws.get_all_records()
            df = pd.DataFrame(records)
            
            if df.empty:
                return None, "No hay ajustes configurados"
            
            row = df[df['Mes'] == mes]
            if row.empty:
                return None, f"No hay ajuste para {mes}"
            
            return row.iloc[0].to_dict(), "Ajuste encontrado"
        except Exception as e:
            return None, f"Error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def cargar_todos_los_ajustes():
    """Carga todos los ajustes"""
    try:
        client, msg = get_sheets_client()
        if not client:
            return pd.DataFrame(), msg
        
        sheet = client.open_by_url(SHEET_URL)
        
        try:
            ws = sheet.worksheet("AJUSTES")
            records = ws.get_all_records()
            df = pd.DataFrame(records)
            return df, "Ajustes cargados"
        except:
            return pd.DataFrame(), "No hay ajustes configurados"
    except Exception as e:
        return pd.DataFrame(), f"Error: {str(e)}"