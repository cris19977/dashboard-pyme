import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="Sistema Gestión PyME (CLP)", layout="wide", page_icon="🇨🇱")

# --- FUNCIÓN HELPER: FORMATO PESO CHILENO ---
def fmt_clp(valor):
    """Convierte un número a formato CLP: $1.000 (Sin decimales, con punto)"""
    if pd.isna(valor):
        return "$0"
    return "${:,.0f}".format(valor).replace(",", ".")

# ==========================================
# SIDEBAR: CARGA DE DATOS
# ==========================================
st.sidebar.header("📁 Carga de Datos")
st.sidebar.markdown("Sube tu Excel con columnas: `Producto`, `Unidades`, `Precio`, `Costo`, `Mes`")
uploaded_file = st.sidebar.file_uploader("Subir Excel (.xlsx)", type=["xlsx"])

# Función de carga en caché
@st.cache_data
def load_data(file):
    if file is not None:
        return pd.read_excel(file)
    return None

# Lógica de Datos (Real vs Demo)
if uploaded_file is not None:
    df_main = load_data(uploaded_file)
    st.sidebar.success("¡Datos cargados correctamente!")
    
    # Validación simple
    req_cols = ['Producto', 'Unidades', 'Precio', 'Costo', 'Mes']
    if not all(col in df_main.columns for col in req_cols):
        st.error(f"Error: Faltan columnas. Requeridas: {req_cols}")
        st.stop()
else:
    st.sidebar.info("👆 Modo Demo. Sube tu archivo para ver datos reales.")
    # Datos de ejemplo realistas para Chile
    data_demo = {
        'Producto': ['Polera Básica', 'Jeans Denim', 'Zapatillas Urbanas', 'Jockey', 'Polera Básica', 'Jeans Denim', 'Zapatillas Urbanas', 'Jockey'],
        'Unidades': [50, 30, 10, 80, 65, 45, 18, 95],
        'Precio': [12990, 24990, 45990, 8990, 12990, 24990, 45990, 8990],
        'Costo': [6500, 12000, 25000, 3500, 6500, 12000, 25000, 3500],
        'Mes': [1, 1, 1, 1, 2, 2, 2, 2]
    }
    df_main = pd.DataFrame(data_demo)

# ==========================================
# INTERFAZ PRINCIPAL
# ==========================================
st.title("🚀 Sistema de Gestión PyME")
st.markdown("Visualización financiera y proyecciones en **Pesos Chilenos (CLP)**.")

tab1, tab2, tab3 = st.tabs(["🧮 Calculadora Precios", "📊 Dashboard Ventas", "🤖 Predicción IA"])

# ==========================================
# TAB 1: CALCULADORA (CLP)
# ==========================================
with tab1:
    st.header("Simulador de Precio de Venta")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Costos y Márgenes")
        # Inputs con step=100 para evitar decimales molestos
        costo_unitario = st.number_input("Costo Unitario ($)", min_value=0, value=5000, step=100)
        margen_deseado = st.slider("Margen de Ganancia (%)", 0, 100, 30)
        impuesto = st.number_input("IVA / Impuesto (%)", min_value=0.0, value=19.0)

    with col2:
        st.subheader("Resultado")
        # Cálculos
        precio_neto = costo_unitario * (1 + (margen_deseado / 100))
        precio_final = precio_neto * (1 + (impuesto / 100))
        utilidad_unitaria = precio_neto - costo_unitario
        impuesto_valor = precio_final - precio_neto

        # Métricas con formato CLP
        st.metric(label="Precio Venta Final (con IVA)", value=fmt_clp(precio_final))
        st.metric(label="Utilidad por Unidad", value=fmt_clp(utilidad_unitaria), delta=f"{margen_deseado}% Margen")
        
        # Gráfico de composición
        df_precio = pd.DataFrame({
            'Componente': ['Costo', 'Utilidad', 'Impuestos'],
            'Valor': [costo_unitario, utilidad_unitaria, impuesto_valor]
        })
        
        fig_pie = px.pie(df_precio, values='Valor', names='Componente', 
                         title='Estructura del Precio', hole=0.4,
                         color_discrete_sequence=['#94a3b8', '#10b981', '#ef4444'])
        
        # Configuración Plotly para Chile
        fig_pie.update_layout(separators=",.") 
        fig_pie.update_traces(textinfo='percent+label', hovertemplate="%{label}: <br>%{value:$,.0f}")
        
        st.plotly_chart(fig_pie, use_container_width=True)

