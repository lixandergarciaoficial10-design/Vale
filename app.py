import streamlit as st
import pandas as pd
import plotly.express as px
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# 1. CONFIGURACIÓN Y ESTILO
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
    .btn-whatsapp {
        background-color: #25D366 !important; color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# --- 2. SISTEMA DE ACCESO ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/1053/1053210.png", width=80)
        st.markdown("<h2 style='color: #1D1D1F;'>CobroYa Global</h2>", unsafe_allow_html=True)
        user = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        if st.button("Acceder al Sistema"):
            if user == "admin" and password == "1234":
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Acceso denegado.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- 3. NAVEGACIÓN ---
with st.sidebar:
    st.markdown("<h2 style='color: #007AFF; text-align: center;'>CobroYa</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("NAVEGACIÓN", ["Panel de Control", "Clientes", "Nueva Cuenta", "Gestión de Cobros"])
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- 4. MÓDULOS ---

if menu == "Panel de Control":
    st.header("Análisis de Cartera")
    
    # Métricas Reales
    res_c = conn.table("cuentas").select("balance_pendiente").eq("estado", "Activo").execute()
    total_calle = sum([float(i['balance_pendiente']) for i in res_c.data]) if res_c.data else 0
    
    res_p = conn.table("pagos").select("monto_pagado, fecha_pago").execute()
    df_p = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame()

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><small>TOTAL POR COBRAR</small><h2>RD$ {total_calle:,.2f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><small>RECAUDADO MES</small><h2 style='color: #34C759;'>RD$ {df_p['monto_pagado'].sum() if not df_p.empty else 0:,.2f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><small>ESTADO</small><h2 style='color: #FF9500;'>Saludable</h2></div>", unsafe_allow_html=True)

    if not df_p.empty:
        st.subheader("Tendencia de Cobros")
        df_p['fecha_pago'] = pd.to_datetime(df_p['fecha_pago']).dt.date
        fig = px.area(df_p.groupby('fecha_pago').sum().reset_index(), x='fecha_pago', y='monto_pagado', color_discrete_sequence=['#007AFF'])
        st.plotly_chart(fig, use_container_width=True)

elif menu == "Clientes":
    st.header("Directorio")
    with st.expander("➕ Nuevo Cliente"):
        with st.form("f_cli"):
            n = st.text_input("Nombre")
            t = st.text_input("WhatsApp (Ej: 8291234567)")
            if st.form_submit_button("Registrar"):
                conn.table("clientes").insert({"nombre": n, "telefono": t}).execute()
                st.success("Listo")
                st.rerun()
    
    res = conn.table("clientes").select("*").execute()
    if res.data: st.table(pd.DataFrame(res.data)[['nombre', 'telefono']])

elif menu == "Nueva Cuenta":
    st.header("Registrar Deuda")
    res_cl = conn.table("clientes").select("id, nombre").execute()
    cl_opt = {c['nombre']: c['id'] for c in res_cl.data} if res_cl.data else {}
    
    if cl_opt:
        with st.form("f_deuda"):
            c_sel = st.selectbox("Cliente", list(cl_opt.keys()))
            monto = st.number_input("Monto (RD$)", min_value=1.0)
            if st.form_submit_button("Crear Cuenta"):
                conn.table("cuentas").insert({"cliente_id": cl_opt[c_sel], "monto_inicial": monto, "balance_pendiente": monto}).execute()
                st.success("Cuenta abierta.")
    else: st.warning("Cree un cliente primero.")

elif menu == "Gestión de Cobros":
    st.header("Panel de Cobranza Activa")
    
    # Traer cuentas activas con nombres de clientes
    query = conn.table("cuentas").select("id, balance_pendiente, clientes(nombre, telefono)").eq("estado", "Activo").execute()
    
    if query.data:
        for item in query.data:
            with st.container():
                col_info, col_pago, col_wa = st.columns([2, 1, 1])
                nombre = item['clientes']['nombre']
                tel = item['clientes']['telefono']
                deuda = float(item['balance_pendiente'])
                
                col_info.markdown(f"**{nombre}** \nBalance: RD$ {deuda:,.2f}")
                
                # Input de pago
                monto_pago = col_pago.number_input(f"Abono", min_value=0.0, max_value=deuda, key=f"p_{item['id']}")
                if col_pago.button(f"Pagar", key=f"btn_{item['id']}"):
                    if monto_pago > 0:
                        # 1. Registrar el pago
                        conn.table("pagos").insert({"cuenta_id": item['id'], "monto_pagado": monto_pago}).execute()
                        # 2. Actualizar el balance
                        nuevo_balance = deuda - monto_pago
                        estado = "Pagado" if nuevo_balance <= 0 else "Activo"
                        conn.table("cuentas").update({"balance_pendiente": nuevo_balance, "estado": estado}).eq("id", item['id']).execute()
                        st.success(f"¡Abono de {monto_pago} registrado!")
                        st.rerun()
                
                # Botón WhatsApp
                msg = f"Hola {nombre}, te recordamos tu balance pendiente de RD${deuda:,.2f}. ¿Cuándo podemos pasar?"
                wa_link = f"https://wa.me/{tel}?text={msg.replace(' ', '%20')}"
                col_wa.markdown(f'<br><a href="{wa_link}" target="_blank"><button style="background-color:#25D366; border:none; color:white; padding:10px; border-radius:10px; cursor:pointer; width:100%;">📲 Cobrar</button></a>', unsafe_allow_html=True)
                st.markdown("---")
    else:
        st.info("No hay cuentas pendientes por cobrar.")
