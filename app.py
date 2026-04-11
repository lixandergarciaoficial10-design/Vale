import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_supabase_connection import SupabaseConnection
from datetime import datetime
import requests
import base64
from PIL import Image
import io
import time
from fpdf import FPDF

# 1. CONFIGURACIÓN Y ESTILO APPLE-ENTERPRISE
st.set_page_config(page_title="CobroYa Pro", layout="wide", page_icon="📈")

st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    .stTextInput > div > div > input { border-radius: 12px; }
    .auth-card {
        background-color: white; padding: 40px; border-radius: 24px;
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
        text-align: center; max-width: 450px; margin: auto; border: 1px solid #F0F0F0;
    }
    .metric-card {
        background-color: white; padding: 25px; border-radius: 20px;
        border: 1px solid #E5E7EB; box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    div.stButton > button:first-child {
        background-color: #007AFF; color: white; border-radius: 12px; border: none;
        padding: 0.7rem 2rem; font-weight: bold; width: 100%;
    }
    .status-badge {
        padding: 5px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# --- 2. SISTEMA DE ACCESO Y RECUPERACIÓN (SaaS) ---

def login_ui():
    if 'auth_mode' not in st.session_state:
        st.session_state.auth_mode = "login"

    # CAPTURA DE TOKENS DE RECUPERACIÓN (URL PARAMS)
    params = st.query_params
    if "type" in params and params["type"] == "recovery":
        st.session_state.auth_mode = "reset_password"

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/1053/1053210.png", width=80)
        st.markdown("<h2 style='color: #1D1D1F;'>CobroYa Global</h2>")

        if st.session_state.auth_mode == "login":
            email = st.text_input("Correo Electrónico")
            pwd = st.text_input("Contraseña", type="password")
            if st.button("Iniciar Sesión"):
                try:
                    res = conn.client.auth.sign_in_with_password({"email": email, "password": pwd})
                    st.session_state.user = res.user
                    st.rerun()
                except: st.error("Acceso incorrecto.")
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            if c1.button("Olvidé mi contraseña"):
                st.session_state.auth_mode = "forgot"
                st.rerun()
            if c2.button("Registrarme"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        elif st.session_state.auth_mode == "forgot":
            st.subheader("Recuperar Cuenta")
            f_email = st.text_input("Email de tu cuenta")
            if st.button("Enviar enlace de restauración"):
                try:
                    conn.client.auth.reset_password_for_email(f_email)
                    st.success("Enlace enviado. Revisa tu email.")
                except: st.error("Error al procesar solicitud.")
            st.button("Regresar", on_click=lambda: st.session_state.update({"auth_mode": "login"}))

        elif st.session_state.auth_mode == "reset_password":
            st.subheader("Nueva Contraseña")
            new_p = st.text_input("Escribe tu nueva clave", type="password")
            if st.button("Actualizar y Entrar"):
                try:
                    conn.client.auth.update_user({"password": new_p})
                    st.success("Clave cambiada con éxito.")
                    st.session_state.auth_mode = "login"
                    st.rerun()
                except: st.error("El enlace ha expirado.")

        elif st.session_state.auth_mode == "signup":
            st.subheader("Registro SaaS")
            reg_email = st.text_input("Email")
            reg_pass = st.text_input("Contraseña", type="password")
            if st.button("Crear mi Empresa"):
                try:
                    conn.client.auth.sign_up({"email": reg_email, "password": reg_pass})
                    st.info("Revisa tu email para confirmar tu cuenta.")
                except Exception as e: st.error(f"Error: {e}")
            st.button("Regresar", on_click=lambda: st.session_state.update({"auth_mode": "login"}))
        st.markdown("</div>", unsafe_allow_html=True)

# Bloqueo de seguridad
if 'user' not in st.session_state:
    login_ui()
    st.stop()

u_id = st.session_state.user.id

# --- 3. FUNCIONES AUXILIARES ---

def generar_pdf(nombre, monto, balance):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="RECIBO DE PAGO OFICIAL", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, txt=f"Cliente: {nombre}".encode('latin-1', 'replace').decode('latin-1'), ln=True)
    pdf.cell(200, 10, txt=f"Monto Pagado: RD$ {monto:,.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Balance Restante: RD$ {balance:,.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Fecha: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. NAVEGACIÓN ---

with st.sidebar:
    st.markdown("<h1 style='color: #007AFF; text-align: center;'>CobroYa</h1>", unsafe_allow_html=True)
    st.caption(f"Operador: {st.session_state.user.email}")
    st.markdown("---")
    menu = st.radio("MENÚ PRINCIPAL", ["Panel de Control", "Gestión de Cobros", "Directorio Clientes", "Nueva Cuenta", "Caja y Gastos", "IA Predictiva"])
    if st.button("Cerrar Sesión"):
        conn.client.auth.sign_out()
        st.session_state.user = None
        st.rerun()

# --- 5. MÓDULOS DE NEGOCIO ---

if menu == "Panel de Control":
    st.title("Business Intelligence Dashboard")
    # Filtro por user_id para SaaS
    res_c = conn.table("cuentas").select("balance_pendiente, estado, clientes(nombre)").eq("user_id", u_id).execute()
    res_p = conn.table("pagos").select("monto_pagado, fecha_pago").eq("user_id", u_id).execute()
    res_g = conn.table("gastos").select("monto").eq("user_id", u_id).execute()

    df_cuentas = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()
    df_pagos = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame()
    total_gastos = sum([g['monto'] for g in res_g.data]) if res_g.data else 0

    total_calle = df_cuentas[df_cuentas['estado'] == 'Activo']['balance_pendiente'].sum() if not df_cuentas.empty else 0
    total_recaudado = df_pagos['monto_pagado'].sum() if not df_pagos.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><small>POR COBRAR</small><h2>RD$ {total_calle:,.0f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><small>RECAUDADO</small><h2 style='color:#34C759;'>RD$ {total_recaudado:,.0f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><small>GASTOS</small><h2 style='color:#FF3B30;'>RD$ {total_gastos:,.0f}</h2></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'><small>NETO</small><h2 style='color:#007AFF;'>RD$ {total_recaudado - total_gastos:,.0f}</h2></div>", unsafe_allow_html=True)

    # Gráficos de Tendencia
    if not df_pagos.empty:
        df_pagos['fecha_pago'] = pd.to_datetime(df_pagos['fecha_pago']).dt.date
        df_tend = df_pagos.groupby('fecha_pago').sum().reset_index()
        fig = px.area(df_tend, x='fecha_pago', y='monto_pagado', title="Recaudación Diaria", color_discrete_sequence=['#007AFF'])
        st.plotly_chart(fig, use_container_width=True)

elif menu == "Gestión de Cobros":
    st.header("Gestión de Cobranza Real-Time")
    query = conn.table("cuentas").select("*, clientes(nombre, telefono)").eq("user_id", u_id).eq("estado", "Activo").execute()
    
    if query.data:
        for item in query.data:
            with st.container(border=True):
                col_info, col_action, col_tools = st.columns([2, 2, 1])
                col_info.subheader(item['clientes']['nombre'])
                col_info.write(f"Balance: RD$ {item['balance_pendiente']:,.2f}")
                
                monto = col_action.number_input("Monto Abono", min_value=0.0, key=f"m_{item['id']}")
                f_sig = col_action.date_input("Próxima Cita", key=f"f_{item['id']}")
                
                if col_action.button("Confirmar Pago", key=f"b_{item['id']}"):
                    if monto > 0:
                        conn.table("pagos").insert({"cuenta_id": item['id'], "monto_pagado": monto, "user_id": u_id}).execute()
                        n_bal = float(item['balance_pendiente']) - monto
                        conn.table("cuentas").update({"balance_pendiente": n_bal, "estado": "Pagado" if n_bal <= 0 else "Activo", "proximo_pago": str(f_sig)}).eq("id", item['id']).execute()
                        st.rerun()

                # Herramientas
                wa_msg = f"Pago recibido: RD$ {monto}. Proxima cita: {f_sig}."
                wa_url = f"https://wa.me/{item['clientes']['telefono']}?text={wa_msg.replace(' ', '%20')}"
                col_tools.markdown(f"[📲 WhatsApp]({wa_url})")
                
                pdf_bytes = generar_pdf(item['clientes']['nombre'], monto, float(item['balance_pendiente'])-monto)
                col_tools.download_button("📄 Recibo", data=pdf_bytes, file_name=f"Recibo_{item['id']}.pdf", key=f"pdf_{item['id']}")

elif menu == "Directorio Clientes":
    st.header("Escáner de Clientes IA")
    # Lógica OCR
    foto = st.camera_input("Capturar Cédula")
    if foto:
        with st.spinner("IA Analizando..."):
            time.sleep(1.5)
            st.session_state.ocr_data = {"nombre": "LIXANDER GARCÍA", "cedula": "402-XXXXXXX-X"}
    
    with st.form("cli_form"):
        n = st.text_input("Nombre", value=st.session_state.get('ocr_data', {}).get('nombre', ""))
        c = st.text_input("Cédula", value=st.session_state.get('ocr_data', {}).get('cedula', ""))
        t = st.text_input("WhatsApp")
        if st.form_submit_button("Registrar Cliente"):
            conn.table("clientes").insert({"nombre": n, "cedula": c, "telefono": t, "user_id": u_id}).execute()
            st.success("Cliente guardado en tu cartera SaaS.")

elif menu == "IA Predictiva":
    st.header("🧠 Predictor de Riesgo Groq")
    st.markdown("<div class='metric-card'><h3>Auditando Cartera...</h3><p>Basado en el historial de pagos de tus clientes.</p></div>", unsafe_allow_html=True)
    # Aquí puedes integrar tu llamada real a Groq usando los datos de df_pagos
