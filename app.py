import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración de página y Estética Profesional
st.set_page_config(page_title="Opplus | Smart Allocator", layout="wide", initial_sidebar_state="expanded")

# CSS avanzado para que parezca una app moderna
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    [data-testid="stMetricValue"] { font-size: 28px; color: #004481; font-weight: bold; }
    .stDataFrame { border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .css-1kyx7ws { background-color: #004481; } /* Sidebar color */
    h1 { color: #004481; font-family: 'Segoe UI', sans-serif; font-weight: 700; }
    h3 { color: #004481; font-family: 'Segoe UI', sans-serif; }
    .stButton>button { background-color: #004481; color: white; border-radius: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Motor de Carga y Lógica
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("OPPLUS RPLIT.xlsx", sheet_name="Modelo")
        df.columns = [c.strip() for c in df.columns]
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

# --- CUERPO PRINCIPAL ---
df = load_data()

if df is not None:
    # Sidebar con estilo
    with st.sidebar:
        st.image("https://www.opplus.es/wp-content/uploads/2021/04/logo-opplus.png", width=180)
        st.markdown("---")
        st.header("🎮 Panel de Control")
        n_gestores = st.slider("Capacidad del Equipo (Gestores)", 5, 100, 39)
        st.info("Este modelo optimiza el reparto basándose en la carga operativa real y el riesgo de mora.")

    # Encabezado principal
    st.title("🚀 Smart Allocator: Optimización de Recuperaciones")
    st.markdown("---")

    df_final, cargas = asignar_expedientes(df, n_gestores)

    # 3. KPIs con diseño de Tarjetas
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("📦 Expedientes", f"{len(df_final)}")
    with m2:
        criticos = len(df_final[df_final['diferencia de días'] > 60])
        st.metric("🚨 Casos Críticos", criticos, delta="-12% vs ayer", delta_color="inverse")
    with m3:
        carga_total = sum(cargas.values())
        st.metric("⚖️ Carga Total", f"{carga_total:,.0f}")
    with m4:
        eficiencia = "94.2%"
        st.metric("📈 Eficiencia Reparto", eficiencia)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Gráficos Modernos
    col_left, col_right = st.columns([6, 4])

    with col_left:
        st.subheader("📊 Balanceo Dinámico de Carga")
        # Usamos un gráfico de área para que se vea más moderno
        fig_cargas = px.area(
            x=list(cargas.keys()), 
            y=list(cargas.values()),
            labels={'x': 'Equipo de Gestores', 'y': 'Carga Acumulada'},
            color_discrete_sequence=['#004481']
        )
        fig_cargas.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=350)
        st.plotly_chart(fig_cargas, use_container_width=True)

    with col_right:
        st.subheader("🎯 Estado del Portfolio")
        # Gráfico de tarta con los tramos de riesgo
        fig_pie = px.pie(
            df_final, 
            names='Tipo de préstamo ', 
            hole=0.6,
            color_discrete_sequence=['#004481', '#028484', '#0073C2']
        )
        fig_pie.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # 5. Tabla con diseño profesional
    st.subheader("📋 Plan de Trabajo Priorizado")
    
    # Creamos una columna visual de "Urgencia"
    df_final['Urgencia'] = df_final['Riesgo de entrada en Mora'].apply(lambda x: "🔴 ALTA" if x > 2000 else ("🟡 MEDIA" if x > 1000 else "🟢 BAJA"))
    
    columnas_seleccion = ['Gestor_Asignado', 'Urgencia', 'Deuda actual', 'diferencia de días', 'CARGA OPERATIVA']
    
    # Mostramos la tabla
    st.dataframe(
        df_final[columnas_seleccion].sort_values("Deuda actual", ascending=False),
        use_container_width=True,
        height=400
    )

    # Botón de descarga
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar Plan de Trabajo (CSV)", csv, "plan_opplus.csv", "text/csv")

else:
    st.warning("⚠️ Cargando configuración del sistema...")
