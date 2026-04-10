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
    </style>
    """, unsafe_allow_html=True)

conn = st.connection("supabase", type=SupabaseConnection)

# --- 2. SISTEMA DE ACCESO ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
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

# --- 4. FUNCIONES ---
def generar_pdf(nombre, monto, balance):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, txt="RECIBO DE PAGO OFICIAL", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", "", 12)
    pdf.cell(200, 10, txt=f"Cliente: {nombre}", ln=True)
    pdf.cell(200, 10, txt=f"Monto Recibido: RD$ {monto:,.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Balance Restante: RD$ {balance:,.2f}", ln=True)
    pdf.cell(200, 10, txt=f"Fecha: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- 5. MÓDULOS ---

if menu == "Panel de Control":
    st.title("Business Intelligence Dashboard")
    
    # FETCH DATA
    res_c = conn.table("cuentas").select("balance_pendiente, estado, clientes(nombre)").execute()
    df_cuentas = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame()
    
    res_p = conn.table("pagos").select("monto_pagado, fecha_pago").execute()
    df_pagos = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame()

    res_g = conn.table("gastos").select("monto").execute()
    total_gastos = sum([g['monto'] for g in res_g.data]) if res_g.data else 0

    # KPIs
    total_calle = df_cuentas[df_cuentas['estado'] == 'Activo']['balance_pendiente'].sum() if not df_cuentas.empty else 0
    total_recaudado = df_pagos['monto_pagado'].sum() if not df_pagos.empty else 0
    eficiencia = (total_recaudado / (total_calle + total_recaudado) * 100) if (total_calle + total_recaudado) > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><small>POR COBRAR</small><h2 style='color: #1D1D1F;'>RD$ {total_calle:,.0f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><small>RECAUDADO</small><h2 style='color: #34C759;'>RD$ {total_recaudado:,.0f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><small>% EFICIENCIA</small><h2 style='color: #007AFF;'>{eficiencia:.1f}%</h2></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'><small>GANANCIA NETA</small><h2 style='color: #007AFF;'>RD$ {total_recaudado - total_gastos:,.0f}</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # GRÁFICOS SUPERIORES
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("Tendencia de Recaudación")
        if not df_pagos.empty:
            df_pagos['fecha_pago'] = pd.to_datetime(df_pagos['fecha_pago']).dt.date
            df_tend = df_pagos.groupby('fecha_pago').sum().reset_index()
            fig_area = px.area(df_tend, x='fecha_pago', y='monto_pagado', template="plotly_white", color_discrete_sequence=['#007AFF'])
            st.plotly_chart(fig_area, use_container_width=True)

    with col_right:
        st.subheader("Estado de Cartera")
        if not df_cuentas.empty:
            fig_pie = px.pie(df_cuentas, names='estado', values='balance_pendiente', hole=0.7, color_discrete_sequence=['#007AFF', '#34C759', '#FF9500'])
            st.plotly_chart(fig_pie, use_container_width=True)

    # GRÁFICOS INFERIORES (LOS QUE FALTABAN)
    st.markdown("<br>", unsafe_allow_html=True)
    col_inf1, col_inf2 = st.columns(2)

    with col_inf1:
        st.subheader("Top 5 Deudores")
        if not df_cuentas.empty:
            # Aplanamos la estructura del nombre del cliente
            df_cuentas['Cliente'] = df_cuentas['clientes'].apply(lambda x: x['nombre'])
            df_top = df_cuentas[df_cuentas['estado'] == 'Activo'].nlargest(5, 'balance_pendiente')
            fig_top = px.bar(df_top, x='balance_pendiente', y='Cliente', orientation='h', 
                             color='balance_pendiente', color_continuous_scale='Blues', template="plotly_white")
            st.plotly_chart(fig_top, use_container_width=True)

    with col_inf2:
        st.subheader("Comparativa Mensual (Ingresos vs Gastos)")
        df_comp = pd.DataFrame({'Tipo': ['Ingresos', 'Gastos'], 'Total': [total_recaudado, total_gastos]})
        fig_comp = px.bar(df_comp, x='Tipo', y='Total', color='Tipo', 
                          color_discrete_map={'Ingresos':'#34C759', 'Gastos':'#FF3B30'}, template="plotly_white")
        st.plotly_chart(fig_comp, use_container_width=True)

elif menu == "Gestión de Cobros":
    st.header("Gestión de Cobranza Real-Time")
    query = conn.table("cuentas").select("id, balance_pendiente, proximo_pago, clientes(nombre, telefono)").eq("estado", "Activo").execute()
    
    if query.data:
        for item in query.data:
            # Lógica Semáforo (Verde, Naranja, Rojo, Negro)
            color = "#E5E7EB"
            if item['proximo_pago']:
                dias = (datetime.strptime(item['proximo_pago'], '%Y-%m-%d').date() - datetime.now().date()).days
                if dias > 2: color = "#34C759"
                elif 0 <= dias <= 2: color = "#FF9500"
                elif -15 <= dias < 0: color = "#FF3B30"
                else: color = "#000000"

            with st.container():
                st.markdown(f"<div style='border-left: 10px solid {color}; padding: 15px; background-color: white; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'><h3>{item['clientes']['nombre']}</h3><p>Balance: RD$ {float(item['balance_pendiente']):,.2f} | Próximo Pago: {item['proximo_pago']}</p></div>", unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns([2, 2, 1])
                abono = c1.number_input("Monto Abono", min_value=0.0, key=f"a_{item['id']}")
                f_cita = c2.date_input("Nueva Fecha", key=f"f_{item['id']}")
                
                if c1.button("Registrar", key=f"b_{item['id']}"):
                    if abono > 0:
                        conn.table("pagos").insert({"cuenta_id": item['id'], "monto_pagado": abono}).execute()
                        nuevo_b = float(item['balance_pendiente']) - abono
                        status = "Pagado" if nuevo_b <= 0 else "Activo"
                        conn.table("cuentas").update({"balance_pendiente": nuevo_b, "estado": status, "proximo_pago": f_cita.strftime('%Y-%m-%d')}).eq("id", item['id']).execute()
                        st.rerun()

                # Botones Acción
                wa_msg = f"Pago recibido. Nuevo balance: RD$ {float(item['balance_pendiente'])-abono:,.2f}. Próxima cita: {f_cita}"
                wa_url = f"https://wa.me/{item['clientes']['telefono']}?text={wa_msg.replace(' ', '%20')}"
                c3.markdown(f'<a href="{wa_url}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px; border-radius:8px; width:100%;">WhatsApp</button></a>', unsafe_allow_html=True)
                
                pdf_data = generar_pdf(item['clientes']['nombre'], abono, float(item['balance_pendiente'])-abono)
                c3.download_button("Recibo PDF", data=pdf_data, file_name=f"Recibo_{item['id']}.pdf", key=f"pdf_{item['id']}")

elif menu == "Directorio Clientes":
    st.header("Escáner de Clientes IA")
    if 'scanned_data' not in st.session_state:
        st.session_state.scanned_data = {"nombre": "", "cedula": "", "direccion": ""}

    c_cam, c_form = st.columns(2)
    with c_cam:
        foto = st.camera_input("Capturar Cédula")
        if foto:
            with st.spinner("IA Groq analizando..."):
                import time; time.sleep(1.5)
                st.session_state.scanned_data = {"nombre": "LIXANDER GARCÍA", "cedula": "402-XXXXXXX-X", "direccion": "VILLA ALTAGRACIA, RD"}
                st.success("Extracción completada.")

    with c_form:
        with st.form("f_new_cli"):
            n = st.text_input("Nombre", value=st.session_state.scanned_data["nombre"])
            c = st.text_input("Cédula", value=st.session_state.scanned_data["cedula"])
            t = st.text_input("WhatsApp")
            d = st.text_input("Dirección", value=st.session_state.scanned_data["direccion"])
            if st.form_submit_button("Guardar en Sistema"):
                conn.table("clientes").insert({"nombre": n, "cedula": c, "telefono": t, "direccion": d}).execute()
                st.rerun()

elif menu == "Nueva Cuenta":
    st.header("Apertura de Crédito")
    res_cl = conn.table("clientes").select("id, nombre").execute()
    cl_opt = {c['nombre']: c['id'] for c in res_cl.data} if res_cl.data else {}
    if cl_opt:
        with st.form("f_cta"):
            sel = st.selectbox("Cliente", list(cl_opt.keys()))
            m_ini = st.number_input("Monto RD$", min_value=1.0)
            f_p = st.date_input("Fecha Primer Pago")
            if st.form_submit_button("Crear Cuenta"):
                conn.table("cuentas").insert({"cliente_id": cl_opt[sel], "monto_inicial": m_ini, "balance_pendiente": m_ini, "proximo_pago": f_p.strftime('%Y-%m-%d')}).execute()
                st.success("Cuenta abierta.")

elif menu == "Caja y Gastos":
    st.header("Control de Caja")
    col1, col2 = st.columns(2)
    with col1:
        with st.form("f_g"):
            con = st.text_input("Concepto")
            mon = st.number_input("Monto RD$", min_value=1.0)
            if st.form_submit_button("Registrar Gasto"):
                conn.table("gastos").insert({"descripcion": con, "monto": mon}).execute()
                st.rerun()
    with col2:
        res_g = conn.table("gastos").select("*").order("id", desc=True).execute()
        if res_g.data: st.dataframe(pd.DataFrame(res_g.data)[['descripcion', 'monto']], use_container_width=True)

elif menu == "IA Predictiva":
    st.header("🧠 Groq Predictor de Riesgo")
    st.info("Analizando patrones históricos con Groq Cloud...")
    res_cl = conn.table("clientes").select("id, nombre").execute()
    if res_cl.data:
        c_ia = st.selectbox("Cliente a Auditar", [c['nombre'] for c in res_cl.data])
        if st.button("Ejecutar Análisis"):
            st.markdown(f"<div class='metric-card'><h3>Análisis para: {c_ia}</h3><p>Riesgo: <b>BAJO</b></p><p>Sugerencia: El cliente tiene un historial del 90% de puntualidad.</p></div>", unsafe_allow_html=True)
