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

# Función: Lee directamente los datos del nuevo Excel
def process_data(umbral_alto, umbral_medio):
    try:
        # ADAPTADO: Nombre del nuevo archivo Excel
        df = pd.read_excel("OPPLUS.xlsx", sheet_name="Modelo")
        df.columns = [c.strip() for c in df.columns]
        
        # Redondeamos el riesgo original del Excel para la interfaz gráfica
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
        
        # Sumamos los criterios a la mochila del gestor elegido utilizando la nueva columna 'Tiempo invertido'
        gestores[gestor_libre]["carga"] += fila['CARGA OPERATIVA']
        gestores[gestor_libre]["minutos"] += fila['Tiempo invertido']
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
        # ADAPTADO: Ahora calcula la media sobre la nueva columna 'Tiempo invertido'
        media_tiempo = df_final['Tiempo invertido'].mean()
        st.metric(
            label="📞 Tiempo Medio de Comunicación", 
            value=f"{media_tiempo:.1f} min"
        )
        
    st.markdown("<br>", unsafe_allow_html=True)

    # SECCIÓN 1: GRÁFICOS ESTRATÉGICOS
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Volumen por Nivel de Riesgo")
        colores_semaforo = {'Alto Riesgo': '#e74c3c', 'Riesgo Medio': '#f1c40f', 'Bajo Riesgo': '#2ecc71'}
        fig_riesgo = px.pie(
            df_final, names='Nivel Riesgo', hole=0.5,
            color='Nivel Riesgo',
            color_discrete_map=colores_semaforo
        )
        st.plotly_chart(fig_riesgo, use_container_width=True)

    with col_b:
        st.subheader("Matriz Carga vs Riesgo")
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
        st.caption("Casos críticos reales que requieren mayor tiempo de gestión")
        
        l1 = df_final[(df_final['Nivel Carga'] == 'Alta Carga') & (df_final['Nivel Riesgo'] == 'Alto Riesgo')]
        l1 = l1.sort_values(by="Riesgo de entrada en Mora", ascending=False)
        
        if not l1.empty:
            for _, fila in l1.head(15).iterrows(): 
                # ADAPTADO: Muestra 'Nº de cliente' y 'Tiempo invertido'
                st.write(f"📄 **Exp. {int(fila['Nº de cliente'])}** | Riesgo: `{int(fila['Riesgo de entrada en Mora'])}` | ⏱️ `{fila['Tiempo invertido']:.1f} min` | 👤 `{fila['Gestor_Asignado']}`")
        else:
            st.write("✅ Sin casos en este cuadrante.")
        st.markdown('</div>', unsafe_allow_html=True)

    with lp2:
        st.markdown('<div class="prioridad-card" style="border-left: 5px solid #f1c40f;">', unsafe_allow_html=True)
        st.subheader("Lista 2: Carga Baja / Riesgo Alto")
        st.caption("Prioridad 'Quick Win': Alta peligrosidad real, baja dificultad operativa")
        
        l2 = df_final[(df_final['Nivel Carga'] == 'Baja Carga') & (df_final['Nivel Riesgo'] == 'Alto Riesgo')]
        l2 = l2.sort_values(by="Riesgo de entrada en Mora", ascending=False)
        
        if not l2.empty:
            for _, fila in l2.head(15).iterrows():
                # ADAPTADO: Muestra 'Nº de cliente' y 'Tiempo invertido'
                st.write(f"📄 **Exp. {int(fila['Nº de cliente'])}** | Riesgo: `{int(fila['Riesgo de entrada en Mora'])}` | ⏱️ `{fila['Tiempo invertido']:.1f} min` | 👤 `{fila['Gestor_Asignado']}`")
        else:
            st.write("✅ Sin casos en este cuadrante.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()
    
    # SECCIÓN 3: TABLA GENERAL
    st.subheader("📋 Censo Completo de Asignaciones")
    st.dataframe(
        # ADAPTADO: Columnas clave mapeadas según el nuevo censo 'OPPLUS.xlsx'
        df_final[['Nº de cliente', 'Gestor_Asignado', 'Cuadrante', 'Deuda actual', 'diferencia de días', 'Tiempo invertido', 'Riesgo de entrada en Mora']],
        use_container_width=True
    )

    st.divider()

    # SECCIÓN 4: TABLA DE BALANCE DE TIEMPOS POR GESTOR
    st.subheader("📊 Balance de Tiempos y Cargas por Gestor")
    st.caption("Verifica el reparto equitativo del tiempo total de comunicación y volumen de trabajo en el equipo.")
    
    datos_tabla_gestores = []
    for g_id, métricas in estadísticas_gestores.items():
        datos_tabla_gestores.append({
            "Gestor Asignado": g_id,
            "Expedientes Asignados": métricas["expedientes_totales"],
            "Tiempo Total (Minutos)": round(métricas["minutos"], 1),
            "Tiempo Total (Horas)": round(métricas["minutos"] / 60, 2),
            "Carga Operativa Total": round(métricas["carga"], 2)
        })
        
    df_tiempos_gestores = pd.DataFrame(datos_tabla_gestores)
    st.dataframe(df_tiempos_gestores, use_container_width=True, hide_index=True)

else:
    st.error("Archivo no encontrado o formato incorrecto.")
