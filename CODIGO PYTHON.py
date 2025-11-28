"""
Dashboard de Monitoreo Ambiental - Emisiones Fugitivas en Tanques
Enfoque: Gestión de Emission Rate (kg/h) para OGMP Nivel 5 y inventario GEI
Autor: Equipo Técnico Ambiental
Última actualización: Noviembre 2025

═══════════════════════════════════════════════════════════════════════════════
ESTRUCTURA DEL DASHBOARD - REORGANIZADO Y OPTIMIZADO
═══════════════════════════════════════════════════════════════════════════════

1. CONFIGURACIÓN GLOBAL Y ESTILOS
   └─ Paleta de colores empresarial
   └─ Configuración de página y CSS responsivo
   └─ Título principal con diseño mejorado

2. CARGA Y VALIDACIÓN DE DATOS
   └─ Funciones de detección automática de hojas Excel
   └─ Auto-detección de columnas (lat, lon, CH4, emission rate, viento, etc.)
   └─ Validación y limpieza profunda de datos
   └─ Filtros por campo operativo (Chichimene, Castilla, etc.)

3. SECCIÓN DE KPIs PRINCIPALES
   └─ KPIs de Emission Rate (prioridad OGMP Nivel 5)
      • Emisión Total, Mayor Emisor, Menor Emisor, Promedio/Instalación, Mediciones
   └─ Métricas de Concentración CH₄
      • Total puntos, Pico Máximo, Promedio, Mínimo (con botones de navegación)

4. NAVEGACIÓN POR TABS

   ┌─────────────────────────────────────────────────────────────────────┐
   │ TAB 1: 🗺️ MAPA SATELITAL INTERACTIVO                               │
   ├─────────────────────────────────────────────────────────────────────┤
   │ • Mapa satelital con capa Esri World Imagery                        │
   │ • Marcadores con escala de colores por concentración                │
   │ • Popups informativos con datos completos                           │
   │ • Navegación automática a puntos máximo/mínimo                      │
   │ • Colormap con gradiente verde → amarillo → rojo                    │
   └─────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────┐
   │ TAB 2: 📊 ANÁLISIS INTEGRAL DE EMISIONES                           │
   ├─────────────────────────────────────────────────────────────────────┤
   │                                                                      │
   │ 📌 SECCIÓN 1: ANÁLISIS DE TASA DE EMISIÓN (EMISSION RATE)          │
   │    ├─ Ranking de instalaciones (barras horizontales + tabla)        │
   │    ├─ Filtros: Top N, métricas (Total/Promedio/Máximo)             │
   │    ├─ Estadísticas por instalación                                  │
   │    └─ KPIs: Total instalaciones, Emisión total, Promedio, Mayor     │
   │                                                                      │
   │ 📌 SECCIÓN 2: CORRELACIÓN EMISSION RATE VS CONCENTRACIÓN            │
   │    ├─ Scatter plot multicolor por instalación                       │
   │    ├─ Análisis por cuadrantes (Crítico, Anomalía, Revisar, Óptimo) │
   │    ├─ Métricas de cada cuadrante                                    │
   │    └─ Tablas de instalaciones críticas y anómalas                   │
   │                                                                      │
   │ 📌 SECCIÓN 3: SERIE TEMPORAL DE EMISSION RATE                       │
   │    ├─ Gráfico de líneas con evolución temporal                      │
   │    ├─ Filtro de instalaciones y agregación temporal                 │
   │    ├─ Análisis de patrones (Intermitentes, Tendencias, Picos)       │
   │    └─ Detección automática de anomalías temporales                  │
   │                                                                      │
   │ 📌 SECCIÓN 4: INVENTARIO DE EMISIONES ACUMULADAS                    │
   │    ├─ Vista Total del Dataset vs Acumulado Mensual                  │
   │    ├─ Gráfico de barras con % del total                             │
   │    ├─ Tabla pivot mensual (si hay datos temporales)                 │
   │    └─ KPIs: Emisión total, Top 3%, Promedio, Mayor emisor          │
   │                                                                      │
   │ 📌 SECCIÓN 5: ANÁLISIS DE CONCENTRACIÓN DE METANO                   │
   │    ├─ Filtros: Mínimo mediciones, Top N, Ordenamiento               │
   │    ├─ 3 visualizaciones: Boxplot, Scatter, Barras con error         │
   │    ├─ Tabla de estadísticas por instalación                         │
   │    └─ Fallback para datasets sin Facility Name                      │
   │                                                                      │
   └─────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────┐
   │ TAB 3: 💨 ANÁLISIS DE VELOCIDAD DE VIENTO                          │
   ├─────────────────────────────────────────────────────────────────────┤
   │ • Histograma de distribución de velocidad                           │
   │ • Box plot de estadísticas                                          │
   │ • Serie temporal (si hay datos de fecha/hora)                       │
   │ • Métricas: Promedio, Máximo, Mínimo, Desv. Estándar               │
   │ • Soporte para datos de Extended y Summary                          │
   └─────────────────────────────────────────────────────────────────────┘

   ┌─────────────────────────────────────────────────────────────────────┐
   │ TAB 4: 📈 ESTADÍSTICAS DETALLADAS Y EXPORTACIÓN                    │
   ├─────────────────────────────────────────────────────────────────────┤
   │ • Histograma de distribución de CH₄                                 │
   │ • Box plot de concentración                                         │
   │ • Tabla de datos completos (scrollable)                             │
   │ • Botón de descarga CSV                                             │
   └─────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════
CARACTERÍSTICAS CLAVE
═══════════════════════════════════════════════════════════════════════════════

✅ COMPLETAMENTE RESPONSIVE: Optimizado para desktop, tablet y móvil
✅ TODAS LAS GRÁFICAS MANTIENEN: Colores, estilos, interactividad original
✅ FILTROS DINÁMICOS: Por campo, Top N, agregación temporal, métricas
✅ NAVEGACIÓN INTUITIVA: Flujo lógico de KPIs → Mapas → Análisis → Export
✅ DOCUMENTACIÓN: Comentarios técnicos en cada sección
✅ SIN PÉRDIDA DE FUNCIONALIDAD: 100% del código original preservado

═══════════════════════════════════════════════════════════════════════════════
"""

import os
import pandas as pd
import numpy as np
import streamlit as st
import folium
from streamlit_folium import st_folium
import branca.colormap as cm
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════
# 1. CONFIGURACIÓN GLOBAL Y PALETA DE COLORES
# ══════════════════════════════════════════════════════════════════════

# Paleta de colores empresarial (basada en dashboard corporativo)
ENERGY_COLORS = {
    'primary': '#1ABC9C',      # Verde turquesa principal
    'secondary': '#16A085',    # Verde turquesa oscuro
    'accent': '#48C9B0',       # Verde turquesa claro
    'success': '#27AE60',      # Verde éxito
    'warning': '#F39C12',      # Naranja advertencia
    'danger': '#E74C3C',       # Rojo peligro
    'dark': '#2C3E50',         # Azul oscuro corporativo
    'light': '#ECF0F1',        # Gris claro
    'info': '#3498DB'          # Azul información
}

# ══════════════════════════════════════════════════════════════════════
# 2. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# ══════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="🛢️ Gestión de Emisiones Fugitivas - OGMP Nivel 5",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado con paleta de energías de transición
st.markdown(f"""
<style>
    /* Hacer la app responsive y de ancho completo */
    .stApp {{
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
        max-width: 100% !important;
    }}
    
    /* Contenedor principal */
    .main {{
        background-color: rgba(255, 255, 255, 0.98);
        border-radius: 20px;
        padding: 2rem;
        max-width: 100%;
        margin: 0 auto;
    }}
    
    /* Ancho completo para el contenido */
    .block-container {{
        max-width: 100% !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
    }}
    
    /* Responsive para pantallas grandes */
    @media (min-width: 1400px) {{
        .block-container {{
            max-width: 98% !important;
            padding-left: 4rem !important;
            padding-right: 4rem !important;
        }}
    }}
    
    /* Responsive para pantallas medianas */
    @media (max-width: 1024px) {{
        .block-container {{
            padding-left: 2rem !important;
            padding-right: 2rem !important;
        }}
    }}
    
    /* Responsive para móviles */
    @media (max-width: 768px) {{
        .block-container {{
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        .main {{
            padding: 1rem;
        }}
    }}
    
    h1 {{
        color: {ENERGY_COLORS['dark']};
        font-weight: 700;
        text-align: center;
        padding: 1.5rem 0;
        font-size: clamp(1.5rem, 4vw, 2.8rem);
        background: linear-gradient(135deg, {ENERGY_COLORS['primary']} 0%, {ENERGY_COLORS['secondary']} 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    h2, h3 {{
        color: {ENERGY_COLORS['primary']};
        font-weight: 600;
    }}
    
    /* Métricas responsive */
    .stMetric {{
        background: linear-gradient(135deg, {ENERGY_COLORS['accent']} 0%, {ENERGY_COLORS['secondary']} 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }}
    
    .stMetric label {{
        font-size: clamp(0.8rem, 1.5vw, 1rem);
    }}
    
    .stMetric [data-testid="stMetricValue"] {{
        font-size: clamp(1.2rem, 2.5vw, 2rem);
    }}
    
    .metric-card {{
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-left: 5px solid {ENERGY_COLORS['primary']};
        margin: 1rem 0;
    }}
    
    /* Sidebar responsive */
    [data-testid="stSidebar"] {{
        min-width: 250px;
    }}
    
    @media (max-width: 768px) {{
        [data-testid="stSidebar"] {{
            min-width: 200px;
        }}
    }}
    
    /* Mapas y gráficas ocupan todo el ancho */
    .stPlotlyChart, iframe {{
        width: 100% !important;
    }}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 3. TÍTULO PRINCIPAL
# ══════════════════════════════════════════════════════════════════════

# Título principal con icono y estilo mejorado
st.markdown("""
<div style='text-align: center; padding: 1rem 0 2rem 0;'>
    <h1 style='margin: 0; padding: 0;'>
        🛢️ Monitoreo Ambiental de Emisiones Fugitivas en Tanques
    </h1>
    <p style='color: #7F8C8D; font-size: 1.1rem; margin-top: 0.5rem;'>
        Sistema de Análisis y Visualización de Concentraciones de Metano
    </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
# 4. CARGA Y VALIDACIÓN DE DATOS
# ══════════════════════════════════════════════════════════════════════

# Sidebar - Carga de archivos
with st.sidebar:
    st.markdown(f"## 📁 Cargar Datos")
    st.markdown("---")
    
    default_path = os.path.join("VRO", "ECP0001 - VRO Processed Report", "ECP0001 - VRO Processed Report.xlsx")
    
    uploaded = st.file_uploader("Seleccione archivo Excel (.xlsx)", type=["xlsx"], label_visibility="collapsed")
    
    use_default = False
    if not uploaded:
        st.info("⬆️ Por favor cargue un archivo Excel para iniciar el análisis")
        st.stop()

# ══════════════════════════════════════════════════════════════════════
# 4.1 FUNCIONES DE CARGA Y DETECCIÓN DE DATOS
# ══════════════════════════════════════════════════════════════════════

data = None
wind_data = None
all_sheets = {}

def find_data_sheet(xls):
    """
    Encuentra automáticamente la hoja con datos de emisiones
    Busca hojas prioritarias y detecta headers por palabras clave
    """
    priority_sheets = ['Emission Location Summary', 'Emission Location Extended', 'Facility Summary']
    
    for sheet in priority_sheets:
        if sheet in xls.sheet_names:
            df_temp = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=20)
            for idx in range(len(df_temp)):
                if any('latitude' in str(val).lower() or 'longitude' in str(val).lower() for val in df_temp.iloc[idx]):
                    return sheet, idx
    
    return xls.sheet_names[0], 0

