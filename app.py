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

# Función simplificada: Lee directamente los datos originales sin factores exponenciales
def process_data(umbral_alto, umbral_medio):
    try:
        # Lee el archivo subido
        df = pd.read_excel("OPPLUS mod1.xlsx", sheet_name="Modelo")
        df.columns = [c.strip() for c in df.columns]
        
        # Redondeamos el riesgo original del Excel para que se vea limpio
        df['Riesgo de entrada en Mora'] = df['Riesgo de entrada en Mora'].round(0)
        
        mediana_carga = df['CARGA OPERATIVA'].median()
        
        def clasificar_riesgo(r):
            if r > umbral_alto: return 'Alto Riesgo'
            if r > umbral_medio: return 'Riesgo Medio'
            return 'Bajo Riesgo'
        
        def clasificar_carga(c):
            return 'Alta Carga' if c > mediana_carga else 'Baja Carga'

        df['Nivel Riesgo'] = df['Riesgo de entrada en Mora'].apply(clasificar_riesgo)
        df['Nivel Carga'] = df['CARGA OPERATIVA'].apply(clasificar_carga)
        df['Cuadrante'] = df['Nivel Carga'] + " / " + df['Nivel Riesgo']
        
        return df
    except Exception as e:
        st.error(f"Error procesando fórmulas: {e}")
        return None

def asignar_expedientes(data, num_gestores):
    # Ordenamos el censo basándonos estrictamente en el riesgo del Excel
    data = data.sort_values(by="Riesgo de entrada en Mora", ascending=False)
    
    # Estructura para controlar la carga, minutos de comunicación y volumen por gestor
    gestores = {f"Gestor {i+1}": {"carga": 0, "minutos": 0, "expedientes_totales": 0} for i in range(num_gestores)}
    asignaciones = []
    
    for _, fila in data.iterrows():
        # Buscamos el gestor óptimo: primero por menor cantidad de minutos, y en caso de empate por menor carga
        gestor_libre = min(
            gestores.keys(), 
            key=lambda g: (gestores[g]["minutos"], gestores[g]["carga"])
        )
        
        asignaciones.append(gestor_libre)
        
        # Sumamos los criterios a la mochila del gestor elegido
        gestores[gestor_libre]["carga"] += fila['CARGA OPERATIVA']
        gestores[gestor_libre]["minutos"] += fila['T(min) de comunicación']
        gestores[gestor_libre]["expedientes_totales"] += 1
        
    data['Gestor_Asignado'] = asignaciones
    return data, gestores

# --- PANEL DE CONTROL INTERACTIVO (SIDEBAR) ---
with st.sidebar:
    st.markdown("### ⚙️ Parámetros del Modelo")
    n_gestores = st.slider("Gestores Disponibles", 10, 60, 39)
    
    st.markdown("---")
    st.markdown("### 🎯 Reglas de Negocio")
    u_alto = st.number_input("Mínimo para 'Alto Riesgo'", min_value=500, max_value=100000, value=3000, step=500)
    u_medio = st.number_input("Mínimo para 'Riesgo Medio'", min_value=100, max_value=49999, value=1500, step=100)
    dias_kpi = st.slider("Plazo crítico de control (Días)", 15, 90, 60, step=5)

# --- LÓGICA PRINCIPAL ---
df = process_data(u_alto, u_medio)

if df is not None:
    st.title("Modelo de priorización | Optimización Opplus")

    df_final, estadísticas_gestores = asignar_expedientes(df, n_gestores)

    # =========================================================
    # SECCIÓN: PANEL DE KPIs ESTRATÉGICOS (MÉTRICAS EN FILA)
    # =========================================================
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    with kpi1:
        st.metric(label="📦 Volumen de Expedientes", value=len(df_final))
        
    with kpi2:
        casos_bajo_limite = len(df_final[df_final['diferencia de días'] <= dias_kpi])
        pct_bajo_limite = (casos_bajo_limite / len(df_final)) * 100
        st.metric(
            label=f"⏱️ Índice de Cobertura (< {dias_kpi} días)", 
            value=f"{pct_bajo_limite:.1f}%"
        )
        
    with kpi3:
        casos_criticos = len(df_final[df_final['diferencia de días'] > dias_kpi])
        st.metric(
            label=f"🚨 Alertas de Mora (> {dias_kpi} días)", 
            value=casos_criticos
        )

    with kpi4:
        media_tiempo = df_final['T(min) de comunicación'].mean()
        st.metric(
            label="📞 Tiempo Medio de Comunicación", 
            value=f"{media_tiempo:.1f} min"
        )
        
    st.markdown("<br>", unsafe_allow_html=True)

    # SECCIÓN 1: GRÁFICOS ESTRATÉGICOS
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader
