# test_km.py
import streamlit as st
from modules.data_manager import get_tabla_km, get_km_solo_localidad, get_km_dentro_localidad, get_km_total_localidad

def test_km():
    """Prueba los valores de KM para todas las localidades"""
    tabla_km = get_tabla_km()
    
    if tabla_km.empty:
        print("❌ Tabla KM vacía")
        return
    
    print("🔍 Columnas en Tabla KM:", tabla_km.columns.tolist())
    print("\n📊 Mostrando primeras 5 filas:")
    print(tabla_km.head())
    
    print("\n🔍 Probando localidad ACEBAL:")
    print(f"  KM solo: {get_km_solo_localidad('ACEBAL')}")
    print(f"  KM DENTRO: {get_km_dentro_localidad('ACEBAL')}")
    print(f"  TOTAL KM: {get_km_total_localidad('ACEBAL')}")
    
    print("\n🔍 Probando localidad CAÑADA DE GOMEZ:")
    print(f"  KM solo: {get_km_solo_localidad('CAÑADA DE GOMEZ')}")
    print(f"  KM DENTRO: {get_km_dentro_localidad('CAÑADA DE GOMEZ')}")
    print(f"  TOTAL KM: {get_km_total_localidad('CAÑADA DE GOMEZ')}")

if __name__ == "__main__":
    # Primero cargar datos
    from modules.data_manager import cargar_datos_iniciales
    cargar_datos_iniciales()
    test_km()