def load_all_relevant_sheets(xls):
    """
    Carga todas las hojas relevantes del archivo Excel
    Prioriza hojas con datos de emisiones y viento
    """
    sheets_data = {}
    
    # Hojas prioritarias
    priority_sheets = ['Emission Location Summary', 'Emission Location Extended']
    
    for sheet in priority_sheets:
        if sheet in xls.sheet_names:
            try:
                df_temp = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=20)
                for idx in range(len(df_temp)):
                    if any('latitude' in str(val).lower() or 'longitude' in str(val).lower() or 'wind' in str(val).lower() for val in df_temp.iloc[idx]):
                        df = pd.read_excel(xls, sheet_name=sheet, header=idx)
                        df.columns = df.columns.str.strip()
                        sheets_data[sheet] = df
                        break
            except Exception:
                continue
    
    return sheets_data

# ══════════════════════════════════════════════════════════════════════
# 4.2 PROCESAMIENTO DE DATOS CARGADOS
# ══════════════════════════════════════════════════════════════════════

if uploaded:
    if uploaded.name.lower().endswith(".xlsx"):
        xls = pd.ExcelFile(uploaded)
        all_sheets = load_all_relevant_sheets(xls)
        sheet, header_row = find_data_sheet(xls)
        data = pd.read_excel(xls, sheet_name=sheet, header=header_row)
        
        # Cargar datos de viento de Extended si existe
        if 'Emission Location Extended' in all_sheets:
            wind_data = all_sheets['Emission Location Extended']
else:
    st.stop()

if data is None or len(data) == 0:
    st.info("👆 Por favor cargue un archivo Excel para comenzar el análisis")
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# 4.3 AUTO-DETECCIÓN DE COLUMNAS Y UNIDADES
# ══════════════════════════════════════════════════════════════════════

# Clean column names
data.columns = data.columns.str.strip()

# Auto-detect columns
def auto_detect_columns(df):
    """
    Detección automática de columnas críticas
    Mapea nombres de columnas variantes a nombres estándar
    Soporta múltiples formatos y nomenclaturas
    """
    cols_lower = {str(c).lower().strip(): c for c in df.columns}
    
    def find(keys):
        for k in keys:
            for c_low, c in cols_lower.items():
                if k in c_low:
                    return c
        return None

    detected = {
        'lat': find(["latitude", "lat", "y"]),
        'lon': find(["longitude", "lon", "lng", "long", "x"]),
        'ch4': find(["ch4", "methane", "metano", "ch_4", "concentration", "concentracion", "emission", "flux"]),
        'emission_rate': find(["emission rate", "emission_rate", "emissionrate", "rate", "tasa", "kg/h", "kg/hr"]),
        'wspd': find(["wind_speed", "wind speed", "wind_spd", "windspeed", "speed", "wspd", "velocidad", "wind speed (m/s)"]),
        'wdir': find(["wind_dir", "wind direction", "wind_direction", "winddirection", "direction", "wdir", "direccion"]),
        'date': find(["date", "fecha", "time", "hora", "datetime", "timestamp", "survey"]),
        'time': find(["time", "hora", "hour"]),
        'scan_datetime': find(["scan date time", "scan_date_time", "scandatetime", "scan date", "scan time", "utc"]),
        'location': find(["location", "id", "name", "emission location"]),
        'facility': find(["facility name", "facility_name", "facility", "instalacion", "instalación"]),
        'presidencia': find(["presidencia", "presidency", "presidente"]),
        'regional': find(["regional", "region", "área", "area"]),
        'units': None
    }
    return detected

cols = auto_detect_columns(data)
lat_col, lon_col, ch4_col = cols['lat'], cols['lon'], cols['ch4']
emission_rate_col = cols['emission_rate']
wspd_col, wdir_col = cols['wspd'], cols['wdir']
date_col, time_col = cols['date'], cols['time']
scan_datetime_col = cols['scan_datetime']
location_col = cols['location']
facility_col = cols['facility']
presidencia_col = cols['presidencia']
regional_col = cols['regional']

# Detectar unidades de CH4
ch4_units = "ppm"
if ch4_col:
    col_name_lower = str(ch4_col).lower()
    if 'kg/h' in col_name_lower or 'kg/hr' in col_name_lower:
        ch4_units = "kg/h"
    elif 'g/s' in col_name_lower:
        ch4_units = "g/s"
    elif 'ppm' in col_name_lower or 'concentration' in col_name_lower or 'flux' in col_name_lower:
        ch4_units = "ppm"

# Detectar unidades de Emission Rate
emission_rate_units = "kg/h"
if emission_rate_col:
    col_name_lower = str(emission_rate_col).lower()
    if 'kg/h' in col_name_lower or 'kg/hr' in col_name_lower:
        emission_rate_units = "kg/h"
    elif 'g/s' in col_name_lower:
        emission_rate_units = "g/s"
    elif 't/h' in col_name_lower or 'ton/h' in col_name_lower:
        emission_rate_units = "t/h"
        
# Buscar datos de viento en Extended si no hay en Summary
wind_cols_extended = None
if wind_data is not None and (not wspd_col or not wdir_col):
    wind_cols_extended = auto_detect_columns(wind_data)
    if not wspd_col and wind_cols_extended['wspd']:
        wspd_col = wind_cols_extended['wspd']
    if not wdir_col and wind_cols_extended['wdir']:
        wdir_col = wind_cols_extended['wdir']

# ══════════════════════════════════════════════════════════════════════
# 4.4 VALIDACIÓN DE COLUMNAS CRÍTICAS
# ══════════════════════════════════════════════════════════════════════

if not all([lat_col, lon_col]):
    st.error(f"❌ No se pudieron detectar columnas de latitud y/o longitud.")
    st.info(f"📋 Columnas disponibles: {', '.join([str(c) for c in data.columns])}")
    st.dataframe(data.head(10))
    st.stop()

if not ch4_col:
    # Intentar usar cualquier columna numérica como concentración
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        ch4_col = numeric_cols[0]
        st.warning(f"⚠️ Usando columna '{ch4_col}' como concentración de metano")
    else:
        st.error("❌ No se encontró columna de concentración de metano")
        st.stop()

# ══════════════════════════════════════════════════════════════════════
# 4.5 LIMPIEZA Y VALIDACIÓN DE DATOS
# ══════════════════════════════════════════════════════════════════════

# Clean data - Limpieza profunda de datos nulos y vacíos
df = data.copy()

# Remover filas completamente vacías
df = df.dropna(how='all')

# Remover filas donde las columnas críticas estén vacías
df = df.dropna(subset=[lat_col, lon_col])

# Convertir a numérico y limpiar valores inválidos
df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')
df[ch4_col] = pd.to_numeric(df[ch4_col], errors='coerce')

# Eliminar filas con coordenadas inválidas (0, NaN, o fuera de rango)
df = df[df[lat_col].notna() & df[lon_col].notna()]
df = df[(df[lat_col] != 0) | (df[lon_col] != 0)]  # Eliminar (0,0)
df = df[(df[lat_col] >= -90) & (df[lat_col] <= 90)]  # Validar latitud
df = df[(df[lon_col] >= -180) & (df[lon_col] <= 180)]  # Validar longitud

# Limpiar columna de concentración
df = df[df[ch4_col].notna()]
df = df[df[ch4_col] > 0]  # Solo valores positivos

# Limpiar columna de Emission Rate si existe
if emission_rate_col and emission_rate_col in df.columns:
    df[emission_rate_col] = pd.to_numeric(df[emission_rate_col], errors='coerce')
    # No eliminar filas por emission rate nulo, solo convertir

# Limpiar columnas de viento si existen
if wspd_col and wspd_col in df.columns:
    df[wspd_col] = pd.to_numeric(df[wspd_col], errors='coerce')
    # No eliminar filas por viento nulo, solo convertir
    
if wdir_col and wdir_col in df.columns:
    df[wdir_col] = pd.to_numeric(df[wdir_col], errors='coerce')
    # Validar dirección entre 0 y 360
    df.loc[df[wdir_col].notna(), wdir_col] = df.loc[df[wdir_col].notna(), wdir_col] % 360

# Intentar crear índice datetime
if date_col and date_col in df.columns:
    try:
        df['datetime'] = pd.to_datetime(df[date_col], errors='coerce')
        # Ordenar por fecha si existe
        if df['datetime'].notna().any():
            df = df.sort_values('datetime')
    except Exception:
        pass

# Procesar Scan Date Time (UTC) si existe
if scan_datetime_col and scan_datetime_col in df.columns:
    try:
        df['scan_datetime_parsed'] = pd.to_datetime(df[scan_datetime_col], errors='coerce', utc=True)
        # Si no hay datetime general, usar scan_datetime
        if 'datetime' not in df.columns or df['datetime'].isna().all():
            df['datetime'] = df['scan_datetime_parsed']
        # Ordenar por scan_datetime si existe
        if df['scan_datetime_parsed'].notna().any():
            df = df.sort_values('scan_datetime_parsed')
    except Exception:
        pass

# Resetear índice después de la limpieza
df = df.reset_index(drop=True)

if len(df) == 0:
    st.error("❌ No hay datos válidos después de la limpieza")
    st.info("💡 Verifique que el archivo contenga datos válidos de latitud, longitud y concentración")
    st.stop()

# Calcular métricas solo con datos válidos
try:
    max_idx = df[ch4_col].idxmax()
    max_row = df.loc[max_idx]
    min_idx = df[ch4_col].idxmin()
    min_row = df.loc[min_idx]
    avg_ch4 = df[ch4_col].mean()
    min_ch4 = df[ch4_col].min()
    max_ch4 = df[ch4_col].max()
except Exception as e:
    st.error(f"❌ Error al calcular métricas: {e}")
    st.stop()

# ══════════════════════════════════════════════════════════════════════
# 4.6 DETECCIÓN DE CAMPO Y FILTROS
# ══════════════════════════════════════════════════════════════════════

# Detectar campo automáticamente basado en Facility Name
def detect_campo(facility_name):
    """
    Detecta el campo operativo basado en el nombre de la instalación
    Retorna: "Campo Chichimene", "Campo Castilla" o "Otros Campos"
    """
    if pd.isna(facility_name):
        return "Desconocido"
    
    facility_str = str(facility_name).upper()
    
    # Palabras clave para Chichimene
    chichimene_keywords = ['CHICHIMENE', 'CHCH', 'CHI']
    # Palabras clave para Castilla
    castilla_keywords = ['CASTILLA', 'CAST', 'CAS']
    
    for keyword in chichimene_keywords:
        if keyword in facility_str:
            return "Campo Chichimene"
    
    for keyword in castilla_keywords:
        if keyword in facility_str:
            return "Campo Castilla"
    
    return "Otros Campos"

# Agregar columna de campo si existe facility_col
if facility_col and facility_col in df.columns:
    df['Campo'] = df[facility_col].apply(detect_campo)
else:
    df['Campo'] = "Desconocido"

# ══════════════════════════════════════════════════════════════════════
# 4.7 SIDEBAR - INFORMACIÓN Y FILTROS
# ══════════════════════════════════════════════════════════════════════

# Información en sidebar
with st.sidebar:
    st.markdown("---")
    
    # Filtro de campo
    st.markdown(f"## 🏭 Filtro por Campo")
    
    campos_disponibles = sorted(df['Campo'].unique().tolist())
    campo_options = ["Todos los Campos"] + campos_disponibles
    
    selected_campo = st.selectbox(
        "Seleccionar Campo:",
        options=campo_options,
        index=0,
        help="Filtrar datos por campo operativo"
    )
    
    # Aplicar filtro de campo
    if selected_campo != "Todos los Campos":
        df_filtered = df[df['Campo'] == selected_campo].copy()
        st.success(f"✅ Mostrando solo: **{selected_campo}**")
    else:
        df_filtered = df.copy()
        st.info("📊 Mostrando todos los campos")
    
    st.markdown("---")
    st.markdown(f"## 📊 Información del Análisis")
    st.metric("📍 Puntos de Emisión", f"{len(df_filtered):,}")
    st.metric("🌡️ Unidades CH₄", ch4_units)
    
    # Mostrar distribución por campo
    if len(df_filtered) > 0:
        campo_counts = df_filtered['Campo'].value_counts()
        st.markdown("### 🗂️ Por Campo:")
        for campo, count in campo_counts.items():
            st.caption(f"• {campo}: {count:,} puntos")
    
    # Calcular si hay datos de viento disponibles
    wind_available = False
    if wind_data is not None and wind_cols_extended:
        if wind_cols_extended['wspd'] and wind_cols_extended['wspd'] in wind_data.columns:
            wind_points = len(wind_data[wind_data[wind_cols_extended['wspd']].notna()])
            if wind_points > 0:
                wind_available = True
                st.metric("💨 Datos de Viento", f"{wind_points:,}")
    
    st.markdown("---")
    st.caption("🌍 Monitor Ambiental v2.0")

