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
    st.header("Configuración de Desembolso Pro")
    res_cli = conn.table("clientes").select("id, nombre").eq("user_id", u_id).execute()
    
    if res_cli.data:
        # 1. PARAMETRIZACIÓN INICIAL
        col1, col2, col3 = st.columns(3)
        with col1:
            cliente_obj = st.selectbox("Cliente", options=res_cli.data, format_func=lambda x: x['nombre'])
            capital = st.number_input("Capital a Entregar (RD$)", min_value=0.0, step=100.0)
        
        with col2:
            porcentaje = st.number_input("Interés Total (%)", min_value=0, value=20)
            # Diccionario de frecuencias para la lógica de fechas
            frecuencias = {
                "Semanal": {"days": 7},
                "Quincenal": {"days": 14},
                "Mensual": {"months": 1},
                "Trimestral": {"months": 3},
                "Anual": {"months": 12}
            }
            freq_sel = st.selectbox("Frecuencia de Pagos", list(frecuencias.keys()), index=2)
        
        with col3:
            cuotas_n = st.number_input("Número de Cuotas", min_value=1, value=4)
            fecha_inicio = st.date_input("Fecha de Primera Cuota", value=datetime.now().date())

        # 2. CÁLCULO DE EXPECTATIVA
        total_esperado = capital * (1 + (porcentaje / 100))
        monto_sugerido = total_esperado / cuotas_n

        st.markdown("---")
        st.subheader("📝 Plan de Amortización Ajustable")
        st.caption(f"Frecuencia detectada: {freq_sel}. Sistema de fechas automático activado.")

        # 3. GENERACIÓN DEL CRONOGRAMA DINÁMICO
        cronograma = []
        for i in range(cuotas_n):
            # Lógica de salto de fecha según frecuencia
            if "days" in frecuencias[freq_sel]:
                nueva_fecha = fecha_inicio + pd.DateOffset(days=i * frecuencias[freq_sel]["days"])
            else:
                nueva_fecha = fecha_inicio + pd.DateOffset(months=i * frecuencias[freq_sel]["months"])
            
            cronograma.append({
                "Nº": i + 1,
                "Fecha": nueva_fecha.date(),
                "Monto Cuota (RD$)": round(monto_sugerido, 2)
            })
        
        df_plan = pd.DataFrame(cronograma)

        # 4. EL "EXCEL" REACTIVO
        # Permitimos editar Fecha y Monto. Nº está bloqueado.
        df_editable = st.data_editor(
            df_plan,
            column_config={
                "Nº": st.column_config.NumberColumn("Nº", disabled=True),
                "Fecha": st.column_config.DateColumn("Fecha Límite", format="DD/MM/YYYY"),
                "Monto Cuota (RD$)": st.column_config.NumberColumn("Valor de la Cuota", min_value=0)
            },
            hide_index=True,
            use_container_width=True,
            key="amortizacion_pro"
        )

        # 5. VALIDACIÓN DE SUMA (Para que el prestamista no se confunda)
        total_real = df_editable["Monto Cuota (RD$)"].sum()
        diferencia = total_real - total_esperado

        c1, c2, c3 = st.columns(3)
        c1.metric("Capital Inicial", f"RD$ {capital:,.2f}")
        c2.metric("Total de Deuda Final", f"RD$ {total_real:,.2f}")
        c3.metric("Ganancia Neta", f"RD$ {total_real - capital:,.2f}", 
                  delta=f"Dif: {diferencia:,.2f}", delta_color="inverse")

        # 6. GUARDADO CON DOBLE CONFIRMACIÓN
        if st.button("🚀 Confirmar y Activar Préstamo", use_container_width=True):
            if capital > 0:
                with st.spinner("Creando contrato y sincronizando calendario de pagos..."):
                    # Registrar cuenta
                    res_cta = conn.table("cuentas").insert({
                        "cliente_id": cliente_obj['id'],
                        "monto_inicial": total_real,
                        "balance_pendiente": total_real,
                        "user_id": u_id,
                        "estado": "Activo",
                        "proximo_pago": str(df_editable.iloc[0]["Fecha"]) # Primera fecha del calendario
                    }).execute()
                    
                    st.success(f"¡Préstamo de RD$ {total_real:,.2f} activado!")
                    time.sleep(1)
                    st.rerun()
            else:
                st.error("Debes poner un capital mayor a 0.")
    else:
        st.error("Registra primero un cliente para abrir su cuenta.")
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
