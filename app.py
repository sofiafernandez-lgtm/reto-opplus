import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# 1. Configuración de Estilo BBVA/Opplus
st.set_page_config(page_title="Opplus - Optimizador de Prioridades", layout="wide")

# Colores corporativos (aproximados)
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
    # Asegúrate de que el archivo se llame exactamente así en GitHub
    try:
        df = pd.read_excel("OPPLUS RPLIT.xlsx",sheet_name="Modelo") # <--- CAMBIA ESTO POR EL NOMBRE DE TU ARCHIVO
        return df
    except:
        st.error("⚠️ No se encontró el archivo Excel. Asegúrate de subirlo a GitHub con el nombre correcto.")
        return None

df = load_data()
if df is not None:
    # Esto quita espacios invisibles al principio o al final de los nombres
    df.columns = [c.strip() for c in df.columns]

if df is not None:
    # 3. Sidebar - Panel de Control
    st.sidebar.image("https://www.opplus.es/wp-content/uploads/2021/04/logo-opplus.png", width=200) # Logo Opplus si tienes URL
    st.sidebar.header("⚙️ Ajustes del Modelo")
    
    n_gestores = st.sidebar.slider("Número de Gestores Disponibles", 5, 50, 39)
    k_ajuste = st.sidebar.slider("Factor de Urgencia (Ki)", 0.0001, 0.0050, 0.0002, format="%.4f")

    # 4. Lógica de Asignación Automática (Para evitar cuellos de botella)
    st.write("Columnas detectadas:", df.columns.tolist())
    
  def asignar_expedientes(data, num_gestores):
    # 1. ORDENAR: Ponemos arriba los de más riesgo
    # Usamos el nombre exacto de tu nueva hoja: "Riesgo de entrada en Mora"
    data = data.sort_values(by="Riesgo de entrada en Mora", ascending=False)
    
    # 2. PREPARAR GESTORES: Creamos una lista con los gestores (del 1 al 39, por ejemplo)
    # Todos empiezan con 0 de carga acumulada
    gestores = {f"Gestor {i+1}": 0 for i in range(num_gestores)}
    asignaciones = []

    # 3. REPARTIR: Vamos uno a uno
    for _, fila in data.iterrows():
        # Buscamos quién es el gestor que menos trabajo tiene acumulado en ese momento
        gestor_libre = min(gestores, key=gestores.get)
        
        # Le asignamos el expediente
        asignaciones.append(gestor_libre)
        
        # Le sumamos la "CARGA OPERATIVA" de ese expediente a su cuenta personal
        # Usamos el nombre exacto: "CARGA OPERATIVA"
        gestores[gestor_libre] += fila['CARGA OPERATIVA']
        
    # 4. RESULTADO: Guardamos quién es el dueño de cada fila
    data['Gestor_Asignado'] = asignaciones
    return data, gestores
      
    df_final, cargas = asignar_expedientes(df, n_gestores)

    # 5. Visualización de KPIs (Cuadros superiores)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Expedientes", len(df_final))
    
    with col2:
        # KPI del concurso: Minimizar expedientes > 60 días
        # En tu excel parece ser la columna 'diferencia de'
        casos_criticos = len(df_final[df_final['diferencia de'] > 60])
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
        st.subheader("Balanceo de Carga (Evitando Cuellos de Botella)")
        # Creamos el gráfico de barras para ver que todos trabajan lo mismo
        fig_carga = px.bar(
            x=list(cargas.keys()), 
            y=list(cargas.values()),
            labels={'x': 'Gestores', 'y': 'Carga Operativa Acumulada'},
            color=list(cargas.values()),
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig_carga, use_container_width=True)

    with row1_col2:
        st.subheader("Riesgo de Exceder los 60 días")
        # Histograma de antigüedad
        fig_dias = px.histogram(
            df_final, 
            x="diferencia de", 
            nbins=30,
            color_discrete_sequence=[COLOR_AZUL_BBVA]
        )
        fig_dias.add_vline(x=60, line_dash="dash", line_color="red", annotation_text="Límite Mora")
        st.plotly_chart(fig_dias, use_container_width=True)

    # 7. Tabla Detallada
    st.subheader("Listado de Trabajo Priorizado")
    # Mostramos las columnas más importantes para que el jurado vea la lógica
    columnas_mostrar = ['Gestor_Asignado', 'Riesgo de entrada en Mora', 'CARGA OPERATIVA', 'diferencia de días', 'Deuda actual']
    st.dataframe(df_final[columnas_mostrar].style.background_gradient(subset=['Riesgo de entrada en Mora'], cmap='Reds'), use_container_width=True)

else:
    st.info("💡 Por favor, sube el archivo Excel para activar el dashboard.")
