import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. Configuración de Estilo BBVA/Opplus
st.set_page_config(page_title="Opplus - Optimizador de Prioridades", layout="wide")

# Colores corporativos
COLOR_AZUL_BBVA = "#004481"

st.markdown(f"""
    <style>
    .main {{ background-color: #f4f7f9; }}
    .stMetric {{ background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }}
    </style>
    """, unsafe_allow_html=True)

st.title("Sistema de Optimización de Expedientes | Reto Opplus")

# 2. Cargar Datos
@st.cache_data
def load_data():
    try:
        # Cargamos la hoja "Modelo" que es la que tiene los datos unificados
        df = pd.read_excel("OPPLUS RPLIT.xlsx", sheet_name="Modelo")
        return df
    except Exception as e:
        st.error(f"⚠️ Error al cargar el Excel: {e}")
        return None

# Función de Motor de Asignación (Ahora correctamente alineada)
def asignar_expedientes(data, num_gestores):
    # 1. ORDENAR: Riesgo de mayor a menor
    data = data.sort_values(by="Riesgo de entrada en Mora", ascending=False)
    
    # 2. PREPARAR GESTORES
    gestores = {f"Gestor {i+1}": 0 for i in range(num_gestores)}
    asignaciones = []

    # 3. REPARTIR
    for _, fila in data.iterrows():
        gestor_libre = min(gestores, key=gestores.get)
        asignaciones.append(gestor_libre)
        # Sumamos la carga operativa
        gestores[gestor_libre] += fila['CARGA OPERATIVA']
        
    data['Gestor_Asignado'] = asignaciones
    return data, gestores

# --- EJECUCIÓN DEL CUERPO PRINCIPAL ---
df = load_data()

if df is not None:
    # Limpieza de nombres de columnas
    df.columns = [c.strip() for c in df.columns]

    # Sidebar
    st.sidebar.image("https://www.opplus.es/wp-content/uploads/2021/04/logo-opplus.png", width=200)
    st.sidebar.header("⚙️ Ajustes del Modelo")
    
    n_gestores = st.sidebar.slider("Número de Gestores Disponibles", 5, 50, 39)
    
    # Ejecutar la lógica
    df_final, cargas = asignar_expedientes(df, n_gestores)

    # 5. Visualización de KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Expedientes", len(df_final))
    
    with col2:
        # Usamos el nombre real de tu columna: 'diferencia de días'
        casos_criticos = len(df_final[df_final['diferencia de días'] > 60])
        st.metric("Casos Críticos (>60 días)", casos_criticos, delta="Objetivo: 0", delta_color="inverse")

    with col3:
        promedio_carga = round(sum(cargas.values()) / n_gestores, 2)
        st.metric("Carga Media por Gestor", promedio_carga)
        
    with col4:
        st.metric("Gestores Activos", n_gestores)

    st.divider()

    # 6. Gráficos de Impacto
    row1_col1, row1_col2 = st.columns(2)

    with row1_col1:
        st.subheader("Balanceo de Carga entre Gestores")
        fig_carga = px.bar(
            x=list(cargas.keys()), 
            y=list(cargas.values()),
            labels={'x': 'Gestores', 'y': 'Carga Total Acumulada'},
            color=list(cargas.values()),
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_carga, use_container_width=True)

    with row1_col2:
        st.subheader("Distribución por Antigüedad")
        fig_dias = px.histogram(
            df_final, 
            x="diferencia de días", 
            nbins=30,
            color_discrete_sequence=[COLOR_AZUL_BBVA]
        )
        fig_dias.add_vline(x=60, line_dash="dash", line_color="red", annotation_text="Límite 60 días")
        st.plotly_chart(fig_dias, use_container_width=True)

    # 7. Tabla Detallada
    st.subheader("Listado de Trabajo Priorizado (Vista Gestor)")
    columnas_mostrar = ['Gestor_Asignado', 'Riesgo de entrada en Mora', 'CARGA OPERATIVA', 'diferencia de días', 'Deuda actual']
    st.dataframe(df_final[columnas_mostrar].style.background_gradient(subset=['Riesgo de entrada en Mora'], cmap='Reds'), use_container_width=True)

else:
    st.info("💡 Esperando archivo Excel...")
