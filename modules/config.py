# modules/config.py
import os

# URL de Google Sheets
SHEET_URL = "https://docs.google.com/spreadsheets/d/1piffkqZ9xGZnfqmDPU_9dEoL_TPZSbXRxLngGjS2BHo/edit"

# Meses en español
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
         'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

# Valores base (sin ajuste)
BASE_VALUES = {
    'km_moto': 188,
    'km_auto': 531,
    'km_supervisor': 576
}

# Columnas para el DataFrame de visitas
VISITS_COLUMNS = ['Mes', 'Promotor', 'Localidad', 'Veces Moto', 
                  'Veces Auto', 'Peajes', 'KM Extras', 'Supervisor', 
                  'KM Supervisor', 'Fecha']

# Buscar credenciales
CREDENTIALS_PATHS = [
    'credentials.json',
    'service_account.json',
    os.path.join(os.path.expanduser('~'), '.streamlit', 'credentials.json')
]