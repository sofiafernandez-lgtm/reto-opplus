import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración de página
st.set_page_config(page_title="Opplus Strategy Dashboard", layout="wide")

# CSS para mejorar el aspecto
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #004481; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("OPPLUS RPLIT.xlsx", sheet_name="Modelo")
        df.columns = [c.strip() for c in df.columns]
        # Clasificamos el Riesgo
        def clasificar_riesgo(r):
            if r > 2000: return 'Alto Riesgo'
            if r > 1000: return 'Riesgo Medio'
            return 'Bajo Riesgo'
        
        # Clasificamos la Carga
        def clasificar_carga(c):
            return 'Carga Alta' if c > df['CARGA OPERATIVA'].median() else 'Carga Baja'

        df['Nivel Riesgo'] = df['Riesgo de entrada en Mora'].apply(clasificar_riesgo)
        df['Nivel Carga'] = df['CARGA OPERATIVA'].apply(clasificar_carga)
        
        # Creamos los Cuadrantes
        def asignar_cuadrante(row):
            return f"{row['Nivel Carga']} / {row['Nivel Riesgo']}"
        df['Cuadrante'] = df.apply(asignar_cuadrante, axis=1)
        
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
    st.title("📊 Panel de Control Estratégico | Reto Opplus")
    
    # Sidebar
    with st.sidebar:
        st.image("https://www.opplus.es/wp-content/uploads/2021/04/logo-opplus.png", width=150)
        n_gestores = st.slider("Gestores disponibles", 10, 60, 39)
        st.markdown("---")
        st.write("### Definición de Umbrales")
        st.caption("Alto Riesgo: > 2000 pts")
        st.caption("Carga Alta: > Mediana")

    df_final, cargas = asignar_expedientes(df, n_gestores)

    # Gráficos Superiores
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🌡️ Distribución de Riesgo (%)")
        # Gráfico de tarta con colores específicos
        fig_riesgo = px.pie(
            df_final, names='Nivel Riesgo', 
            color='Nivel Riesgo',
            color_discrete_map={'Alto Riesgo':'#e74c3c', 'Riesgo Medio':'#f1c40f', 'Bajo Riesgo':'#2ecc71'},
            hole=0.5
        )
        st.plotly_chart(fig_riesgo, use_container_width=True)

    with col_b:
        st.subheader("⚖️ Matriz Carga vs Riesgo (Nº Casos)")
        # Gráfico de barras de los cuadrantes solicitados
        cuadrantes_stats = df_final['Cuadrante'].value_counts().reset_index()
        fig_cuadrantes = px.bar(
            cuadrantes_stats, x='Cuadrante', y='count',
            color='Cuadrante',
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        st.plotly_chart(fig_cuadrantes, use_container_width=True)

    st.markdown("---")
    
    # Sección de Análisis de Dispersión (Muy profesional)
    st.subheader("🔍 Análisis Detallado de Expedientes")
    fig_scatter = px.scatter(
        df_final, 
        x="CARGA OPERATIVA", 
        y="Riesgo de entrada en Mora",
        color="Nivel Riesgo",
        size="Deuda actual",
        hover_data=['Gestor_Asignado', 'Tipo de préstamo '],
        color_discrete_map={'Alto Riesgo':'#e74c3c', 'Riesgo Medio':'#f1c40f', 'Bajo Riesgo':'#2ecc71'},
        title="Cada punto es un cliente (el tamaño es la deuda)"
    )
    # Añadimos líneas de cuadrante
    fig_scatter.add_hline(y=1500, line_dash="dot", annotation_text="Umbral Crítico")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Tabla Final
    st.subheader("📋 Lista de Asignación Final")
    st.dataframe(
        df_final[['Gestor_Asignado', 'Nivel Riesgo', 'Cuadrante', 'Deuda actual', 'CARGA OPERATIVA']],
        use_container_width=True
    )
else:
    st.error("No se pudo cargar el archivo. Verifica que se llame 'OPPLUS RPLIT.xlsx' y tenga la hoja 'Modelo'.")