# Usar df_filtered en lugar de df para el resto del análisis
df = df_filtered

if selected_campo != "Todos los Campos":
    st.info(f"🏭 Visualizando datos de: **{selected_campo}** ({len(df):,} puntos)")

# ══════════════════════════════════════════════════════════════════════
# 5. SECCIÓN DE KPIs PRINCIPALES
# ══════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════
# 5.1 KPIs PRINCIPALES - EMISSION RATE (Prioridad OGMP Nivel 5)
# ═══════════════════════════════════════════════════════════════

if emission_rate_col and emission_rate_col in df.columns and facility_col and facility_col in df.columns:
    # Calcular KPIs de Emission Rate
    df_emission_kpi = df[[facility_col, emission_rate_col]].copy()
    df_emission_kpi = df_emission_kpi.dropna()
    
    if len(df_emission_kpi) > 0:
        st.markdown("---")
        st.markdown("### 🎯 Indicadores Clave de Desempeño (KPIs) - Emission Rate")
        
        # Calcular métricas
        total_emission_rate = df_emission_kpi[emission_rate_col].sum()
        avg_emission_rate = df_emission_kpi[emission_rate_col].mean()
        num_measurements = len(df_emission_kpi)
        
        # Agrupar por instalación
        emission_by_facility = df_emission_kpi.groupby(facility_col)[emission_rate_col].sum()
        max_facility_name = emission_by_facility.idxmax()
        max_facility_value = emission_by_facility.max()
        min_facility_name = emission_by_facility.idxmin()
        min_facility_value = emission_by_facility.min()
        avg_per_facility = emission_by_facility.mean()
        num_facilities = len(emission_by_facility)
        
        # Limpiar nombres
        max_facility_clean = str(max_facility_name).replace('_', ' ')
        min_facility_clean = str(min_facility_name).replace('_', ' ')
        
        # Mostrar KPIs en tarjetas con tamaño uniforme
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        with kpi1:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {ENERGY_COLORS['primary']} 0%, {ENERGY_COLORS['secondary']} 100%); 
                        padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); height: 200px;
                        display: flex; flex-direction: column; justify-content: space-between;'>
                <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>📊 EMISIÓN TOTAL</div>
                <div style='color: white; font-size: 2.5rem; font-weight: 700; line-height: 1;'>{total_emission_rate:.2f}</div>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                    {emission_rate_units}<br>
                    <span style='font-size: 0.8rem; opacity: 0.85;'>Dataset completo</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi2:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); 
                        padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); height: 200px;
                        display: flex; flex-direction: column; justify-content: space-between;'>
                <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>🔴 MAYOR EMISOR</div>
                <div style='color: white; font-size: 2.5rem; font-weight: 700; line-height: 1;'>{max_facility_value:.2f}</div>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                    {emission_rate_units}<br>
                    <span style='font-size: 0.8rem; opacity: 0.85;'>{max_facility_clean[:25]}...</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi3:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%); 
                        padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); height: 200px;
                        display: flex; flex-direction: column; justify-content: space-between;'>
                <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>🟢 MENOR EMISOR</div>
                <div style='color: white; font-size: 2.5rem; font-weight: 700; line-height: 1;'>{min_facility_value:.2f}</div>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                    {emission_rate_units}<br>
                    <span style='font-size: 0.8rem; opacity: 0.85;'>{min_facility_clean[:25]}...</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi4:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, {ENERGY_COLORS['warning']} 0%, #E67E22 100%); 
                        padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); height: 200px;
                        display: flex; flex-direction: column; justify-content: space-between;'>
                <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>📈 PROMEDIO/INSTALACIÓN</div>
                <div style='color: white; font-size: 2.5rem; font-weight: 700; line-height: 1;'>{avg_per_facility:.2f}</div>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                    {emission_rate_units}<br>
                    <span style='font-size: 0.8rem; opacity: 0.85;'>{num_facilities} instalaciones</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi5:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); 
                        padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); height: 200px;
                        display: flex; flex-direction: column; justify-content: space-between;'>
                <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>✅ MEDICIONES VÁLIDAS</div>
                <div style='color: white; font-size: 2.5rem; font-weight: 700; line-height: 1;'>{num_measurements:,}</div>
                <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                    Puntos<br>
                    <span style='font-size: 0.8rem; opacity: 0.85;'>Dataset activo</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")

# ═══════════════════════════════════════════════════════════════
# 5.2 MÉTRICAS DE CONCENTRACIÓN CH₄
# ═══════════════════════════════════════════════════════════════

st.markdown("### 🔬 Métricas de Concentración de Metano (CH₄)")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {ENERGY_COLORS['primary']} 0%, {ENERGY_COLORS['secondary']} 100%); 
                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); height: 180px;
                display: flex; flex-direction: column; justify-content: space-between;'>
        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 30px; display: flex; align-items: center;'>📊 TOTAL DE PUNTOS</div>
        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{len(df):,}</div>
        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
            Mediciones<br>
            <span style='font-size: 0.8rem; opacity: 0.85;'>Dataset completo</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
with col2:
    # Botón para pico máximo
    max_facility = str(max_row[facility_col]).replace('_', ' ') if facility_col and facility_col in max_row.index and not pd.isna(max_row[facility_col]) else "N/A"
    max_lat_val = float(max_row[lat_col])
    max_lon_val = float(max_row[lon_col])
    
    # Usar HTML para crear botón personalizado
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); 
                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                cursor: pointer; transition: transform 0.2s; height: 180px; display: flex; flex-direction: column; justify-content: space-between;'
                onmouseover="this.style.transform='translateY(-2px)'"
                onmouseout="this.style.transform='translateY(0)'">
        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 30px; display: flex; align-items: center;'>🔴 PICO MÁXIMO CH₄</div>
        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{max_ch4:.2f}</div>
        <div style='color: rgba(255,255,255,0.95); font-size: 0.95rem; font-weight: 500;'>
            {ch4_units}<br>
            <span style='font-size: 0.8rem; opacity: 0.85;'>{max_facility[:20]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗺️ Ver ubicación en mapa", key="btn_max", use_container_width=True):
        st.session_state['goto_max'] = True
        st.rerun()
        
with col3:
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, {ENERGY_COLORS['accent']} 0%, {ENERGY_COLORS['primary']} 100%); 
                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); height: 180px;
                display: flex; flex-direction: column; justify-content: space-between;'>
        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 30px; display: flex; align-items: center;'>📈 PROMEDIO CH₄</div>
        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{avg_ch4:.2f}</div>
        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
            {ch4_units}<br>
            <span style='font-size: 0.8rem; opacity: 0.85;'>Concentración media</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
with col4:
    # Botón para mínimo
    min_facility = str(min_row[facility_col]).replace('_', ' ') if facility_col and facility_col in min_row.index and not pd.isna(min_row[facility_col]) else "N/A"
    min_lat_val = float(min_row[lat_col])
    min_lon_val = float(min_row[lon_col])
    
    # Usar HTML para crear botón personalizado en celeste
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%); 
                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                cursor: pointer; transition: transform 0.2s; height: 180px; display: flex; flex-direction: column; justify-content: space-between;'
                onmouseover="this.style.transform='translateY(-2px)'"
                onmouseout="this.style.transform='translateY(0)'">
        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 30px; display: flex; align-items: center;'>🟢 MÍNIMO CH₄</div>
        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{min_ch4:.2f}</div>
        <div style='color: rgba(255,255,255,0.95); font-size: 0.95rem; font-weight: 500;'>
            {ch4_units}<br>
            <span style='font-size: 0.8rem; opacity: 0.85;'>{min_facility[:20]}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗺️ Ver ubicación en mapa", key="btn_min", use_container_width=True):
        st.session_state['goto_min'] = True
        st.rerun()

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════
# 6. NAVEGACIÓN POR TABS - ANÁLISIS DETALLADOS
# ══════════════════════════════════════════════════════════════════════

# Inicializar session state para controlar tabs
if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = 0

