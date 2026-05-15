import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración y Estilo
st.set_page_config(page_title="Opplus Strategy Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .prioridad-card { 
        background-color: white; padding: 20px; border-radius: 10px; 
        border-left: 5px solid #004481; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #004481; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("OPPLUS RPLIT.xlsx", sheet_name="Modelo")
        df.columns = [c.strip() for c in df.columns]
        
        # Clasificaciones para lógica de negocio
        mediana_carga = df['CARGA OPERATIVA'].median()
        
        def clasificar_riesgo(r):
            if r > 2000: return 'Alto Riesgo'
            if r > 1000: return 'Riesgo Medio'
            return 'Bajo Riesgo'
        
        def clasificar_carga(c):
            return 'Alta Carga' if c > mediana_carga else 'Baja Carga'

        df['Nivel Riesgo'] = df['Riesgo de entrada en Mora'].apply(clasificar_riesgo)
        df['Nivel Carga'] = df['CARGA OPERATIVA'].apply(clasificar_carga)
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

# --- EJECUCIÓN ---
df = load_data()

if df is not None:
    st.title("📊 Panel Estratégico y Listas de Prioridad | Opplus")
    
    with st.sidebar:
        st.image("https://www.opplus.es/wp-content/uploads/2021/04/logo-opplus.png", width=150)
        n_gestores = st.sidebar.slider("Gestores", 10, 60, 39)

    df_final, cargas = asignar_expedientes(df, n_gestores)

    # Gráficos (Mantenemos lo anterior)
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🌡️ Distribución de Riesgo")
        fig_riesgo = px.pie(df_final, names='Nivel Riesgo', hole=0.5,
                            color='Nivel Riesgo',
                            color_discrete_map={'Alto Riesgo':'#e74c3c', 'Riesgo Medio':'#f1c40f', 'Bajo Riesgo':'#2ecc71'})
        st.plotly_chart(fig_riesgo, use_container_width=True)
    with col_b:
        st.subheader("⚖️ Carga por Gestor")
        fig_cargas = px.bar(x=list(cargas.keys()), y=list(cargas.values()), color_discrete_sequence=['#004481'])
        st.plotly_chart(fig_cargas, use_container_width=True)

    st.divider()

    # --- NUEVAS LISTAS DE PRIORIDAD ---
    st.header("🔥 Listas de Prioridad Crítica")
    st.info("Estas listas muestran los expedientes que deben atenderse de forma inmediata según su perfil de carga y riesgo.")

    lp1, lp2 = st.columns(2)

    with lp1:
        st.markdown('<div class="prioridad-card">', unsafe_allow_html=True)
        st.subheader("🔴 Lista 1: Alta Carga y Alto Riesgo")
        st.write("*Casos complejos que requieren atención experta inmediata*")
        
        # Filtro: Carga Alta Y Riesgo Alto
        l1 = df_final[(df_final['Nivel Carga'] == 'Alta Carga') & (df_final['Nivel Riesgo'] == 'Alto Riesgo')]
        l1 = l1.sort_values(by="Riesgo de entrada en Mora", ascending=False)
        
        if not l1.empty:
            for _, fila in l1.iterrows():
                st.write(f"📍 **Expediente {fila['Nº de cliente']}** (Riesgo: {int(fila['Riesgo de entrada en Mora'])}) → Asignado a: `{fila['Gestor_Asignado']}`")
        else:
            st.write("✅ No hay expedientes en este cuadrante.")
        st.markdown('</div>', unsafe_allow_html=True)

    with lp2:
        st.markdown('<div class="prioridad-card" style="border-left: 5px solid #f1c40f;">', unsafe_allow_html=True)
        st.subheader("⚡ Lista 2: Baja Carga y Alto Riesgo")
        st.write("*'Quick wins': Casos peligrosos pero rápidos de gestionar*")
        
        # Filtro: Carga Baja Y Riesgo Alto
        l2 = df_final[(df_final['Nivel Carga'] == 'Baja Carga') & (df_final['Nivel Riesgo'] == 'Alto Riesgo')]
        l2 = l2.sort_values(by="Riesgo de entrada en Mora", ascending=False)
        
        if not l2.empty:
            for _, fila in l2.iterrows():
                st.write(f"📍 **Expediente {fila['Nº de cliente']}** (Riesgo: {int(fila['Riesgo de entrada en Mora'])}) → Asignado a: `{fila['Gestor_Asignado']}`")
        else:
            st.write("✅ No hay expedientes en este cuadrante.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    st.subheader("📋 Tabla Maestra de Asignaciones")
    st.dataframe(df_final[['Nº de cliente', 'Gestor_Asignado', 'Nivel Riesgo', 'Nivel Carga', 'Deuda actual']], use_container_width=True)

else:
    st.error("Error al cargar el archivo. Comprueba que el Excel esté en el repositorio.")
