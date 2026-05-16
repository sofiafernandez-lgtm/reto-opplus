import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Opplus Smart Dashboard", layout="wide")

# CSS para estilo BBVA/Opplus
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .prioridad-card { 
        background-color: white; padding: 20px; border-radius: 10px; 
        border-left: 5px solid #004481; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #004481; font-family: 'Segoe UI'; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        # Cargamos la hoja "Modelo" del nuevo archivo OPPLUS definitivo.xlsx
        df = pd.read_excel("OPPLUS definitivo.xlsx", sheet_name="Modelo")
        df.columns = [c.strip() for c in df.columns]
        
        mediana_carga = df['CARGA OPERATIVA'].median()
        
        def clasificar_riesgo(r):
            if r > 2000: return 'Alto Riesgo'
            if r > 1000: return 'Riesgo Medio'
            return 'Bajo Riesgo'
        
        def clasificar_carga(c):
            return 'Alta Carga' if c > mediana_carga else 'Baja Carga'

        df['Nivel Riesgo'] = df['Riesgo de entrada en Mora'].apply(clasificar_riesgo)
        df['Nivel Carga'] = df['CARGA OPERATIVA'].apply(clasificar_carga)
        # Creamos la columna Cuadrante para el gráfico de barras
        df['Cuadrante'] = df['Nivel Carga'] + " / " + df['Nivel Riesgo']
        
        return df
    except:
        return None

def asignar_expedientes(data, num_gestores):
    data = data.sort_values(by="Riesgo de entrada en Mora", ascending=False)
    gestores = {f"Gestor {i+1}": 0 for i in range(num_gestores)}
    asignaciones = []
    for _, fila in data.iterrows():
        gestor_libre = min(gestores, key=gestores.get)
        asignaciones.append(gestor_libre)
        gestores[gestor_libre] += fila['CARGA OPERATIVA']
    data['Gestor_Asignado'] = asignaciones
    return data, gestores

# --- LÓGICA PRINCIPAL ---
df = load_data()

if df is not None:
    st.title("Modelo de priorización | Optimización Opplus")
    
    with st.sidebar:
        st.image("https://www.opplus.es/wp-content/uploads/2021/04/logo-opplus.png", width=150)
        n_gestores = st.slider("Gestores Disponibles", 10, 60, 39)

    df_final, cargas = asignar_expedientes(df, n_gestores)

    # ==========================================
    # SECCIÓN NUEVA: PANEL DE KPIs ESTRATÉGICOS
    # ==========================================
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric(label="📦 Volumen de Expedientes", value=len(df_final))
        
    with kpi2:
        # Cuenta cuántos casos están controlados a tiempo (<= 60 días)
        casos_bajo_limite = len(df_final[df_final['diferencia de días'] <= 60])
        # Calcula el porcentaje del total
        pct_bajo_limite = (casos_bajo_limite / len(df_final)) * 100
        
        st.metric(
            label="Índice de Cobertura (< 60 días)", 
            value=f"{pct_bajo_limite:.1f}%", 
            delta="Objetivo: > 90%", 
            delta_color="normal"
        )
        
    with kpi3:
        # Casos críticos fuera de plazo (> 60 días)
        casos_criticos = len(df_final[df_final['diferencia de días'] > 60])
        st.metric(
            label=" Alertas de Mora (> 60 días)", 
            value=casos_criticos, 
            delta="A regularizar urgente", 
            delta_color="inverse"
        )
        
    st.markdown("<br>", unsafe_allow_html=True)
    # ==========================================

    # SECCIÓN 1: GRÁFICOS ESTRATÉGICOS
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Volumen por Nivel de Riesgo")
        fig_riesgo = px.pie(
            df_final, names='Nivel Riesgo', hole=0.5,
            color='Nivel Riesgo',
            color_discrete_map={'Alto Riesgo':'#e74c3c', 'Riesgo Medio':'#f1c40f', 'Bajo
