import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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

# Función modificada para recalcular de forma ultrasensible
def process_data(umbral_alto, umbral_medio, exp_deuda, exp_tiempo):
    try:
        df = pd.read_excel("OPPLUS definitivo.xlsx", sheet_name="Modelo")
        df.columns = [c.strip() for c in df.columns]
        
        # --- RECALCULO DE IMPACTO MATEMÁTICO ---
        # Calculamos las medias para normalizar
        deuda_media = df['Deuda actual'].mean() if df['Deuda actual'].mean() > 0 else 1000
        dias_medios = df['diferencia de días'].mean() if df['diferencia de días'].mean() > 0 else 30
        
        # Si ambos exponentes son 0, usamos el riesgo original del Excel.
        # Si el usuario mueve un slider, recalculamos aplicando el castigo exponencial.
        if exp_deuda > 0 or exp_tiempo > 0:
            factor_exponencial = np.exp((df['Deuda actual'] / deuda_media) * exp_deuda) * np.exp((df['diferencia de días'] / dias_medios) * exp_tiempo)
            df['Riesgo de entrada en Mora'] = df['Riesgo de entrada en Mora'] * factor_exponencial
        
        # Redondeamos el riesgo para que quede limpio visualmente
        df['Riesgo de entrada en Mora'] = df['Riesgo de entrada en Mora'].round(0)
        # ----------------------------------------
        
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
    # Clave: Ordenamos el Censo Completo por el NUEVO riesgo recalculado dinámicamente
    data = data.sort_values(by="Riesgo de entrada en Mora", ascending=False)
    gestores = {f"Gestor {i+1}": 0 for i in range(num_gestores)}
    asignaciones = []
    for _, fila in data.iterrows():
        gestor_libre = min(gestores, key=gestores.get)
        asignaciones.append(gestor_libre)
        gestores[gestor_libre] += fila['CARGA OPERATIVA']
    data['Gestor_Asignado'] = asignaciones
    return data, gestores

# --- PANEL DE CONTROL INTERACTIVO (SIDEBAR) ---
with st.sidebar:
    st.image("https://www.opplus.es/wp-content/uploads/2021/04/logo-opplus.png", width=150)
    st.markdown("### ⚙️ Parámetros del Modelo")
    n_gestores = st.slider("Gestores Disponibles", 10, 60, 39)
    
    st.markdown("---")
    st.markdown("### 📈 Exponentes de Sensibilidad (Riesgo)")
    st.caption("Modifica las prioridades del modelo matemáticamente:")
    
    # Sliders exponenciales (Empiezan en 0 para ver el excel original, y al moverlos cambia todo)
    e_deuda = st.slider("Sensibilidad de Deuda (λ1)", 0.0, 5.0, 0.0, step=0.1)
    e_tiempo = st.slider("Sensibilidad de Días Abiertos (λ2)", 0.0, 5.0, 0.0, step=0.1)
    
    st.markdown("---")
    st.markdown("### 🎯 Reglas de Negocio")
    # Umbrales calibrados para que reaccionen perfectamente con las tarjetas tácticas
    u_alto = st.number_input("Mínimo para 'Alto Riesgo'", min_value=1500, max_value=1000000, value=3000, step=500)
    u_medio = st.number_input("Mínimo para 'Riesgo Medio'", min_value=500, max_value=99999, value=1500, step=100)
    dias_kpi = st.slider("Plazo crítico de control (Días)", 15, 90, 60, step=5)

# --- LÓGICA PRINCIPAL ---
df = process_data(u_alto, u_medio, e_deuda, e_tiempo)

