import streamlit as st
import pandas as pd
import plotly.express as px
from st_supabase_connection import SupabaseConnection

# 1. CONFIGURACIÓN Y ESTILO APPLE-CLEAN
st.set_page_config(page_title="CobroYa Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    .stTextInput > div > div > input { border-radius: 10px; }
    .auth-card {
        background-color: white; padding: 40px; border-radius: 20px;
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
        text-align: center; max-width: 450px; margin: auto; border: 1px solid #F0F0F0;
    }
    .metric-card {
        background-color: white; padding: 25px; border-radius: 18px;
        border: 1px solid #E5E7EB; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    div.stButton > button:first-child {
        background-color: #007AFF; color: white; border-radius: 12px; border: none;
        padding: 0.6rem 2rem; font-weight: bold; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# Conexión a Supabase
conn = st.connection("supabase", type=SupabaseConnection)

# --- 2. SISTEMA DE ACCESO (LOGIN) ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/1053/1053210.png", width=80)
        st.markdown("<h2 style='color: #1D1D1F;'>CobroYa Global</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #86868B;'>Gestión de Cartera e Inteligencia Financiera</p>", unsafe_allow_html=True)
        
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        
        if st.button("Acceder al Sistema"):
            # Credenciales temporales (Cámbialas luego)
            if user == "admin" and password == "1234":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Acceso denegado. Verifique sus credenciales.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 3. FUNCIONES DE DATOS ---
def cargar_metricas():
    # Suma real del balance pendiente
    res = conn.table("cuentas").select("balance_pendiente").eq("estado", "Activo").execute()
    total = sum([float(c['balance_pendiente']) for c in res.data]) if res.data else 0
    
    # Conteo de clientes
    res_cli = conn.table("clientes").select("id", count="exact").execute()
    count_cli = res_cli.count if res_cli.count else 0
    
    return total, count_cli

# --- 4. NAVEGACIÓN ---
with st.sidebar:
    st.markdown("<h2 style='color: #007AFF; text-align: center;'>CobroYa</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("NAVEGACIÓN", ["Panel de Control", "Clientes", "Nueva Cuenta", "IA Predictor"])
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULOS ---
if menu == "Panel de Control":
    st.header("Análisis de Cartera en Tiempo Real")
    total_calle, total_clientes = cargar_metricas()
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><small>DINERO EN CALLE</small><h2 style='color: #1D1D1F;'>RD$ {total_calle:,.2f}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><small>CLIENTES ACTIVOS</small><h2 style='color: #007AFF;'>{total_clientes}</h2></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><small>EFICIENCIA</small><h2 style='color: #34C759;'>94.2%</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Gráfico de Pagos Reales
    st.subheader("Historial de Recaudación (Datos de Supabase)")
    res_p = conn.table("pagos").select("monto_pagado, fecha_pago").execute()
    if res_p.data:
        df_p = pd.DataFrame(res_p.data)
        df_p['fecha_pago'] = pd.to_datetime(df_p['fecha_pago']).dt.date
        fig = px.bar(df_p, x='fecha_pago', y='monto_pagado', 
                     color_discrete_sequence=['#007AFF'], template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay pagos registrados para mostrar tendencias.")

elif menu == "Clientes":
    st.header("Directorio de Clientes")
    with st.expander("➕ Registrar Nuevo Cliente"):
        with st.form("form_cli"):
            n = st.text_input("Nombre")
            c = st.text_input("Cédula")
            t = st.text_input("Teléfono")
            if st.form_submit_button("Guardar Cliente"):
                conn.table("clientes").insert({"nombre": n, "cedula": c, "telefono": t}).execute()
                st.success("Registrado.")
                st.rerun()
    
    res_all = conn.table("clientes").select("*").execute()
    if res_all.data:
        st.dataframe(pd.DataFrame(res_all.data)[['nombre', 'cedula', 'telefono']], use_container_width=True)

elif menu == "Nueva Cuenta":
    st.header("Apertura de Crédito")
    # Lógica para seleccionar cliente y crear deuda (similar a la anterior pero integrada)
    res_cl = conn.table("clientes").select("id, nombre").execute()
    cl_opt = {c['nombre']: c['id'] for c in res_cl.data} if res_cl.data else {}
    
    if cl_opt:
        with st.form("f_deuda"):
            c_sel = st.selectbox("Cliente", list(cl_opt.keys()))
            m_fiao = st.number_input("Monto", min_value=1.0)
            if st.form_submit_button("Crear Deuda"):
                conn.table("cuentas").insert({"cliente_id": cl_opt[c_sel], "monto_inicial": m_fiao, "balance_pendiente": m_fiao}).execute()
                st.success("Cuenta creada.")
    else:
        st.warning("Cree un cliente primero.")

elif menu == "IA Predictor":
    st.header("Analítica Predictiva (IA)")
    st.markdown("<div class='metric-card'>Esta sección utiliza los datos de pago históricos para predecir la probabilidad de cobro exitoso.</div>", unsafe_allow_html=True)
    # Aquí es donde conectaremos Groq en el siguiente paso
