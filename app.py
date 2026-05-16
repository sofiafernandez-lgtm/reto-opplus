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
        # Cargamos la hoja "Modelo"
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

    # SECCIÓN 1: GRÁFICOS ESTRATÉGICOS
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Volumen por Nivel de Riesgo")
        fig_riesgo = px.pie(
            df_final, names='Nivel Riesgo', hole=0.5,
            color='Nivel Riesgo',
            color_discrete_map={'Alto Riesgo':'#e74c3c', 'Riesgo Medio':'#f1c40f', 'Bajo Riesgo':'#2ecc71'}
        )
        st.plotly_chart(fig_riesgo, use_container_width=True)

    with col_b:
        st.subheader("Matriz Carga vs Riesgo")
        # Recuperamos el gráfico de barras por cuadrantes
        cuadrantes_stats = df_final['Cuadrante'].value_counts().reset_index()
        cuadrantes_stats.columns = ['Cuadrante', 'count']
        fig_cuadrantes = px.bar(
            cuadrantes_stats, x='Cuadrante', y='count',
            color='Cuadrante',
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_cuadrantes, use_container_width=True)

    st.markdown("---")

    # SECCIÓN 2: LISTAS TÁCTICAS DE PRIORIDAD
    st.header("Listas de Asignación Inmediata")
    
    lp1, lp2 = st.columns(2)

    with lp1:
        st.markdown('<div class="prioridad-card">', unsafe_allow_html=True)
        st.subheader("Lista 1: Carga Alta / Riesgo Alto")
        st.caption("Casos críticos que requieren mayor tiempo de gestión")
        
        l1 = df_final[(df_final['Nivel Carga'] == 'Alta Carga') & (df_final['Nivel Riesgo'] == 'Alto Riesgo')]
        l1 = l1.sort_values(by="Riesgo de entrada en Mora", ascending=False)
        
        if not l1.empty:
            for _, fila in l1.head(15).iterrows(): # Mostramos los 15 más urgentes
                st.write(f"📄 **Exp. {fila['Nº de cliente']}** | Riesgo: `{int(fila['Riesgo de entrada en Mora'])}` | 👤 `{fila['Gestor_Asignado']}`")
        else:
            st.write("✅ Sin casos en este cuadrante.")
        st.markdown('</div>', unsafe_allow_html=True)

    with lp2:
        st.markdown('<div class="prioridad-card" style="border-left: 5px solid #f1c40f;">', unsafe_allow_html=True)
        st.subheader("Lista 2: Carga Baja / Riesgo Alto")
        st.caption("Prioridad 'Quick Win': Alta peligrosidad, baja dificultad")
        
        l2 = df_final[(df_final['Nivel Carga'] == 'Baja Carga') & (df_final['Nivel Riesgo'] == 'Alto Riesgo')]
        l2 = l2.sort_values(by="Riesgo de entrada en Mora", ascending=False)
        
        if not l2.empty:
            for _, fila in l2.head(15).iterrows():
                st.write(f"📄 **Exp. {fila['Nº de cliente']}** | Riesgo: `{int(fila['Riesgo de entrada en Mora'])}` | 👤 `{fila['Gestor_Asignado']}`")
        else:
            st.write("✅ Sin casos en este cuadrante.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    
    # SECCIÓN 3: TABLA GENERAL
    st.subheader("📋 Censo Completo de Asignaciones")
    st.dataframe(
        df_final[['Nº de cliente', 'Gestor_Asignado', 'Cuadrante', 'Deuda actual', 'diferencia de días']],
        use_container_width=True
    )

else:
    st.error("Archivo no encontrado o formato incorrecto.")
