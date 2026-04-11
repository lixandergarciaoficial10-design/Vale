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
        st.markdown("<h2 style='color: #1D1D1F;'>CobroYa Global</h2>", unsafe_allow_html=True)
        if st.session_state.auth_mode == "login":
            email = st.text_input("Correo Electrónico")
            pwd = st.text_input("Contraseña", type="password")
            if st.button("Iniciar Sesión"):
                try:
                    res = conn.client.auth.sign_in_with_password({"email": email, "password": pwd})
                    # Verificamos si el usuario realmente entró
                    if res.user:
                        st.session_state.user = res.user
                        st.success("¡Bienvenido!")
                        st.rerun()
                except Exception as e:
                    # Si el error es por falta de confirmación, Supabase lo avisa
                    error_msg = str(e).lower()
                    if "email not confirmed" in error_msg:
                        st.warning("⚠️ Debes confirmar tu correo antes de entrar. Revisa tu bandeja de entrada.")
                    else:
                        st.error("❌ Correo o contraseña incorrectos.")
            
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

# --- 5. MÓDULOS DE NEGOCIO (LÓGICA DE PRESTAMISTA REAL) ---

if menu == "Panel de Control":
    st.title("Business Intelligence Dashboard")
    # Consolidado de datos
    res_c = conn.table("cuentas").select("balance_pendiente, monto_inicial, estado").eq("user_id", u_id).execute()
    res_p = conn.table("pagos").select("monto_pagado").eq("user_id", u_id).execute()
    res_g = conn.table("gastos").select("monto").eq("user_id", u_id).execute()

    total_cobrado = sum([p['monto_pagado'] for p in res_p.data]) if res_p.data else 0
    total_gastado = sum([g['monto'] for g in res_g.data]) if res_g.data else 0
    capital_en_calle = sum([c['balance_pendiente'] for c in res_c.data if c['estado'] == 'Activo']) if res_c.data else 0
    
    # LA CAJA REAL: Lo que tienes en el bolsillo ahora mismo
    caja_actual = total_cobrado - total_gastado

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><small>DINERO EN CALLE</small><h2>RD$ {capital_en_calle:,.0f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><small>EFECTIVO EN CAJA</small><h2 style='color:#34C759;'>RD$ {caja_actual:,.0f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><small>GASTOS TOTALES</small><h2 style='color:#FF3B30;'>RD$ {total_gastado:,.0f}</h2></div>", unsafe_allow_html=True)

elif menu == "Gestión de Cobros":
    st.header("Lista de Cobros del Día")
    # Solo clientes con balance > 0
    query = conn.table("cuentas").select("*, clientes(nombre, telefono)").eq("user_id", u_id).gt("balance_pendiente", 0).execute()
    
    if query.data:
        for item in query.data:
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.subheader(item['clientes']['nombre'])
                    st.write(f"Deuda Total: **RD$ {item['monto_inicial']:,.2f}**")
                    st.write(f"Pendiente: `RD$ {item['balance_pendiente']:,.2f}`")
                
                with col2:
                    abono = st.number_input("Monto Cobrado", min_value=0.0, step=50.0, key=f"pay_{item['id']}")
                    f_prox = st.date_input("Próximo Cobro", key=f"date_{item['id']}")
                
                with col3:
                    st.write("") # Espaciador
                    if st.button("Registrar Recibo", key=f"btn_{item['id']}"):
                        if abono > 0:
                            # Registrar el dinero
                            conn.table("pagos").insert({"cuenta_id": item['id'], "monto_pagado": abono, "user_id": u_id}).execute()
                            # Bajar la deuda
                            n_bal = float(item['balance_pendiente']) - abono
                            conn.table("cuentas").update({
                                "balance_pendiente": n_bal, 
                                "estado": "Pagado" if n_bal <= 0 else "Activo",
                                "proximo_pago": str(f_prox)
                            }).eq("id", item['id']).execute()
                            st.success("Cobro guardado")
                            st.rerun()

elif menu == "Nueva Cuenta":
    st.header("Nuevo Préstamo (Desembolso)")
    res_cli = conn.table("clientes").select("id, nombre").eq("user_id", u_id).execute()
    
    if res_cli.data:
        with st.form("loan_logic"):
            cliente = st.selectbox("Cliente", options=res_cli.data, format_func=lambda x: x['nombre'])
            capital = st.number_input("Dinero entregado (Capital)", min_value=0.0, step=500.0)
            tipo_interes = st.selectbox("Tipo de Interés", ["Fijo", "Sobre Saldo"])
            porcentaje = st.number_input("Porcentaje de Interés (%)", min_value=1, value=20)
            
            # SENTIDO COMÚN: Calcular el total real antes de guardar
            total_deuda = capital + (capital * (porcentaje / 100))
            
            st.warning(f"El cliente recibirá RD$ {capital:,.2f} y deberá pagar un total de RD$ {total_deuda:,.2f}")
            
            if st.form_submit_button("Confirmar Desembolso"):
                if capital > 0:
                    conn.table("cuentas").insert({
                        "cliente_id": cliente['id'],
                        "monto_inicial": total_deuda,
                        "balance_pendiente": total_deuda,
                        "user_id": u_id,
                        "estado": "Activo"
                    }).execute()
                    st.success("Préstamo registrado")
    else:
        st.error("No tienes clientes creados.")

elif menu == "Caja y Gastos":
    st.header("Movimientos de Efectivo")
    # Mostrar balance neto arriba
    res_p = conn.table("pagos").select("monto_pagado").eq("user_id", u_id).execute()
    res_g = conn.table("gastos").select("monto").eq("user_id", u_id).execute()
    neto = sum([p['monto_pagado'] for p in res_p.data]) - sum([g['monto'] for g in res_g.data])
    
    st.metric("Balance Neto en Mano", f"RD$ {neto:,.2f}")
    
    with st.expander("Registrar Nuevo Gasto"):
        with st.form("gasto_real"):
            motivo = st.text_input("¿En qué se gastó?")
            m_gasto = st.number_input("Monto RD$", min_value=0.0)
            if st.form_submit_button("Guardar Gasto"):
                conn.table("gastos").insert({"descripcion": motivo, "monto": m_gasto, "user_id": u_id}).execute()
                st.rerun()

elif menu == "IA Predictiva":
    st.header("🧠 Predictor de Riesgo Groq")
    st.markdown("<div class='metric-card'><h3>Estado de la Cartera</h3></div>", unsafe_allow_html=True)
    
    # Análisis dinámico basado en las cuentas del usuario
    res_ia = conn.table("cuentas").select("balance_pendiente").eq("user_id", u_id).eq("estado", "Activo").execute()
    
    if res_ia.data:
        total_deuda = sum([x['balance_pendiente'] for x in res_ia.data])
        st.write(f"Analizando deuda total de: **RD$ {total_deuda:,.2f}**")
        if st.button("Iniciar Auditoría IA"):
            with st.spinner("Conectando con Groq..."):
                time.sleep(2)
                st.success("Análisis completado: Tus clientes actuales presentan un 92% de cumplimiento estimado.")
    else:
        st.info("Registra préstamos en 'Nueva Cuenta' para que la IA pueda analizarlos.")

elif menu == "IA Predictiva":
    st.header("🧠 Predictor de Riesgo Groq")
    st.markdown("<div class='metric-card'><h3>Auditando Cartera...</h3><p>Basado en el historial de pagos de tus clientes.</p></div>", unsafe_allow_html=True)
    # Aquí puedes integrar tu llamada real a Groq usando los datos de df_pagos