if df is not None:
    st.title("Modelo de priorización | Optimización Opplus")

    df_final, cargas = asignar_expedientes(df, n_gestores)

    # ==========================================
    # PANEL DE KPIs ESTRATÉGICOS
    # ==========================================
    kpi1, kpi2, kpi3 = st.columns(3)
    
    with kpi1:
        st.metric(label="📦 Volumen de Expedientes", value=len(df_final))
        
    with kpi2:
        casos_bajo_limite = len(df_final[df_final['diferencia de días'] <= dias_kpi])
        pct_bajo_limite = (casos_bajo_limite / len(df_final)) * 100
        st.metric(
            label=f"⏱️ Índice de Cobertura (< {dias_kpi} días)", 
            value=f"{pct_bajo_limite:.1f}%", 
            delta="Objetivo: > 90%", 
            delta_color="normal"
        )
        
    with kpi3:
        casos_criticos = len(df_final[df_final['diferencia de días'] > dias_kpi])
        st.metric(
            label="🚨 Alertas de Mora (> {dias_kpi} días)", 
            value=casos_criticos, 
            delta="A regularizar urgente", 
            delta_color="inverse"
        )
        
    st.markdown("<br>", unsafe_allow_html=True)

    # SECCIÓN 1: GRÁFICOS ESTRATÉGICOS
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Volumen por Nivel de Riesgo")
        riesgo_stats = df_final['Nivel Riesgo'].value_counts().reset_index()
        riesgo_stats.columns = ['Nivel Riesgo', 'Cantidad']
        
        colores_semaforo = {'Alto Riesgo': '#e74c3c', 'Riesgo Medio': '#f1c40f', 'Bajo Riesgo': '#2ecc71'}
        
        fig_riesgo = px.bar(
            riesgo_stats, x='Cantidad', y='Nivel Riesgo', orientation='h',
            color='Nivel Riesgo', color_discrete_map=colores_semaforo,
            category_orders={'Nivel Riesgo': ['Alto Riesgo', 'Riesgo Medio', 'Bajo Riesgo']}
        )
        fig_riesgo.update_layout(showlegend=False, yaxis_title=None, xaxis_title="Nº de Expedientes")
        st.plotly_chart(fig_riesgo, use_container_width=True)

    with col_b:
        st.subheader("Matriz Carga vs Riesgo")
        cuadrantes_stats = df_final['Cuadrante'].value_counts().reset_index()
        cuadrantes_stats.columns = ['Cuadrante', 'count']
        fig_cuadrantes = px.bar(
            cuadrantes_stats, x='Cuadrante', y='count',
            color='Cuadrante', color_discrete_sequence=px.colors.qualitative.Safe
        )
        st.plotly_chart(fig_cuadrantes, use_container_width=True)

    st.markdown("---")

    # SECCIÓN 2: LISTAS TÁCTICAS DE PRIORIDAD (¡Ahora cambian de inmediato!)
    st.header("Listas de Asignación Inmediata")
    
    lp1, lp2 = st.columns(2)

    with lp1:
        st.markdown('<div class="prioridad-card">', unsafe_allow_html=True)
        st.subheader("Lista 1: Carga Alta / Riesgo Alto")
        st.caption("Casos críticos reordenados por el nuevo impacto exponencial")
        
        # Filtramos los que ahora mismo son Alto Riesgo según el cálculo vivo
        l1 = df_final[(df_final['Nivel Carga'] == 'Alta Carga') & (df_final['Nivel Riesgo'] == 'Alto Riesgo')]
        l1 = l1.sort_values(by="Riesgo de entrada en Mora", ascending=False)
        
        if not l1.empty:
            for _, fila in l1.head(15).iterrows(): 
                # Pintamos el nuevo número de riesgo calculado
                st.write(f"📄 **Exp. {fila['Columna1']}** | Nuevo Riesgo: `{int(fila['Riesgo de entrada en Mora'])}` | 👤 `{fila['Gestor_Asignado']}`")
        else:
            st.write("✅ Sin casos en este cuadrante con el umbral actual.")
        st.markdown('</div>', unsafe_allow_html=True)

    with lp2:
        st.markdown('<div class="prioridad-card" style="border-left: 5px solid #f1c40f;">', unsafe_allow_html=True)
        st.subheader("Lista 2: Carga Baja / Riesgo Alto")
        st.caption("Prioridad 'Quick Win' reordenada por impacto exponencial")
        
        l2 = df_final[(df_final['Nivel Carga'] == 'Baja Carga') & (df_final['Nivel Riesgo'] == 'Alto Riesgo')]
        l2 = l2.sort_values(by="Riesgo de entrada en Mora", ascending=False)
        
        if not l2.empty:
            for _, fila in l2.head(15).iterrows():
                st.write(f"📄 **Exp. {fila['Columna1']}** | Nuevo Riesgo: `{int(fila['Riesgo de entrada en Mora'])}` | 👤 `{fila['Gestor_Asignado']}`")
        else:
            st.write("✅ Sin casos en este cuadrante con el umbral actual.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    
    # SECCIÓN 3: TABLA GENERAL (Se reordena por completo según tus sliders)
    st.subheader("📋 Censo Completo de Asignaciones")
    st.caption("La tabla se reordena dinámicamente poniendo arriba los expedientes más penalizados por los exponentes.")
    st.dataframe(
        df_final[['Columna1', 'Riesgo de entrada en Mora', 'Gestor_Asignado', 'Cuadrante', 'Deuda actual', 'diferencia de días']],
        use_container_width=True
    )

else:
    st.error("Archivo no encontrado o formato incorrecto.")