# ==========================================
# TAB 2: DASHBOARD (CLP)
# ==========================================
with tab2:
    st.header("Análisis de Rentabilidad")
    
    # 1. Cálculos Masivos
    df_main['Venta_Total'] = df_main['Unidades'] * df_main['Precio']
    df_main['Costo_Total'] = df_main['Unidades'] * df_main['Costo']
    df_main['Utilidad'] = df_main['Venta_Total'] - df_main['Costo_Total']
    
    # Agrupación
    df_prod = df_main.groupby('Producto')[['Venta_Total', 'Utilidad', 'Unidades']].sum().reset_index()
    
    # 2. KPIs Generales
    k1, k2, k3 = st.columns(3)
    k1.metric("Ventas Totales", fmt_clp(df_main['Venta_Total'].sum()))
    k2.metric("Utilidad Total", fmt_clp(df_main['Utilidad'].sum()))
    k3.metric("Unidades Vendidas", f"{df_main['Unidades'].sum():,.0f}".replace(",", "."))
    
    st.markdown("---")

    # 3. Gráficos
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Ingresos vs Utilidad")
        fig_bar = px.bar(df_prod, x='Producto', y=['Venta_Total', 'Utilidad'], barmode='group',
                         color_discrete_map={'Venta_Total': '#3b82f6', 'Utilidad': '#10b981'})
        
        # Formato Eje Y y Tooltip en CLP
        fig_bar.update_layout(separators=",.", yaxis_tickformat="$,.0f")
        fig_bar.update_traces(hovertemplate="%{y:$,.0f}")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c2:
        st.subheader("Distribución de Ganancias")
        fig_pie2 = px.pie(df_prod, values='Utilidad', names='Producto', hole=0.4)
        fig_pie2.update_layout(separators=",.")
        fig_pie2.update_traces(hovertemplate="%{label}: <br>%{value:$,.0f}")
        st.plotly_chart(fig_pie2, use_container_width=True)

    # 4. Tabla Detallada con formato
    st.subheader("Detalle de Operaciones")
    
    # Diccionario de formato para Pandas
    format_mapping = {
        'Precio': lambda x: fmt_clp(x),
        'Costo': lambda x: fmt_clp(x),
        'Venta_Total': lambda x: fmt_clp(x),
        'Costo_Total': lambda x: fmt_clp(x),
        'Utilidad': lambda x: fmt_clp(x)
    }
    
    # Mostrar tabla estilizada
    st.dataframe(
        df_main.style.format(format_mapping, na_rep="-"),
        use_container_width=True
    )

# ==========================================
# TAB 3: PREDICCIONES (IA)
# ==========================================
with tab3:
    st.header("Proyección de Ventas (IA)")
    
    # Preparar datos
    df_hist = df_main.groupby('Mes')['Venta_Total'].sum().reset_index()
    
    if len(df_hist) < 2:
        st.warning("⚠️ Se necesitan datos de al menos 2 meses distintos para predecir.")
    else:
        X = df_hist['Mes'].values.reshape(-1, 1)
        y = df_hist['Venta_Total'].values
        
        # Modelo
        model = LinearRegression()
        model.fit(X, y)
        
        # Predicción Mes Siguiente
        next_month = df_hist['Mes'].max() + 1
        pred_val = model.predict([[next_month]])[0]
        
        # Visualización
        col_res, col_g = st.columns([1, 2])
        
        with col_res:
            st.info(f"Predicción Mes {next_month}")
            st.metric("Venta Estimada", fmt_clp(pred_val))
            
            r2 = model.score(X, y)
            st.write(f"**Confianza del modelo (R²):** {r2:.2f}")
            if r2 < 0.5:
                st.caption("⚠️ Baja precisión (pocos datos históricos).")

        with col_g:
            # Dataframe para gráfico
            df_fut = pd.DataFrame({'Mes': [next_month], 'Venta_Total': [pred_val], 'Tipo': 'Proyección'})
            df_hist['Tipo'] = 'Real'
            df_chart = pd.concat([df_hist, df_fut], ignore_index=True)
            
            fig_line = px.line(df_chart, x='Mes', y='Venta_Total', color='Tipo', markers=True,
                               color_discrete_map={'Real': '#2563eb', 'Proyección': '#ea580c'})
            
            # Formato Chileno en gráfico
            fig_line.update_layout(separators=",.", yaxis_tickformat="$,.0f", title="Tendencia Histórica y Futura")
            fig_line.update_traces(hovertemplate="Mes %{x}: <br>%{y:$,.0f}")
            
            st.plotly_chart(fig_line, use_container_width=True)

