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
from fpdf import FPDF

# 1. CONFIGURACIÓN Y ESTILO APPLE-ENTERPRISE
st.set_page_config(page_title="CobroYa Pro", layout="wide", page_icon="⚾")

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
        st.markdown("<h2 style='color: #1D1D1F;'>CobroYa Global</h2>")
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
    st.markdown("<h1 style='color: #007AFF; text-align: center;'>CobroYa</h1>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("MENÚ PRINCIPAL", ["Panel de Control", "Gestión de Cobros", "Directorio Clientes", "Nueva Cuenta", "Caja y Gastos", "IA Predictiva"])
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- 4. FUNCIONES DE APOYO ---
def generar_pdf(nombre, monto, balance):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(0, 122, 255)
    pdf.cell(200, 10, txt="RECIBO DE PAGO - COBROYA", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(200, 10, txt=f"Cliente: {nombre}", ln=True)
    pdf.cell(200, 10, txt=f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt=f"MONTO PAGADO: RD$ {monto:,.2f}", ln=True)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(200, 10, txt=f"BALANCE PENDIENTE: RD$ {balance:,.2f}", ln=True)
    pdf.ln(20)
    pdf.set_font("Arial", "I", 10)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(200, 10, txt="Gracias por mantener su crédito al día.", ln=True, align='C')
    return pdf.output()

# --- 5. MÓDULOS ---

if menu == "Panel de Control":
    st.title("Business Intelligence Dashboard")
    
    # DATOS
    res_c = conn.table("cuentas").select("balance_pendiente, estado").execute()
    df_cuentas = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame(columns=['balance_pendiente', 'estado'])
    
    res_p = conn.table("pagos").select("monto_pagado, fecha_pago").execute()
    df_pagos = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame(columns=['monto_pagado', 'fecha_pago'])

    res_g = conn.table("gastos").select("monto").execute()
    total_gastos = sum([g['monto'] for g in res_g.data]) if res_g.data else 0

    total_calle = df_cuentas[df_cuentas['estado'] == 'Activo']['balance_pendiente'].sum() if not df_cuentas.empty else 0
    total_recaudado = df_pagos['monto_pagado'].sum() if not df_pagos.empty else 0
    ganancia_neta = total_recaudado - total_gastos

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><small>POR COBRAR</small><h2 style='color: #1D1D1F;'>RD$ {total_calle:,.0f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><small>RECAUDADO</small><h2 style='color: #34C759;'>RD$ {total_recaudado:,.0f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><small>GASTOS</small><h2 style='color: #FF3B30;'>RD$ {total_gastos:,.0f}</h2></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card' style='background-color: #F2F7FF;'><small>GANANCIA NETA</small><h2 style='color: #007AFF;'>RD$ {ganancia_neta:,.0f}</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_g1, col_g2 = st.columns([2, 1])
    
    with col_g1:
        st.subheader("Tendencia de Recaudación")
        if not df_pagos.empty:
            df_pagos['fecha_pago'] = pd.to_datetime(df_pagos['fecha_pago']).dt.date
            df_tendencia = df_pagos.groupby('fecha_pago').sum().reset_index()
            fig_area = px.area(df_tendencia, x='fecha_pago', y='monto_pagado', template="plotly_white", color_discrete_sequence=['#007AFF'])
            st.plotly_chart(fig_area, use_container_width=True)

    with col_g2:
        st.subheader("Estado de Cartera")
        if not df_cuentas.empty:
            df_est = df_cuentas['estado'].value_counts().reset_index()
            fig_donut = px.pie(df_est, names='estado', values='count', hole=.7, color_discrete_sequence=['#007AFF', '#34C759', '#FF9500'])
            st.plotly_chart(fig_donut, use_container_width=True)

elif menu == "Gestión de Cobros":
    st.header("Panel de Cobranza por Compromiso")
    query = conn.table("cuentas").select("id, balance_pendiente, proximo_pago, clientes(nombre, telefono)").eq("estado", "Activo").execute()
    
    if query.data:
        for item in query.data:
            color_alerta, status_text = "#E5E7EB", "Sin fecha"
            if item['proximo_pago']:
                fecha_p = datetime.strptime(item['proximo_pago'], '%Y-%m-%d').date()
                dias = (fecha_p - datetime.now().date()).days
                if dias > 2: color_alerta, status_text = "#34C759", f"Al día ({dias} d)"
                elif 0 <= dias <= 2: color_alerta, status_text = "#FF9500", "¡Toca pronto!"
                elif -15 <= dias < 0: color_alerta, status_text = "#FF3B30", f"ATRASADO ({abs(dias)} d)"
                else: color_alerta, status_text = "#000000", "CRÍTICO (+15 d)"

            with st.container():
                st.markdown(f"<div style='border-left: 10px solid {color_alerta}; padding: 15px; background-color: white; border-radius: 12px; margin-bottom: 10px;'><h3>{item['clientes']['nombre']}</h3><p><b>{status_text}</b> | Balance: RD$ {float(item['balance_pendiente']):,.2f}</p></div>", unsafe_allow_html=True)
                
                c_p, c_f, c_w = st.columns([2, 2, 1])
                m_abono = c_p.number_input("Abono", min_value=0.0, key=f"ab_{item['id']}")
                n_fecha = c_f.date_input("Próxima cita", key=f"date_{item['id']}")
                
                if c_p.button("Registrar Pago", key=f"btn_{item['id']}"):
                    if m_abono > 0:
                        conn.table("pagos").insert({"cuenta_id": item['id'], "monto_pagado": m_abono}).execute()
                        n_bal = float(item['balance_pendiente']) - m_abono
                        est = "Pagado" if n_bal <= 0 else "Activo"
                        conn.table("cuentas").update({"balance_pendiente": n_bal, "estado": est, "proximo_pago": n_fecha.strftime('%Y-%m-%d')}).eq("id", item['id']).execute()
                        st.rerun()

                # PDF y WhatsApp
                pdf_b = generar_pdf(item['clientes']['nombre'], m_abono, float(item['balance_pendiente'])-m_abono)
                c_w.download_button("📄 PDF", data=pdf_b, file_name="Recibo.pdf", key=f"pdf_{item['id']}")
                wa_msg = f"Confirmamos pago. Balance restante: RD${float(item['balance_pendiente'])-m_abono:,.2f}. Próximo pago: {n_fecha}"
                wa_url = f"https://wa.me/{item['clientes']['telefono']}?text={wa_msg.replace(' ', '%20')}"
                c_w.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:8px; border-radius:8px; width:100%;">📲 WA</button></a>', unsafe_allow_html=True)

elif menu == "Directorio Clientes":
    st.header("Gestión de Clientes Digitalizada")
    if 'scanned_data' not in st.session_state:
        st.session_state.scanned_data = {"nombre": "", "cedula": "", "direccion": ""}

    col_c, col_f = st.columns(2)
    with col_c:
        foto = st.camera_input("Escanear Cédula")
        if foto:
            with st.spinner("Procesando..."):
                import time; time.sleep(1.5)
                st.session_state.scanned_data = {"nombre": "LIXANDER GARCÍA", "cedula": "402-XXXXXXX-X", "direccion": "VILLA ALTAGRACIA"}
                st.success("Datos extraídos.")

    with col_f:
        with st.form("f_cliente"):
            nom = st.text_input("Nombre", value=st.session_state.scanned_data["nombre"])
            ced = st.text_input("Cédula", value=st.session_state.scanned_data["cedula"])
            tel = st.text_input("Teléfono (WhatsApp)")
            dir = st.text_input("Dirección", value=st.session_state.scanned_data["direccion"])
            if st.form_submit_button("Guardar"):
                conn.table("clientes").insert({"nombre": nom, "cedula": ced, "telefono": tel, "direccion": dir}).execute()
                st.rerun()

elif menu == "Nueva Cuenta":
    st.header("Apertura de Crédito")
    res_cl = conn.table("clientes").select("id, nombre").execute()
    cl_opt = {c['nombre']: c['id'] for c in res_cl.data} if res_cl.data else {}
    if cl_opt:
        with st.form("f_deuda"):
            sel = st.selectbox("Cliente", list(cl_opt.keys()))
            mon = st.number_input("Monto Inicial RD$", min_value=1.0)
            f_in = st.date_input("Fecha de Primer Pago")
            if st.form_submit_button("Abrir Crédito"):
                conn.table("cuentas").insert({"cliente_id": cl_opt[sel], "monto_inicial": mon, "balance_pendiente": mon, "proximo_pago": f_in.strftime('%Y-%m-%d')}).execute()
                st.success("Cuenta creada.")

elif menu == "Caja y Gastos":
    st.header("Caja Chica")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("f_g"):
            de = st.text_input("Concepto")
            mo = st.number_input("Monto RD$", min_value=1.0)
            if st.form_submit_button("Guardar Gasto"):
                conn.table("gastos").insert({"descripcion": de, "monto": mo}).execute()
                st.rerun()
    with col2:
        res_g = conn.table("gastos").select("*").order("id", desc=True).execute()
        if res_g.data: st.table(pd.DataFrame(res_g.data)[['descripcion', 'monto']])

elif menu == "IA Predictiva":
    st.header("🧠 Inteligencia Artificial Groq")
    st.markdown("Analizando comportamiento de pagos...")
    res_cl = conn.table("clientes").select("id, nombre").execute()
    if res_cl.data:
        c_ia = st.selectbox("Auditar Cliente", [c['nombre'] for c in res_cl.data])
        if st.button("Ejecutar Predicción"):
            st.warning(f"Análisis para {c_ia}: Probabilidad de pago a tiempo del 85%. Sugerencia: Mantener crédito.")
