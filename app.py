import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression


# Función para formatear a Peso Chileno (Ej: 1500 -> $1.500)
def clp(valor):
    return "${:,.0f}".format(valor).replace(",", ".")


# --- Configuración de la Página ---
st.set_page_config(page_title="Sistema Gestión PyME Pro", layout="wide", page_icon="📊")

# --- BARRA LATERAL: CARGA DE DATOS ---
st.sidebar.header("📁 Carga de Datos")
st.sidebar.markdown("Sube tu archivo Excel con las ventas reales.")
uploaded_file = st.sidebar.file_uploader("Subir Excel (.xlsx)", type=["xlsx"])

# Función para cargar datos (Usa caché para no recargar a cada rato)
@st.cache_data
def load_data(file):
    if file is not None:
        return pd.read_excel(file)
    return None

# Lógica de Datos: Si suben archivo lo usamos, si no, usamos datos de ejemplo
if uploaded_file is not None:
    df_main = load_data(uploaded_file)
    st.sidebar.success("¡Datos cargados correctamente!")
    
    # Verificación básica de columnas
    required_columns = ['Producto', 'Unidades', 'Precio', 'Costo', 'Mes']
    if not all(col in df_main.columns for col in required_columns):
        st.error(f"El Excel debe tener las columnas: {', '.join(required_columns)}")
        st.stop()
else:
    st.sidebar.info("👆 Sube un archivo para ver tus datos reales. Mostrando datos de DEMOSTRACIÓN.")
    # Datos de ejemplo por defecto
    data_demo = {
        'Producto': ['Camisa', 'Pantalón', 'Zapatos', 'Gorra', 'Camisa', 'Pantalón', 'Zapatos', 'Gorra'],
        'Unidades': [50, 30, 10, 80, 60, 40, 15, 90],
        'Precio': [2500, 4500, 8000, 1500, 2500, 4500, 8000, 1500],
        'Costo': [1200, 2500, 4000, 600, 1200, 2500, 4000, 600],
        'Mes': [1, 1, 1, 1, 2, 2, 2, 2] # Datos de 2 meses
    }
    df_main = pd.DataFrame(data_demo)

# --- TÍTULO PRINCIPAL ---
st.title("🚀 Sistema de Gestión PyME")

# --- Estructura de Pestañas ---
tab1, tab2, tab3 = st.tabs(["🧮 Calculadora Precios", "📊 Dashboard Ventas", "🤖 Predicción IA"])

# ==========================================
# TAB 1: CALCULADORA (Igual que antes, herramienta utilitaria)
# ==========================================
with tab1:
    st.header("Simulador de Precios")
    col1, col2 = st.columns(2)
    with col1:
        c_unit = st.number_input("Costo del Producto ($)", value=1000.0)
        m_ganancia = st.slider("Margen (%)",30 , 50, 70 , 100)
        tax = st.number_input("Impuestos (%)", value=19.0)
    with col2:
        p_neto = c_unit * (1 + m_ganancia/100)
        p_final = p_neto * (1 + tax/100)

st.metric(label="Precio Final", value=clp(p_final))
st.metric(label="Ganancia Neta", value=clp(p_neto - c_unit))


# ==========================================
# TAB 2: DASHBOARD FINANCIERO (Con datos del Excel)
# ==========================================
with tab2:
    st.header("Análisis de tus Datos")
    
    # 1. Procesamiento de datos
    # Calculamos totales por fila
    df_main['Venta_Total'] = df_main['Unidades'] * df_main['Precio']
    df_main['Costo_Total'] = df_main['Unidades'] * df_main['Costo']
    df_main['Utilidad'] = df_main['Venta_Total'] - df_main['Costo_Total']
    
    # Agrupamos por Producto para ver rendimiento acumulado
    df_productos = df_main.groupby('Producto')[['Venta_Total', 'Utilidad', 'Unidades']].sum().reset_index()
    df_productos['Margen_%'] = ((df_productos['Utilidad'] / df_productos['Venta_Total']) * 100).round(1)

    # 2. Métricas Generales (KPIs)
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Ventas Totales", f"${df_main['Venta_Total'].sum():,.0f}")
    kpi2.metric("Utilidad Total", f"${df_main['Utilidad'].sum():,.0f}")
    kpi3.metric("Unidades Vendidas", f"{df_main['Unidades'].sum():,.0f}")

    st.markdown("---")

    # 3. Gráficos
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Rentabilidad por Producto")
        fig_bar = px.bar(df_productos, x='Producto', y=['Venta_Total', 'Utilidad'], 
                         title="Comparativa Ingresos vs Ganancia", barmode='group')
        fig.update_layout(separators=",.")
st.plotly_chart(fig_bar, use_container_width=True)
    
    with c2:
        st.subheader("Peso en el Negocio")
        fig_pie = px.pie(df_productos, values='Utilidad', names='Producto', 
                         title="¿Qué producto genera más ganancias?", hole=0.4)
        fig.update_layout(separators=",.")
st.plotly_chart(fig_pie, use_container_width=True)
        
    st.dataframe(df_main)

# ==========================================
# TAB 3: PREDICCIONES (Basado en la columna 'Mes' del Excel)
# ==========================================
with tab3:
    st.header("Proyección de Ventas Futuras")
    
    # Agrupar ventas por Mes (Sumar todas las ventas de todos los productos por mes)
    df_history = df_main.groupby('Mes')['Venta_Total'].sum().reset_index()

    if len(df_history) < 2:
        st.warning("⚠️ Necesitas datos de al menos 2 meses distintos en tu Excel para hacer una predicción.")
    else:
        # Preparar datos para Scikit-Learn
        X = df_history['Mes'].values.reshape(-1, 1)
        y = df_history['Venta_Total'].values
        
        # Entrenar Modelo
        modelo = LinearRegression()
        modelo.fit(X, y)
        
        # Predecir siguiente mes (El último mes registrado + 1)
        ultimo_mes = df_history['Mes'].max()
        mes_futuro = np.array([[ultimo_mes + 1]])
        prediccion = modelo.predict(mes_futuro)
        
        # Mostrar resultados
        col_res, col_graph = st.columns([1, 2])
        
        with col_res:
            st.success(f"Predicción para el Mes {ultimo_mes + 1}")
            st.metric("Ventas Esperadas", value=clp{prediccion[0]}")
            st.caption("Basado en regresión lineal de tus datos históricos.")
            
        with col_graph:
            # Graficar Histórico + Predicción
            df_future = pd.DataFrame({'Mes': [ultimo_mes + 1], 'Venta_Total': prediccion, 'Tipo': 'Predicción'})
            df_history['Tipo'] = 'Real'
            
            df_final = pd.concat([df_history, df_future], ignore_index=True)
            
            fig_trend = px.line(df_final, x='Mes', y='Venta_Total', color='Tipo', markers=True,
                                title="Tendencia de Ventas y Futuro",
                                color_discrete_map={'Real': 'blue', 'Predicción': 'green'})
fig.update_layout(separators=",.")
            st.plotly_chart(fig_trend, use_container_width=True)