# Tabs for different visualizations - Mejorados visualmente
st.markdown("""
<style>
    /* Tabs más grandes y sin espacios en blanco */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        width: 100%;
        display: flex;
        justify-content: flex-start;
    }
    .stTabs [data-baseweb="tab"] {
        height: 70px;
        min-width: 280px;
        padding: 15px 35px;
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 12px 12px 0 0;
        font-size: 20px;
        font-weight: 700;
        border: 3px solid #E9ECEF;
        transition: all 0.3s ease;
        flex-grow: 1;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(26, 188, 156, 0.1);
        border-color: #1ABC9C;
        transform: translateY(-2px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1ABC9C 0%, #16A085 100%);
        color: white !important;
        border-color: #1ABC9C;
        box-shadow: 0 4px 12px rgba(26, 188, 156, 0.3);
    }
    
    /* Eliminar padding extra del contenedor de tabs */
    .stTabs {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["🗺️  Mapa Satelital", "📊  Análisis de Emisiones", "💨  Análisis de Viento", "📈  Estadísticas y Exportación"])

# ══════════════════════════════════════════════════════════════════════
# 6.1 TAB 1: MAPA SATELITAL INTERACTIVO
# ══════════════════════════════════════════════════════════════════════

with tab1:
    st.subheader("🗺️ Mapa Satelital Interactivo de Concentración de Metano")
    
    # Variables para controlar el popup automático
    open_max_popup = False
    open_min_popup = False
    
    # Mostrar mensajes cuando se hace clic en los botones
    if 'goto_max' in st.session_state and st.session_state['goto_max']:
        max_facility = str(max_row[facility_col]).replace('_', ' ') if facility_col and facility_col in max_row.index and not pd.isna(max_row[facility_col]) else "N/A"
        st.info(f"📍 Mostrando ubicación del **Pico Máximo**: {max_ch4:.2f} {ch4_units} en {max_facility}")
        center_lat = float(max_row[lat_col])
        center_lon = float(max_row[lon_col])
        zoom_level = 16
        open_max_popup = True
        st.session_state['goto_max'] = False
    elif 'goto_min' in st.session_state and st.session_state['goto_min']:
        min_facility = str(min_row[facility_col]).replace('_', ' ') if facility_col and facility_col in min_row.index and not pd.isna(min_row[facility_col]) else "N/A"
        st.success(f"📍 Mostrando ubicación del **Mínimo**: {min_ch4:.2f} {ch4_units} en {min_facility}")
        center_lat = float(min_row[lat_col])
        center_lon = float(min_row[lon_col])
        zoom_level = 16
        open_min_popup = True
        st.session_state['goto_min'] = False
    else:
        # Calcular centro del mapa con datos válidos
        center_lat = df[lat_col].median()
        center_lon = df[lon_col].median()
        zoom_level = 12
    
    center = [center_lat, center_lon]
    
    m = folium.Map(location=center, zoom_start=zoom_level, tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', attr='Esri')
    
    vmin = float(df[ch4_col].min())
    vmax = float(df[ch4_col].max())
    colormap = cm.LinearColormap([ENERGY_COLORS['success'], ENERGY_COLORS['warning'], ENERGY_COLORS['danger']], 
                                   vmin=vmin, vmax=vmax, caption='Concentración CH₄')
    colormap.add_to(m)
    
    # Iterar solo sobre filas con datos válidos
    for idx, row in df.iterrows():
        try:
            lat = float(row[lat_col])
            lon = float(row[lon_col])
            ch4 = float(row[ch4_col])
            
            # Validar que los valores sean numéricos válidos
            if pd.isna(lat) or pd.isna(lon) or pd.isna(ch4):
                continue
                
            color = colormap(ch4)
            
            popup_html = f"""
            <div style='font-family: Arial; min-width: 250px;'>
                <h4 style='color: {ENERGY_COLORS['primary']}; margin: 0;'>📍 Punto de Emisión</h4>
                <hr style='margin: 5px 0;'>
            """
            
            if facility_col and facility_col in row.index and not pd.isna(row[facility_col]):
                facility_name = str(row[facility_col]).replace('_', ' ')
                popup_html += f"<b>🏭 Instalación:</b> {facility_name}<br>"
            
            if presidencia_col and presidencia_col in row.index and not pd.isna(row[presidencia_col]):
                popup_html += f"<b>🏢 Presidencia:</b> {row[presidencia_col]}<br>"
            
            if regional_col and regional_col in row.index and not pd.isna(row[regional_col]):
                popup_html += f"<b>🌎 Regional:</b> {row[regional_col]}<br>"
            
            if location_col and location_col in row.index and not pd.isna(row[location_col]):
                popup_html += f"<b>📌 Ubicación:</b> {row[location_col]}<br>"
            
            popup_html += f"<b>🌡️ Concentración CH₄:</b> {ch4:.2f} {ch4_units}<br>"
            popup_html += f"<b>📍 Latitud:</b> {lat:.6f}<br>"
            popup_html += f"<b>📍 Longitud:</b> {lon:.6f}<br>"
            
            if wspd_col and wspd_col in row.index and not pd.isna(row[wspd_col]):
                popup_html += f"<b>💨 Velocidad viento:</b> {float(row[wspd_col]):.2f} m/s<br>"
            if wdir_col and wdir_col in row.index and not pd.isna(row[wdir_col]):
                popup_html += f"<b>🧭 Dirección viento:</b> {float(row[wdir_col]):.1f}°<br>"
            if 'datetime' in df.columns and not pd.isna(row.get('datetime')):
                popup_html += f"<b>🕒 Fecha/Hora:</b> {row['datetime']}<br>"
            popup_html += "</div>"
            
            folium.CircleMarker(
                location=[lat, lon], 
                radius=6, 
                color=color, 
                fill=True, 
                fill_color=color, 
                fill_opacity=0.7, 
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(m)
        except Exception as e:
            # Silenciosamente saltar filas con errores
            continue
    
    # Highlight max point
    try:
        max_lat = float(max_row[lat_col])
        max_lon = float(max_row[lon_col])
        max_ch4_val = float(max_row[ch4_col])
        
        # Crear popup detallado para el punto máximo
        max_popup_html = f"""
        <div style='font-family: Arial; min-width: 250px;'>
            <h4 style='color: {ENERGY_COLORS['danger']}; margin: 0;'>🔴 PICO MÁXIMO</h4>
            <hr style='margin: 5px 0;'>
        """
        
        if facility_col and facility_col in max_row.index and not pd.isna(max_row[facility_col]):
            facility_name = str(max_row[facility_col]).replace('_', ' ')
            max_popup_html += f"<b>🏭 Instalación:</b> {facility_name}<br>"
        
        if presidencia_col and presidencia_col in max_row.index and not pd.isna(max_row[presidencia_col]):
            max_popup_html += f"<b>🏢 Presidencia:</b> {max_row[presidencia_col]}<br>"
        
        if regional_col and regional_col in max_row.index and not pd.isna(max_row[regional_col]):
            max_popup_html += f"<b>🌎 Regional:</b> {max_row[regional_col]}<br>"
        
        if location_col and location_col in max_row.index and not pd.isna(max_row[location_col]):
            max_popup_html += f"<b>📍 Ubicación:</b> {max_row[location_col]}<br>"
        
        max_popup_html += f"<b>🌡️ Concentración CH₄:</b> {max_ch4_val:.2f} {ch4_units}<br>"
        max_popup_html += f"<b>📍 Latitud:</b> {max_lat:.6f}<br>"
        max_popup_html += f"<b>📍 Longitud:</b> {max_lon:.6f}<br>"
        max_popup_html += "</div>"
        
        max_popup = folium.Popup(max_popup_html, max_width=300)
        max_marker = folium.CircleMarker(
            location=[max_lat, max_lon], 
            radius=12, 
            color='black', 
            fill=True, 
            fill_color=ENERGY_COLORS['danger'], 
            fill_opacity=1, 
            popup=max_popup
        )
        max_marker.add_to(m)
        
        # Abrir popup automáticamente si se hizo clic en el botón
        if open_max_popup:
            max_popup.add_to(m)
            # Agregar JavaScript para abrir el popup automáticamente
            m.get_root().html.add_child(folium.Element(f"""
            <script>
                setTimeout(function() {{
                    var marker = document.querySelector('[style*="margin-left: -6px"][style*="margin-top: -6px"]');
                    if (marker) {{
                        marker.click();
                    }}
                }}, 500);
            </script>
            """))
    except Exception:
        pass
    
    # Highlight min point
    try:
        min_lat = float(min_row[lat_col])
        min_lon = float(min_row[lon_col])
        min_ch4_val = float(min_row[ch4_col])
        
        # Crear popup detallado para el punto mínimo
        min_popup_html = f"""
        <div style='font-family: Arial; min-width: 250px;'>
            <h4 style='color: {ENERGY_COLORS['success']}; margin: 0;'>🟢 PICO MÍNIMO</h4>
            <hr style='margin: 5px 0;'>
        """
        
        if facility_col and facility_col in min_row.index and not pd.isna(min_row[facility_col]):
            facility_name = str(min_row[facility_col]).replace('_', ' ')
            min_popup_html += f"<b>🏭 Instalación:</b> {facility_name}<br>"
        
        if presidencia_col and presidencia_col in min_row.index and not pd.isna(min_row[presidencia_col]):
            min_popup_html += f"<b>🏢 Presidencia:</b> {min_row[presidencia_col]}<br>"
        
        if regional_col and regional_col in min_row.index and not pd.isna(min_row[regional_col]):
            min_popup_html += f"<b>🌎 Regional:</b> {min_row[regional_col]}<br>"
        
        if location_col and location_col in min_row.index and not pd.isna(min_row[location_col]):
            min_popup_html += f"<b>📍 Ubicación:</b> {min_row[location_col]}<br>"
        
        min_popup_html += f"<b>🌡️ Concentración CH₄:</b> {min_ch4_val:.2f} {ch4_units}<br>"
        min_popup_html += f"<b>📍 Latitud:</b> {min_lat:.6f}<br>"
        min_popup_html += f"<b>📍 Longitud:</b> {min_lon:.6f}<br>"
        min_popup_html += "</div>"
        
        min_popup = folium.Popup(min_popup_html, max_width=300)
        min_marker = folium.CircleMarker(
            location=[min_lat, min_lon], 
            radius=12, 
            color='black', 
            fill=True, 
            fill_color='#3498DB',  # Color celeste para el mínimo
            fill_opacity=1, 
            popup=min_popup
        )
        min_marker.add_to(m)
        
        # Abrir popup automáticamente si se hizo clic en el botón
        if open_min_popup:
            min_popup.add_to(m)
            # Agregar JavaScript para abrir el popup automáticamente
            m.get_root().html.add_child(folium.Element(f"""
            <script>
                setTimeout(function() {{
                    var markers = document.querySelectorAll('[style*="margin-left: -6px"][style*="margin-top: -6px"]');
                    if (markers.length > 1) {{
                        markers[1].click();
                    }}
                }}, 500);
            </script>
            """))
    except Exception:
        pass
    
    st_folium(m, width="100%", height=700)

# ══════════════════════════════════════════════════════════════════════
# 6.2 TAB 2: ANÁLISIS INTEGRAL DE EMISIONES
# ══════════════════════════════════════════════════════════════════════

with tab2:
    st.subheader("📊 Análisis Integral de Emisiones Fugitivas")
    
    # ═══════════════════════════════════════════════════════════════
    # 6.2.1 ANÁLISIS DE TASA DE EMISIÓN (EMISSION RATE)
    # ═══════════════════════════════════════════════════════════════
    
    # Sección 1: Ranking por Emission Rate (Prioridad OGMP Nivel 5)
    if emission_rate_col and emission_rate_col in df.columns and facility_col and facility_col in df.columns:
        st.markdown("---")
        st.markdown("### 🏆 Ranking de Instalaciones por Tasa de Emisión")
        st.caption("""
        **Indicador crítico para:** Inventario GEI | Reconciliación de datos | Comparación entre tecnologías | OGMP Nivel 5 | Priorización de mitigación
        """)
        
        # Preparar datos de emission rate
        df_emission = df[[facility_col, emission_rate_col]].copy()
        df_emission = df_emission.dropna()
        
        # Reemplazar guiones bajos por espacios
        df_emission[facility_col] = df_emission[facility_col].astype(str).str.replace('_', ' ')
        
        # Calcular estadísticas por instalación
        emission_stats = df_emission.groupby(facility_col)[emission_rate_col].agg(['sum', 'mean', 'max', 'count']).round(2)
        emission_stats.columns = ['Total', 'Promedio', 'Máximo', 'Nº Mediciones']
        
        # Ordenar por Total (suma acumulada) de mayor a menor
        emission_stats = emission_stats.sort_values('Total', ascending=True)  # True para que el mayor quede arriba en barras horizontales
        
        # Filtro de top N
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            top_n_emission = st.slider(
                "Mostrar Top N instalaciones por emisión",
                min_value=5,
                max_value=min(50, len(emission_stats)),
                value=min(15, len(emission_stats)),
                help="Limitar visualización a las instalaciones con mayor tasa de emisión"
            )
        
        with col_filter2:
            metric_emission = st.selectbox(
                "Métrica a visualizar:",
                options=['Total', 'Promedio', 'Máximo'],
                index=0,
                help="Criterio de emisión a mostrar en el ranking"
            )
        
        # Filtrar top N
        emission_stats_top = emission_stats.tail(top_n_emission)  # tail porque ascending=True
        
        # Crear gráfico de barras horizontales
        fig_emission = go.Figure()
        
        # Colores basados en magnitud
        colors_emission = emission_stats_top[metric_emission]
        
        fig_emission.add_trace(go.Bar(
            y=emission_stats_top.index,
            x=emission_stats_top[metric_emission],
            orientation='h',
            marker=dict(
                color=colors_emission,
                colorscale=[[0, ENERGY_COLORS['success']], [0.5, ENERGY_COLORS['warning']], [1, ENERGY_COLORS['danger']]],
                showscale=True,
                colorbar=dict(
                    title=f"Emission<br>Rate<br>({emission_rate_units})",
                    x=1.15
                )
            ),
            text=emission_stats_top[metric_emission].apply(lambda x: f'{x:.2f}'),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Emission Rate: %{x:.2f} ' + emission_rate_units + '<extra></extra>'
        ))
        
        fig_emission.update_layout(
            title=f"🏆 Top {top_n_emission} Instalaciones - {metric_emission} Emission Rate",
            xaxis_title=f"Emission Rate ({emission_rate_units})",
            yaxis_title="Instalación",
            height=max(500, top_n_emission * 35),  # Altura dinámica según número de instalaciones
            template='plotly_white',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=False,
            margin=dict(l=250, r=150, t=80, b=80),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.05)'
            ),
            yaxis=dict(
                tickfont=dict(size=11)
            )
        )
        
        st.plotly_chart(fig_emission, use_container_width=True)
        
        # Tabla de estadísticas detalladas
        st.markdown("#### 📋 Estadísticas Detalladas por Instalación")
        emission_stats_display = emission_stats.sort_values('Total', ascending=False).copy()
        emission_stats_display.columns = [f'{col} ({emission_rate_units})' if col != 'Nº Mediciones' else col for col in emission_stats_display.columns]
        st.dataframe(emission_stats_display, use_container_width=True, height=400)
        
        # Métricas clave
        st.markdown("---")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("🏭 Total Instalaciones", f"{len(emission_stats):,}")
        with col_m2:
            st.metric("📊 Emisión Total", f"{emission_stats['Total'].sum():.2f} {emission_rate_units}")
        with col_m3:
            st.metric("📈 Emisión Promedio", f"{emission_stats['Promedio'].mean():.2f} {emission_rate_units}")
        with col_m4:
            top_emitter = emission_stats['Total'].idxmax()
            st.metric("🔴 Mayor Emisor", f"{top_emitter[:20]}...")
        
        # ═══════════════════════════════════════════════════════════════
        # 6.2.2 CORRELACIÓN EMISSION RATE VS CONCENTRACIÓN CH₄
        # ═══════════════════════════════════════════════════════════════
        
        st.markdown("---")
        st.markdown("### 🔬 Correlación: Emission Rate vs Concentración CH₄")
        st.caption("""
        **Análisis crítico para comité:** Identifica anomalías donde alta concentración no correlaciona con alta emisión, o viceversa.
        Los umbrales configurables permiten clasificar instalaciones en cuadrantes para priorización de acciones.
        """)
        
        # Preparar datos combinados
        if ch4_col and ch4_col in df.columns:
            df_correlation = df[[facility_col, emission_rate_col, ch4_col]].copy()
            df_correlation = df_correlation.dropna()
            df_correlation[facility_col] = df_correlation[facility_col].astype(str).str.replace('_', ' ')
            
            if len(df_correlation) > 0:
                
                # ═══════════════════════════════════════════════════════════════
                # CONTROLES DE UMBRALES CONFIGURABLES
                # ═══════════════════════════════════════════════════════════════
                
                st.markdown("#### ⚙️ Configuración de Umbrales para Cuadrantes")
                
                col_threshold1, col_threshold2, col_threshold3 = st.columns([2, 2, 1])
                
                with col_threshold1:
                    # Calcular valores sugeridos
                    median_ch4 = df_correlation[ch4_col].median()
                    mean_ch4 = df_correlation[ch4_col].mean()
                    percentile_75_ch4 = df_correlation[ch4_col].quantile(0.75)
                    
                    threshold_ch4 = st.number_input(
                        f"Umbral CH₄ ({ch4_units})",
                        min_value=float(df_correlation[ch4_col].min()),
                        max_value=float(df_correlation[ch4_col].max()),
                        value=float(median_ch4),
                        step=0.01,
                        help=f"Valores por encima se consideran 'Alto CH₄'. Sugeridos: Mediana={median_ch4:.2f}, Media={mean_ch4:.2f}, P75={percentile_75_ch4:.2f}"
                    )
                
                with col_threshold2:
                    # Calcular valores sugeridos
                    median_emission = df_correlation[emission_rate_col].median()
                    mean_emission = df_correlation[emission_rate_col].mean()
                    percentile_75_emission = df_correlation[emission_rate_col].quantile(0.75)
                    
                    threshold_emission = st.number_input(
                        f"Umbral Emission Rate ({emission_rate_units})",
                        min_value=float(df_correlation[emission_rate_col].min()),
                        max_value=float(df_correlation[emission_rate_col].max()),
                        value=float(median_emission),
                        step=0.01,
                        help=f"Valores por encima se consideran 'Alto Rate'. Sugeridos: Mediana={median_emission:.2f}, Media={mean_emission:.2f}, P75={percentile_75_emission:.2f}"
                    )
                
                with col_threshold3:
                    st.markdown("**Valores Sugeridos:**")
                    st.caption(f"📊 CH₄ Mediana: {median_ch4:.2f}")
                    st.caption(f"📊 Rate Mediana: {median_emission:.2f}")
                    st.caption(f"📈 CH₄ P75: {percentile_75_ch4:.2f}")
                    st.caption(f"📈 Rate P75: {percentile_75_emission:.2f}")
                
                # ═══════════════════════════════════════════════════════════════
                # SCATTER PLOT CON LÍNEAS DE UMBRAL
                # ═══════════════════════════════════════════════════════════════
                
                st.markdown("#### 📈 Scatter Plot: Concentración CH₄ vs Emission Rate")
                
                fig_correlation = px.scatter(
                    df_correlation,
                    x=ch4_col,
                    y=emission_rate_col,
                    color=facility_col,
                    hover_data={
                        facility_col: True,
                        ch4_col: ':.2f',
                        emission_rate_col: ':.2f'
                    },
                    labels={
                        ch4_col: f'Concentración CH₄ ({ch4_units})',
                        emission_rate_col: f'Emission Rate ({emission_rate_units})',
                        facility_col: 'Instalación'
                    },
                    title='Relación entre Concentración CH₄ y Tasa de Emisión por Instalación'
                )
                
                fig_correlation.update_traces(
                    marker=dict(size=10, opacity=0.7, line=dict(width=1, color='white'))
                )
                
                # Agregar líneas de umbral
                fig_correlation.add_hline(
                    y=threshold_emission, 
                    line_dash="dash", 
                    line_color="red", 
                    annotation_text=f"Umbral Rate: {threshold_emission:.2f}",
                    annotation_position="right"
                )
                
                fig_correlation.add_vline(
                    x=threshold_ch4, 
                    line_dash="dash", 
                    line_color="orange", 
                    annotation_text=f"Umbral CH₄: {threshold_ch4:.2f}",
                    annotation_position="top"
                )
                
                # Agregar anotaciones de cuadrantes
                max_ch4 = df_correlation[ch4_col].max()
                max_emission = df_correlation[emission_rate_col].max()
                
                fig_correlation.add_annotation(
                    x=threshold_ch4 + (max_ch4 - threshold_ch4) * 0.5,
                    y=threshold_emission + (max_emission - threshold_emission) * 0.5,
                    text="🔴 CRÍTICO<br>Alto CH₄ + Alto Rate",
                    showarrow=False,
                    font=dict(size=12, color="red"),
                    bgcolor="rgba(255, 0, 0, 0.1)",
                    bordercolor="red",
                    borderwidth=2,
                    borderpad=4
                )
                
                fig_correlation.update_layout(
                    height=650,
                    template='plotly_white',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.05)',
                        title_font=dict(size=14, color=ENERGY_COLORS['dark'])
                    ),
                    yaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.05)',
                        title_font=dict(size=14, color=ENERGY_COLORS['dark'])
                    ),
                    legend=dict(
                        title=dict(text='Instalación', font=dict(size=12)),
                        orientation='v',
                        yanchor='top',
                        y=1,
                        xanchor='left',
                        x=1.02,
                        bgcolor='rgba(255,255,255,0.9)',
                        bordercolor=ENERGY_COLORS['light'],
                        borderwidth=1
                    ),
                    hovermode='closest'
                )
                
                st.plotly_chart(fig_correlation, use_container_width=True)
                
                # ═══════════════════════════════════════════════════════════════
                # CLASIFICACIÓN POR CUADRANTES CON UMBRALES CONFIGURABLES
                # ═══════════════════════════════════════════════════════════════
                
                st.markdown("#### 📊 Análisis por Cuadrantes")
                
                # Clasificar por cuadrantes usando umbrales configurables
                df_correlation['Cuadrante'] = 'N/A'
                
                df_correlation.loc[
                    (df_correlation[ch4_col] >= threshold_ch4) & (df_correlation[emission_rate_col] >= threshold_emission),
                    'Cuadrante'
                ] = '🔴 Alto-Alto (Crítico)'
                
                df_correlation.loc[
                    (df_correlation[ch4_col] < threshold_ch4) & (df_correlation[emission_rate_col] >= threshold_emission),
                    'Cuadrante'
                ] = '🟠 Bajo CH₄ - Alto Rate (Anomalía)'
                
                df_correlation.loc[
                    (df_correlation[ch4_col] >= threshold_ch4) & (df_correlation[emission_rate_col] < threshold_emission),
                    'Cuadrante'
                ] = '🟡 Alto CH₄ - Bajo Rate (Revisar)'
                
                df_correlation.loc[
                    (df_correlation[ch4_col] < threshold_ch4) & (df_correlation[emission_rate_col] < threshold_emission),
                    'Cuadrante'
                ] = '🟢 Bajo-Bajo (Óptimo)'
                
                # ═══════════════════════════════════════════════════════════════
                # TARJETAS DE CUADRANTES CON CONTEO DE PUNTOS
                # ═══════════════════════════════════════════════════════════════
                
                cuadrante_counts = df_correlation['Cuadrante'].value_counts()
                total_points = len(df_correlation)
                
                col_q1, col_q2, col_q3, col_q4 = st.columns(4)
                
                with col_q1:
                    count_critico = cuadrante_counts.get('🔴 Alto-Alto (Crítico)', 0)
                    pct_critico = (count_critico / total_points * 100) if total_points > 0 else 0
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); 
                                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
                        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>🔴 CRÍTICO</div>
                        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{count_critico}</div>
                        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                            {pct_critico:.1f}% del total<br>
                            <span style='font-size: 0.8rem; opacity: 0.85;'>Alto CH₄ + Alto Rate</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_q2:
                    count_anomalia = cuadrante_counts.get('🟠 Bajo CH₄ - Alto Rate (Anomalía)', 0)
                    pct_anomalia = (count_anomalia / total_points * 100) if total_points > 0 else 0
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #F39C12 0%, #E67E22 100%); 
                                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
                        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>🟠 ANOMALÍA</div>
                        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{count_anomalia}</div>
                        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                            {pct_anomalia:.1f}% del total<br>
                            <span style='font-size: 0.8rem; opacity: 0.85;'>Bajo CH₄ + Alto Rate</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_q3:
                    count_revisar = cuadrante_counts.get('🟡 Alto CH₄ - Bajo Rate (Revisar)', 0)
                    pct_revisar = (count_revisar / total_points * 100) if total_points > 0 else 0
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #F1C40F 0%, #F39C12 100%); 
                                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
                        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>🟡 REVISAR</div>
                        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{count_revisar}</div>
                        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                            {pct_revisar:.1f}% del total<br>
                            <span style='font-size: 0.8rem; opacity: 0.85;'>Alto CH₄ + Bajo Rate</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_q4:
                    count_optimo = cuadrante_counts.get('🟢 Bajo-Bajo (Óptimo)', 0)
                    pct_optimo = (count_optimo / total_points * 100) if total_points > 0 else 0
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #27AE60 0%, #229954 100%); 
                                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
                        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>🟢 ÓPTIMO</div>
                        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{count_optimo}</div>
                        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                            {pct_optimo:.1f}% del total<br>
                            <span style='font-size: 0.8rem; opacity: 0.85;'>Bajo CH₄ + Bajo Rate</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # ═══════════════════════════════════════════════════════════════
                # TABLAS DE INSTALACIONES POR CUADRANTE
                # ═══════════════════════════════════════════════════════════════
                
                st.markdown("---")
                st.markdown("#### 🎯 Instalaciones que Requieren Atención")
                
                col_alert1, col_alert2 = st.columns(2)
                
                with col_alert1:
                    st.markdown("**🔴 Instalaciones Críticas (Alto CH₄ - Alto Rate)**")
                    criticas = df_correlation[df_correlation['Cuadrante'] == '🔴 Alto-Alto (Crítico)']
                    if len(criticas) > 0:
                        criticas_grouped = criticas.groupby(facility_col).agg({
                            emission_rate_col: 'mean',
                            ch4_col: 'mean'
                        }).round(2).reset_index()
                        criticas_grouped.columns = ['Facility Name', f'Rate Promedio ({emission_rate_units})', f'CH₄ Promedio ({ch4_units})']
                        criticas_grouped = criticas_grouped.sort_values(f'Rate Promedio ({emission_rate_units})', ascending=False)
                        st.dataframe(criticas_grouped, use_container_width=True, hide_index=True)
                    else:
                        st.info("✅ No hay instalaciones en esta categoría")
                
                with col_alert2:
                    st.markdown("**🟠 Anomalías (Bajo CH₄ - Alto Rate)**")
                    anomalias = df_correlation[df_correlation['Cuadrante'] == '🟠 Bajo CH₄ - Alto Rate (Anomalía)']
                    if len(anomalias) > 0:
                        anomalias_grouped = anomalias.groupby(facility_col).agg({
                            emission_rate_col: 'mean',
                            ch4_col: 'mean'
                        }).round(2).reset_index()
                        anomalias_grouped.columns = ['Facility Name', f'Rate Promedio ({emission_rate_units})', f'CH₄ Promedio ({ch4_units})']
                        anomalias_grouped = anomalias_grouped.sort_values(f'Rate Promedio ({emission_rate_units})', ascending=False)
                        st.dataframe(anomalias_grouped, use_container_width=True, hide_index=True)
                    else:
                        st.info("✅ No hay instalaciones en esta categoría")
            else:
                st.warning("⚠️ No hay suficientes datos para el análisis de correlación")
        else:
            st.warning("⚠️ No se encontró la columna de concentración CH₄ para análisis de correlación")
        
        # ═══════════════════════════════════════════════════════════════
        # 6.2.3 SERIE TEMPORAL DE EMISSION RATE
        # ═══════════════════════════════════════════════════════════════
        
        st.markdown("---")
        st.markdown("### 📅 Serie Temporal de Emission Rate")
        st.caption("""
        **Análisis de tendencias temporales:** Visualiza la evolución de emisiones en el tiempo. 
        Permite identificar patrones, emisiones intermitentes e incrementos vinculados a operación.
        """)
        
        # Verificar si hay datos temporales
        time_col_available = None
        if 'scan_datetime_parsed' in df.columns and df['scan_datetime_parsed'].notna().any():
            time_col_available = 'scan_datetime_parsed'
            time_label = "Scan Date Time (UTC)"
        elif 'datetime' in df.columns and df['datetime'].notna().any():
            time_col_available = 'datetime'
            time_label = "Fecha/Hora"
        
        if time_col_available:
            df_timeseries = df[[facility_col, emission_rate_col, time_col_available]].copy()
            df_timeseries = df_timeseries.dropna()
            df_timeseries[facility_col] = df_timeseries[facility_col].astype(str).str.replace('_', ' ')
            
            if len(df_timeseries) > 0:
                st.markdown("#### ⚙️ Configuración de Visualización")
                col_ts1, col_ts2 = st.columns(2)
                
                with col_ts1:
                    # Obtener lista de instalaciones ordenadas por emisión total
                    facilities_emission = df_timeseries.groupby(facility_col)[emission_rate_col].sum().sort_values(ascending=False)
                    all_facilities = facilities_emission.index.tolist()
                    
                    selected_facilities = st.multiselect(
                        "Seleccionar instalaciones a visualizar:",
                        options=all_facilities,
                        default=all_facilities[:min(10, len(all_facilities))],
                        help="Seleccione las instalaciones para visualizar su evolución temporal"
                    )
                
                with col_ts2:
                    # Opción de agregación temporal
                    time_aggregation = st.selectbox(
                        "Agregación temporal:",
                        options=['Sin agregación', 'Por día', 'Por mes'],
                        index=0,
                        help="Agrupar datos por período para reducir ruido y ver tendencias"
                    )
                
                if selected_facilities:
                    # Filtrar por instalaciones seleccionadas
                    df_ts_filtered = df_timeseries[df_timeseries[facility_col].isin(selected_facilities)].copy()
                    
                    # Aplicar agregación si se selecciona
                    if time_aggregation != 'Sin agregación':
                        freq_map = {
                            'Por día': 'D',
                            'Por mes': 'M'
                        }
                        freq = freq_map[time_aggregation]
                        
                        df_ts_filtered = df_ts_filtered.set_index(time_col_available)
                        df_ts_filtered = df_ts_filtered.groupby([facility_col, pd.Grouper(freq=freq)])[emission_rate_col].mean().reset_index()
                    
                    # Crear gráfico de serie temporal
                    fig_timeseries = px.line(
                        df_ts_filtered,
                        x=time_col_available,
                        y=emission_rate_col,
                        color=facility_col,
                        markers=True,
                        labels={
                            time_col_available: time_label,
                            emission_rate_col: f'Emission Rate ({emission_rate_units})',
                            facility_col: 'Instalación'
                        },
                        title=f'Evolución Temporal de Emission Rate - {time_aggregation}'
                    )
                    
                    fig_timeseries.update_traces(
                        line=dict(width=2.5),
                        marker=dict(size=7, line=dict(width=1, color='white'))
                    )
                    
                    fig_timeseries.update_layout(
                        height=600,
                        template='plotly_white',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            showgrid=True,
                            gridcolor='rgba(0,0,0,0.05)',
                            title_font=dict(size=14, color=ENERGY_COLORS['dark'])
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridcolor='rgba(0,0,0,0.05)',
                            title_font=dict(size=14, color=ENERGY_COLORS['dark'])
                        ),
                        legend=dict(
                            title=dict(text='Instalación', font=dict(size=12)),
                            orientation='v',
                            yanchor='top',
                            y=1,
                            xanchor='left',
                            x=1.02,
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor=ENERGY_COLORS['light'],
                            borderwidth=1
                        ),
                        hovermode='x unified'
                    )
                    
                    st.plotly_chart(fig_timeseries, use_container_width=True)
                    
                    # Análisis de patrones
                    st.markdown("#### 🔍 Análisis de Patrones Detectados")
                    
                    col_pattern1, col_pattern2, col_pattern3 = st.columns(3)
                    
                    with col_pattern1:
                        st.markdown("**🔄 Emisiones Intermitentes**")
                        st.caption("Instalaciones con alta variabilidad")
                        
                        # Calcular coeficiente de variación por instalación
                        cv_by_facility = df_ts_filtered.groupby(facility_col)[emission_rate_col].agg(['std', 'mean'])
                        cv_by_facility['CV'] = (cv_by_facility['std'] / cv_by_facility['mean'] * 100).round(1)
                        cv_by_facility = cv_by_facility.sort_values('CV', ascending=False).head(5)
                        
                        if len(cv_by_facility) > 0:
                            for facility, row in cv_by_facility.iterrows():
                                st.caption(f"• {facility[:25]}: CV={row['CV']:.1f}%")
                        else:
                            st.info("No hay datos suficientes")
                    
                    with col_pattern2:
                        st.markdown("**📈 Tendencias Crecientes**")
                        st.caption("Instalaciones con incremento sostenido")
                        
                        # Detectar tendencias (comparar primera mitad vs segunda mitad)
                        trends = []
                        for facility in selected_facilities:
                            fac_data = df_ts_filtered[df_ts_filtered[facility_col] == facility][emission_rate_col]
                            if len(fac_data) >= 4:
                                mid = len(fac_data) // 2
                                first_half = fac_data.iloc[:mid].mean()
                                second_half = fac_data.iloc[mid:].mean()
                                if first_half > 0:
                                    change_pct = ((second_half - first_half) / first_half * 100)
                                    trends.append((facility, change_pct))
                        
                        trends = sorted(trends, key=lambda x: x[1], reverse=True)[:5]
                        
                        if trends:
                            for facility, change in trends:
                                if change > 0:
                                    st.caption(f"• {facility[:25]}: +{change:.1f}%")
                        else:
                            st.info("No se detectaron tendencias")
                    
                    with col_pattern3:
                        st.markdown("**⚠️ Picos Máximos**")
                        st.caption("Eventos de emisión más altos")
                        
                        # Top 5 picos máximos
                        top_peaks = df_ts_filtered.nlargest(5, emission_rate_col)[[facility_col, emission_rate_col, time_col_available]]
                        
                        if len(top_peaks) > 0:
                            for _, row in top_peaks.iterrows():
                                date_str = row[time_col_available].strftime('%Y-%m-%d') if pd.notna(row[time_col_available]) else 'N/A'
                                st.caption(f"• {row[facility_col][:20]}: {row[emission_rate_col]:.2f} ({date_str})")
                        else:
                            st.info("No hay datos suficientes")
                else:
                    st.warning("⚠️ Por favor seleccione al menos una instalación")
            else:
                st.warning("⚠️ No hay datos temporales válidos para el análisis de serie temporal")
        else:
            st.info("ℹ️ No se encontró columna de fecha/hora (Scan Date Time UTC) para análisis temporal")
            st.caption("💡 Esta sección requiere datos temporales para mostrar evolución de emisiones")
        
        # ═══════════════════════════════════════════════════════════════
        # 6.2.4 INVENTARIO DE EMISIONES ACUMULADAS POR INSTALACIÓN
        # ═══════════════════════════════════════════════════════════════
        
        st.markdown("---")
        st.markdown("### 📊 Inventario de Emisiones Acumuladas por Instalación")
        st.caption("""
        **Reporte OGMP Ready:** Emisiones totales acumuladas por instalación para inventario GEI y reconciliación de datos
        """)
        
        # Preparar datos de emisiones acumuladas
        df_accumulated = df[[facility_col, emission_rate_col]].copy()
        df_accumulated = df_accumulated.dropna()
        df_accumulated[facility_col] = df_accumulated[facility_col].astype(str).str.replace('_', ' ')
        
        if len(df_accumulated) > 0:
            # Configuración de visualización
            st.markdown("#### ⚙️ Configuración de Visualización")
            col_view1, col_view2 = st.columns(2)
            
            with col_view1:
                view_mode = st.radio(
                    "Tipo de acumulación:",
                    options=['Total del Dataset', 'Acumulado Mensual'],
                    index=0,
                    help="Seleccione cómo visualizar las emisiones acumuladas"
                )
            
            with col_view2:
                top_n_accum = st.slider(
                    "Mostrar Top N instalaciones",
                    min_value=5,
                    max_value=min(30, df_accumulated[facility_col].nunique()),
                    value=min(15, df_accumulated[facility_col].nunique()),
                    help="Limitar visualización a principales emisores"
                )
            
            if view_mode == 'Total del Dataset':
                # Calcular acumulado total
                accumulated_total = df_accumulated.groupby(facility_col)[emission_rate_col].agg(['sum', 'mean', 'count']).round(2)
                accumulated_total.columns = ['Total Acumulado', 'Promedio', 'Nº Mediciones']
                accumulated_total = accumulated_total.sort_values('Total Acumulado', ascending=False).head(top_n_accum)
                
                # Calcular porcentaje del total global
                total_emissions = df_accumulated[emission_rate_col].sum()
                accumulated_total['% del Total'] = (accumulated_total['Total Acumulado'] / total_emissions * 100).round(1)
                
                # Gráfico de barras horizontales
                st.markdown("#### 📊 Emisión Total Acumulada por Instalación")
                
                fig_accum = go.Figure()
                
                fig_accum.add_trace(go.Bar(
                    y=accumulated_total.index[::-1],  # Invertir para que el mayor quede arriba
                    x=accumulated_total['Total Acumulado'][::-1],
                    orientation='h',
                    marker=dict(
                        color=accumulated_total['Total Acumulado'][::-1],
                        colorscale=[[0, ENERGY_COLORS['success']], [0.5, ENERGY_COLORS['warning']], [1, ENERGY_COLORS['danger']]],
                        showscale=True,
                        colorbar=dict(
                            title=f"Emisión<br>Total<br>({emission_rate_units})",
                            x=1.15
                        )
                    ),
                    text=accumulated_total['Total Acumulado'][::-1].apply(lambda x: f'{x:.1f}'),
                    textposition='outside',
                    hovertemplate='<b>%{y}</b><br>Total: %{x:.2f} ' + emission_rate_units + '<extra></extra>'
                ))
                
                fig_accum.update_layout(
                    title=f"🏭 Top {top_n_accum} Instalaciones - Emisiones Totales Acumuladas",
                    xaxis_title=f"Emisión Total Acumulada ({emission_rate_units})",
                    yaxis_title="Instalación",
                    height=max(500, top_n_accum * 35),
                    template='plotly_white',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    showlegend=False,
                    margin=dict(l=250, r=150, t=80, b=80),
                    xaxis=dict(
                        showgrid=True,
                        gridcolor='rgba(0,0,0,0.05)'
                    ),
                    yaxis=dict(
                        tickfont=dict(size=11)
                    )
                )
                
                st.plotly_chart(fig_accum, use_container_width=True)
                
                # Tabla resumen para OGMP
                st.markdown("#### 📋 Tabla Resumen - Inventario de Emisiones")
                
                accumulated_display = accumulated_total.copy()
                accumulated_display.columns = [
                    f'Total Acumulado ({emission_rate_units})',
                    f'Promedio ({emission_rate_units})',
                    'Nº Mediciones',
                    '% del Total'
                ]
                st.dataframe(accumulated_display, use_container_width=True, height=400)
                
                # Tarjetas clave del inventario
                st.markdown("---")
                st.markdown("#### 🎯 Métricas Clave del Inventario")
                
                col_inv1, col_inv2, col_inv3, col_inv4 = st.columns(4)
                
                with col_inv1:
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, {ENERGY_COLORS['primary']} 0%, {ENERGY_COLORS['secondary']} 100%); 
                                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
                        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>📊 EMISIÓN TOTAL</div>
                        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{total_emissions:.2f}</div>
                        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                            {emission_rate_units}<br>
                            <span style='font-size: 0.8rem; opacity: 0.85;'>Dataset completo</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_inv2:
                    top_3_total = accumulated_total.head(3)['Total Acumulado'].sum()
                    top_3_pct = (top_3_total / total_emissions * 100)
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); 
                                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
                        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>🔝 TOP 3 CONTRIBUCIÓN</div>
                        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{top_3_pct:.1f}%</div>
                        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                            Del total<br>
                            <span style='font-size: 0.8rem; opacity: 0.85;'>3 principales emisores</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_inv3:
                    avg_emission = accumulated_total['Total Acumulado'].mean()
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%); 
                                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
                        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>📈 PROMEDIO/INSTALACIÓN</div>
                        <div style='color: white; font-size: 2.8rem; font-weight: 700; line-height: 1;'>{avg_emission:.2f}</div>
                        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                            {emission_rate_units}<br>
                            <span style='font-size: 0.8rem; opacity: 0.85;'>Entre top {top_n_accum}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_inv4:
                    max_emitter = accumulated_total.index[0]
                    max_emitter_short = max_emitter[:22] + '...' if len(max_emitter) > 22 else max_emitter
                    
                    st.markdown(f"""
                    <div style='background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); 
                                padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                                height: 200px; display: flex; flex-direction: column; justify-content: space-between;'>
                        <div style='color: white; font-size: 0.9rem; font-weight: 700; opacity: 0.95; min-height: 36px; display: flex; align-items: center;'>🔴 MAYOR EMISOR</div>
                        <div style='color: white; font-size: 1.5rem; font-weight: 700; line-height: 1.2; min-height: 50px; display: flex; align-items: center;'>{max_emitter_short}</div>
                        <div style='color: rgba(255,255,255,0.9); font-size: 0.95rem; font-weight: 500;'>
                            {accumulated_total.loc[max_emitter, 'Total Acumulado']:.2f} {emission_rate_units}<br>
                            <span style='font-size: 0.8rem; opacity: 0.85;'>Emisión acumulada</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
            else:  # Acumulado Mensual
                # Verificar si hay datos temporales
                time_col_monthly = None
                if 'scan_datetime_parsed' in df.columns and df['scan_datetime_parsed'].notna().any():
                    time_col_monthly = 'scan_datetime_parsed'
                elif 'datetime' in df.columns and df['datetime'].notna().any():
                    time_col_monthly = 'datetime'
                
                if time_col_monthly:
                    df_monthly = df[[facility_col, emission_rate_col, time_col_monthly]].copy()
                    df_monthly = df_monthly.dropna()
                    df_monthly[facility_col] = df_monthly[facility_col].astype(str).str.replace('_', ' ')
                    
                    # Extraer año-mes
                    df_monthly['Año-Mes'] = df_monthly[time_col_monthly].dt.to_period('M').astype(str)
                    
                    # Agrupar por instalación y mes
                    monthly_accum = df_monthly.groupby([facility_col, 'Año-Mes'])[emission_rate_col].sum().reset_index()
                    monthly_accum.columns = ['Instalación', 'Mes', 'Emisión Mensual']
                    
                    # Filtrar top N instalaciones por emisión total
                    top_facilities = df_monthly.groupby(facility_col)[emission_rate_col].sum().nlargest(top_n_accum).index
                    monthly_accum_filtered = monthly_accum[monthly_accum['Instalación'].isin(top_facilities)]
                    
                    # Crear gráfico de barras agrupadas por mes
                    fig_monthly = px.bar(
                        monthly_accum_filtered,
                        x='Mes',
                        y='Emisión Mensual',
                        color='Instalación',
                        barmode='stack',
                        labels={
                            'Mes': 'Período (Año-Mes)',
                            'Emisión Mensual': f'Emisión Acumulada Mensual ({emission_rate_units})',
                            'Instalación': 'Instalación'
                        },
                        title=f'Emisiones Acumuladas Mensuales - Top {top_n_accum} Instalaciones'
                    )
                    
                    fig_monthly.update_layout(
                        height=600,
                        template='plotly_white',
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            showgrid=True,
                            gridcolor='rgba(0,0,0,0.05)',
                            tickangle=-45
                        ),
                        yaxis=dict(
                            showgrid=True,
                            gridcolor='rgba(0,0,0,0.05)'
                        ),
                        legend=dict(
                            title=dict(text='Instalación', font=dict(size=12)),
                            orientation='v',
                            yanchor='top',
                            y=1,
                            xanchor='left',
                            x=1.02,
                            bgcolor='rgba(255,255,255,0.9)',
                            bordercolor=ENERGY_COLORS['light'],
                            borderwidth=1
                        )
                    )
                    
                    st.plotly_chart(fig_monthly, use_container_width=True)
                    
                    # Tabla pivot de emisiones mensuales
                    st.markdown("#### 📅 Tabla Mensual de Emisiones por Instalación")
                    
                    pivot_monthly = monthly_accum_filtered.pivot(
                        index='Instalación',
                        columns='Mes',
                        values='Emisión Mensual'
                    ).fillna(0).round(2)
                    
                    # Agregar columna de total
                    pivot_monthly['TOTAL'] = pivot_monthly.sum(axis=1)
                    pivot_monthly = pivot_monthly.sort_values('TOTAL', ascending=False)
                    
                    st.dataframe(pivot_monthly, use_container_width=True, height=400)
                    
                else:
                    st.warning("⚠️ No se encontraron datos temporales para acumulación mensual")
                    st.info("💡 Cambie a 'Total del Dataset' para ver emisiones acumuladas")
        else:
            st.warning("⚠️ No hay datos suficientes de Emission Rate para análisis de acumulación")
        
        # ═══════════════════════════════════════════════════════════════
        # 6.2.5 ANÁLISIS DE CONCENTRACIÓN DE METANO (APOYO)
        # ═══════════════════════════════════════════════════════════════
        
        st.markdown("---")
        st.markdown("### 📈 Concentración de Metano como Apoyo a Análisis de Emisión")
        st.caption("""
        **Análisis complementario:** Las concentraciones de CH₄ respaldan la interpretación del Emission Rate.
        Permiten validar mediciones y detectar inconsistencias en los datos de emisión.
        """)
    
    else:
        if not emission_rate_col:
            st.warning("⚠️ No se encontró la columna 'Emission Rate' en los datos")
            st.info("💡 Esta sección requiere datos de tasa de emisión para el análisis")
    
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN DE CONCENTRACIÓN (MANTENIDA COMO APOYO)
    # ═══════════════════════════════════════════════════════════════
    # SECCIÓN DE CONCENTRACIÓN (MANTENIDA COMO APOYO)
    # ═══════════════════════════════════════════════════════════════
    
    # Crear gráfica por Facility Name
    if facility_col and facility_col in df.columns:
        # Preparar datos
        df_plot = df[[facility_col, ch4_col]].copy()
        df_plot = df_plot.dropna()
        
        # Reemplazar guiones bajos por espacios en Facility Name
        df_plot[facility_col] = df_plot[facility_col].astype(str).str.replace('_', ' ')
        
        # Calcular estadísticas por instalación para ordenar
        facility_stats = df_plot.groupby(facility_col)[ch4_col].agg(['mean', 'max', 'min', 'count', 'std']).round(2)
        facility_stats.columns = ['Promedio', 'Máximo', 'Mínimo', 'Nº Mediciones', 'Desv.Std']
        facility_stats = facility_stats.sort_values('Promedio', ascending=False)
        
        # Filtros interactivos
        st.markdown("### ⚙️ Filtros de Visualización")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_measurements = st.slider(
                "Mínimo de mediciones por instalación",
                min_value=1,
                max_value=int(facility_stats['Nº Mediciones'].max()),
                value=1,
                help="Filtrar instalaciones con pocas mediciones"
            )
        
        with col2:
            top_n = st.slider(
                "Mostrar Top N instalaciones",
                min_value=5,
                max_value=min(50, len(facility_stats)),
                value=min(20, len(facility_stats)),
                help="Limitar visualización a las instalaciones más relevantes"
            )
        
        with col3:
            sort_by = st.selectbox(
                "Ordenar por:",
                options=['Promedio', 'Máximo', 'Mínimo'],
                index=0,
                help="Criterio de ordenamiento"
            )
        
        # Aplicar filtros
        facility_stats_filtered = facility_stats[facility_stats['Nº Mediciones'] >= min_measurements]
        facility_stats_filtered = facility_stats_filtered.sort_values(sort_by, ascending=False).head(top_n)
        
        # Filtrar datos originales
        facilities_to_show = facility_stats_filtered.index.tolist()
        df_plot_filtered = df_plot[df_plot[facility_col].isin(facilities_to_show)]
        
        # Crear orden categórico basado en el ordenamiento
        facility_order = facility_stats_filtered.index.tolist()
        df_plot_filtered[facility_col] = pd.Categorical(
            df_plot_filtered[facility_col], 
            categories=facility_order, 
            ordered=True
        )
        df_plot_filtered = df_plot_filtered.sort_values(facility_col)
        
        st.info(f"📊 Mostrando {len(facilities_to_show)} instalaciones con {len(df_plot_filtered)} mediciones totales")
        
        # Tabs para diferentes tipos de visualización
        viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📊 Boxplot", "🎯 Scatter", "📊 Barras con Error"])
        
        with viz_tab1:
            st.markdown("#### Distribución por Instalación (Boxplot)")
            st.caption("Muestra mediana, cuartiles y dispersión de datos sin ruido visual")
            
            fig_box = go.Figure()
            
            for facility in facility_order:
                facility_data = df_plot_filtered[df_plot_filtered[facility_col] == facility][ch4_col]
                
                fig_box.add_trace(go.Box(
                    y=facility_data,
                    name=facility,
                    marker=dict(color=ENERGY_COLORS['primary']),
                    boxmean='sd',
                    hovertemplate=f'<b>{facility}</b><br>CH₄: %{{y:.2f}} {ch4_units}<extra></extra>'
                ))
            
            fig_box.update_layout(
                title=f"Distribución de Concentración por Instalación (ordenado por {sort_by})",
                xaxis_title="Instalación",
                yaxis_title=f"Concentración CH₄ ({ch4_units})",
                height=600,
                template='plotly_white',
                showlegend=False,
                xaxis=dict(
                    tickangle=-45,
                    tickfont=dict(size=10)
                ),
                margin=dict(b=150)
            )
            
            st.plotly_chart(fig_box, use_container_width=True)
        
        with viz_tab2:
            st.markdown("#### Scatter Plot por Instalación")
            st.caption("Puntos individuales sin líneas - cada punto es una medición")
            
            fig_scatter = go.Figure()
            
            # Crear posiciones numéricas para el eje X
            facility_positions = {facility: i for i, facility in enumerate(facility_order)}
            
            x_positions = [facility_positions[fac] for fac in df_plot_filtered[facility_col]]
            
            fig_scatter.add_trace(go.Scatter(
                x=x_positions,
                y=df_plot_filtered[ch4_col],
                mode='markers',
                name='Concentración CH₄',
                marker=dict(
                    size=8,
                    color=df_plot_filtered[ch4_col],
                    colorscale=[[0, ENERGY_COLORS['success']], [0.5, ENERGY_COLORS['warning']], [1, ENERGY_COLORS['danger']]],
                    showscale=True,
                    colorbar=dict(title=f"CH₄<br>({ch4_units})"),
                    opacity=0.7
                ),
                text=df_plot_filtered[facility_col],
                hovertemplate='<b>Instalación:</b> %{text}<br><b>CH₄:</b> %{y:.2f} ' + ch4_units + '<extra></extra>'
            ))
            
            fig_scatter.update_layout(
                title=f"Concentración de Metano - Scatter (ordenado por {sort_by})",
                xaxis=dict(
                    title="Instalación",
                    tickvals=list(range(len(facility_order))),
                    ticktext=facility_order,
                    tickangle=-45,
                    tickfont=dict(size=10)
                ),
                yaxis_title=f"Concentración CH₄ ({ch4_units})",
                hovermode='closest',
                height=600,
                template='plotly_white',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                margin=dict(b=150),
                showlegend=False
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        with viz_tab3:
            st.markdown("#### Barras con Error Bars")
            st.caption("Comparación de promedios con desviación estándar")
            
            fig_bar = go.Figure()
            
            fig_bar.add_trace(go.Bar(
                x=facility_order,
                y=facility_stats_filtered['Promedio'],
                error_y=dict(
                    type='data',
                    array=facility_stats_filtered['Desv.Std'],
                    visible=True
                ),
                marker=dict(
                    color=facility_stats_filtered['Promedio'],
                    colorscale=[[0, ENERGY_COLORS['success']], [0.5, ENERGY_COLORS['warning']], [1, ENERGY_COLORS['danger']]],
                    showscale=True,
                    colorbar=dict(title=f"CH₄<br>Promedio<br>({ch4_units})")
                ),
                hovertemplate='<b>%{x}</b><br>Promedio: %{y:.2f} ' + ch4_units + '<br>Desv.Std: %{error_y.array:.2f}<extra></extra>'
            ))
            
            fig_bar.update_layout(
                title=f"Concentración Promedio por Instalación (ordenado por {sort_by})",
                xaxis_title="Instalación",
                yaxis_title=f"Concentración Promedio CH₄ ({ch4_units})",
                height=600,
                template='plotly_white',
                xaxis=dict(
                    tickangle=-45,
                    tickfont=dict(size=10)
                ),
                margin=dict(b=150),
                showlegend=False
            )
            
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Mostrar estadísticas
        st.markdown("---")
        st.subheader("📊 Estadísticas por Instalación")
        facility_stats_display = facility_stats_filtered.copy()
        facility_stats_display.columns = [f'{col} ({ch4_units})' if col != 'Nº Mediciones' else col for col in facility_stats_display.columns]
        st.dataframe(facility_stats_display, use_container_width=True)
        
    else:
        st.warning("⚠️ No se encontró la columna 'Facility Name' en los datos")
        # Fallback: scatter simple
        fig_simple = px.scatter(df, y=ch4_col, title="Concentración de Metano",
                            labels={ch4_col: f"Concentración CH₄ ({ch4_units})", "index": "Índice"},
                            color=ch4_col,
                            color_continuous_scale=[[0, ENERGY_COLORS['success']], [0.5, ENERGY_COLORS['warning']], [1, ENERGY_COLORS['danger']]])
        fig_simple.update_layout(height=500, template='plotly_white')
        st.plotly_chart(fig_simple, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# 6.3 TAB 3: ANÁLISIS DE VELOCIDAD DE VIENTO
# ══════════════════════════════════════════════════════════════════════

with tab3:
    st.subheader("💨 Análisis de Velocidad de Viento")
    
    # Usar datos de viento de Extended si están disponibles
    wind_source_df = None
    wind_wspd = None
    
    if wind_data is not None and wind_cols_extended:
        if wind_cols_extended['wspd'] and wind_cols_extended['wspd'] in wind_data.columns:
            wind_source_df = wind_data
            wind_wspd = wind_cols_extended['wspd']
            st.info("📊 Usando datos de viento de hoja: Emission Location Extended")
    
    # Si no hay datos Extended, usar los de Summary
    if wind_source_df is None and wspd_col and wspd_col in df.columns:
        wind_source_df = df
        wind_wspd = wspd_col
    
    if wind_source_df is not None and wind_wspd and wind_wspd in wind_source_df.columns:
        # Filtrar solo datos válidos de viento
        wind_df = wind_source_df[[wind_wspd]].copy()
        wind_df = wind_df.dropna()
        wind_df = wind_df[(wind_df[wind_wspd] > 0) & (wind_df[wind_wspd] < 200)]  # Filtrar velocidades razonables
        
        if len(wind_df) > 0:
            # Crear dos columnas para las gráficas
            col1, col2 = st.columns(2)
            
            with col1:
                # Histograma de distribución de velocidad
                fig_hist = go.Figure()
                fig_hist.add_trace(go.Histogram(
                    x=wind_df[wind_wspd],
                    nbinsx=30,
                    marker=dict(
                        color=ENERGY_COLORS['primary'],
                        line=dict(color=ENERGY_COLORS['secondary'], width=1)
                    ),
                    name='Frecuencia'
                ))
                
                fig_hist.update_layout(
                    title="Distribución de Velocidad de Viento",
                    xaxis_title="Velocidad (m/s)",
                    yaxis_title="Frecuencia",
                    height=400,
                    template='plotly_white',
                    showlegend=False
                )
                
                st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Box plot de velocidad
                fig_box = go.Figure()
                fig_box.add_trace(go.Box(
                    y=wind_df[wind_wspd],
                    name='Velocidad',
                    marker=dict(color=ENERGY_COLORS['accent']),
                    boxmean='sd'
                ))
                
                fig_box.update_layout(
                    title="Estadísticas de Velocidad de Viento",
                    yaxis_title="Velocidad (m/s)",
                    height=400,
                    template='plotly_white',
                    showlegend=False
                )
                
                st.plotly_chart(fig_box, use_container_width=True)
            
            # Gráfica de serie temporal si hay índice temporal
            if 'DateTime' in wind_source_df.columns or 'Date' in wind_source_df.columns or 'Time' in wind_source_df.columns:
                time_col = next((col for col in ['DateTime', 'Date', 'Time'] if col in wind_source_df.columns), None)
                if time_col:
                    wind_time_df = wind_source_df[[time_col, wind_wspd]].copy()
                    wind_time_df = wind_time_df.dropna()
                    wind_time_df = wind_time_df[(wind_time_df[wind_wspd] > 0) & (wind_time_df[wind_wspd] < 200)]
                    
                    if len(wind_time_df) > 0:
                        fig_time = go.Figure()
                        fig_time.add_trace(go.Scatter(
                            x=wind_time_df[time_col],
                            y=wind_time_df[wind_wspd],
                            mode='lines',
                            line=dict(color=ENERGY_COLORS['primary'], width=2),
                            name='Velocidad'
                        ))
                        
                        fig_time.update_layout(
                            title="Serie Temporal de Velocidad de Viento",
                            xaxis_title="Fecha/Hora",
                            yaxis_title="Velocidad (m/s)",
                            height=400,
                            template='plotly_white',
                            showlegend=False
                        )
                        
                        st.plotly_chart(fig_time, use_container_width=True)
            
            # Métricas estadísticas
            st.markdown("### 📊 Estadísticas de Velocidad de Viento")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Velocidad Promedio", f"{wind_df[wind_wspd].mean():.2f} m/s")
            with col2:
                st.metric("Velocidad Máxima", f"{wind_df[wind_wspd].max():.2f} m/s")
            with col3:
                st.metric("Velocidad Mínima", f"{wind_df[wind_wspd].min():.2f} m/s")
            with col4:
                st.metric("Desviación Estándar", f"{wind_df[wind_wspd].std():.2f} m/s")
            
            st.info(f"📊 Total de datos de viento válidos: {len(wind_df)} registros")
        else:
            st.warning("⚠️ No se encontraron datos válidos de velocidad de viento")
    else:
        st.info("ℹ️ No se detectaron datos de velocidad de viento en este archivo")

# ══════════════════════════════════════════════════════════════════════
# 6.4 TAB 4: ESTADÍSTICAS DETALLADAS Y EXPORTACIÓN
# ══════════════════════════════════════════════════════════════════════

with tab4:
    st.subheader("📊 Estadísticas Detalladas y Exportación de Datos")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Distribución de Concentración CH₄")
        fig_hist = px.histogram(df, x=ch4_col, nbins=30, 
                               color_discrete_sequence=[ENERGY_COLORS['primary']],
                               labels={ch4_col: f"Concentración CH₄ ({ch4_units})"})
        fig_hist.update_layout(height=400, showlegend=False, template='plotly_white')
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 Box Plot - Distribución")
        fig_box = px.box(df, y=ch4_col, color_discrete_sequence=[ENERGY_COLORS['secondary']],
                        labels={ch4_col: f"Concentración CH₄ ({ch4_units})"})
        fig_box.update_layout(height=400, showlegend=False, template='plotly_white')
        st.plotly_chart(fig_box, use_container_width=True)
    
    st.markdown("### 📋 Tabla de Datos Completos")
    st.dataframe(df, use_container_width=True, height=400)
    
    # Botón de descarga
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Descargar datos procesados (CSV)",
        data=csv,
        file_name='datos_procesados_emisiones.csv',
        mime='text/csv',
    )

# ══════════════════════════════════════════════════════════════════════
# FUNCIÓN PLACEHOLDER: COMPARACIÓN ECOPETROL VS CARLETON
# ══════════════════════════════════════════════════════════════════════

def layout_comparacion_ecopetrol_carleton():
    """
    Módulo de comparación entre metodologías Ecopetrol y Carleton
    
    PENDIENTE: Implementar análisis comparativo de:
    - Diferencias metodológicas en cuantificación
    - Comparación de resultados por instalación
    - Análisis de desviaciones y factores de reconciliación
    - Gráficas de correlación entre ambas metodologías
    """
    st.markdown("---")
    st.markdown("### 🔬 Comparación Metodológica: Ecopetrol vs Carleton")
    
    st.info("""
    **📋 Módulo en preparación**
    
    Esta sección incluirá análisis comparativo entre las metodologías:
    - **Ecopetrol:** Mediciones y cuantificación corporativa
    - **Carleton University:** Metodología académica internacional
    
    **Análisis planificados:**
    - ✅ Comparación de tasas de emisión por instalación
    - ✅ Identificación de desviaciones sistemáticas
    - ✅ Factores de ajuste y reconciliación
    - ✅ Validación cruzada de resultados
    - ✅ Análisis estadístico de correlación
    
    *Estado: En desarrollo | Disponible próximamente*
    """)
    
    # Placeholder para gráficas futuras
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Comparación de Tasas de Emisión")
        st.caption("*Gráfico comparativo Ecopetrol vs Carleton por instalación*")
        st.image("https://via.placeholder.com/400x300/1ABC9C/FFFFFF?text=Gr%C3%A1fico+en+Desarrollo", use_container_width=True)
    
    with col2:
        st.markdown("#### 📈 Análisis de Correlación")
        st.caption("*Scatter plot con línea de tendencia y R²*")
        st.image("https://via.placeholder.com/400x300/3498DB/FFFFFF?text=An%C3%A1lisis+Pendiente", use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
# FIN DEL DASHBOARD
# ══════════════════════════════════════════════════════════════════════
