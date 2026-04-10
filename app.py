import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_supabase_connection import SupabaseConnection

# Configuración de página estilo Profesional
st.set_page_config(page_title="CobroYa - Gestión Financiera", layout="wide")

# CSS Inyectado para estilo Apple (Blanco, Sombras Suaves, Bordes Redondeados)
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    div.stButton > button:first-child {
        background-color: #007AFF; color: white; border-radius: 10px; border: none;
        padding: 0.5rem 2rem; font-weight: bold;
    }
    .metric-card {
        background-color: white; padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 1px solid #EDEDED;
    }
    h1, h2, h3 { color: #1D1D1F; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# Conexión a Supabase
conn = st.connection("supabase", type=SupabaseConnection)

# --- LÓGICA DE DATOS ---
def get_stats():
    # Simulamos datos para visualizar los gráficos ahora mismo
    # Luego esto se cambia por: conn.table("cuentas").select("*").execute()
    data = {
        'Total en Calle': 150250.00,
        'Cobros Hoy': 12400.00,
        'Clientes Activos': 45,
        'Recuperación': 85
    }
    return data

# --- INTERFAZ DE USUARIO ---

# Sidebar elegante
with st.sidebar:
    st.title("CobroYa")
    st.markdown("---")
    menu = st.radio("Navegación", ["Panel de Control", "Clientes", "Nueva Cuenta", "Reportes"])
    st.markdown("---")
    st.caption("Versión 1.0.0 Pro")

if menu == "Panel de Control":
    st.header("Resumen General")
    stats = get_stats()

    # Bloque de Métricas Principales (Kpis)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'> 📊 <br><small>TOTAL EN CALLE</small><br><h2>RD$ {stats['Total en Calle']:,.2f}</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'> 📅 <br><small>COBROS HOY</small><br><h2 style='color: #007AFF;'>RD$ {stats['Cobros Hoy']:,.2f}</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'> 👥 <br><small>CLIENTES</small><br><h2>{stats['Clientes Activos']}</h2></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'> ✅ <br><small>RECUPERACIÓN</small><br><h2 style='color: #34C759;'>{stats['Recuperación']}%</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráficos Profesionales
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Flujo de Cobros Semanal")
        # Gráfico de Líneas suave
        df_ventas = pd.DataFrame({
            'Día': ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'],
            'Cobrado': [12000, 15000, 8000, 22000, 19000, 30000, 5000]
        })
        fig_line = px.line(df_ventas, x='Día', y='Cobrado', template="plotly_white", 
                           color_discrete_sequence=['#007AFF'])
        fig_line.update_traces(line_width=4, mode='lines+markers')
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        st.subheader("Distribución de Cartera")
        # Gráfico de Donas elegante
        fig_donut = go.Figure(data=[go.Scatter(
            x=[1, 2, 3, 4], y=[10, 11, 12, 13],
            mode='markers',
            marker=dict(size=[40, 60, 80, 100], color=['#007AFF', '#34C759', '#FF9500', '#FF3B30'])
        )])
        # Cambiamos a un Pie Chart real para carteras
        labels = ['Al día', 'Atrasado', 'Vencido']
        values = [70, 20, 10]
        fig_pie = px.pie(names=labels, values=values, hole=.6,
                         color_discrete_sequence=['#34C759', '#FF9500', '#FF3B30'])
        fig_pie.update_layout(showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Tabla de Próximos Cobros
    st.subheader("Próximos Cobros Pendientes")
    df_prox = pd.DataFrame({
        'Cliente': ['Juan Pérez', 'María García', 'Talleres RD', 'Colmado Lora'],
        'Monto': [1500, 3000, 12500, 800],
        'Vence': ['Hoy', 'Hoy', 'Mañana', '12 Abr'],
        'Estado': ['Urgente', 'Urgente', 'Pendiente', 'Pendiente']
    })
    st.table(df_prox)

elif menu == "Nueva Cuenta":
    st.header("Registrar Nueva Deuda")
    with st.form("form_cuenta"):
        cliente = st.selectbox("Seleccionar Cliente", ["Juan Pérez", "Crear Nuevo..."])
        monto = st.number_input("Monto del Préstamo/Fiao (RD$)", min_value=0.0)
        cuotas = st.slider("Cantidad de Cuotas", 1, 12, 1)
        fecha = st.date_input("Fecha de Inicio")
        submitted = st.form_submit_button("Registrar Cuenta")
        if submitted:
            st.success("Cuenta registrada correctamente.")
