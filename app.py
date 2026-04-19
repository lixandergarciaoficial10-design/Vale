import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_supabase_connection import SupabaseConnection
from datetime import datetime, date, timedelta
import requests
import base64
from PIL import Image
import io
import time
from fpdf import FPDF
from groq import Groq
from io import BytesIO
import qrcode
import datetime as dt

# =========================================================
# 1. CONFIGURACIÓN DE PÁGINA Y UX/UI DE ALTO NIVEL
# =========================================================
st.set_page_config(
    page_title="CobroYa Pro | Financial Data Intelligence", 
    layout="wide", 
    page_icon="📈",
    initial_sidebar_state="expanded"
)

# Diseño de Interfaz Estilo SaaS Moderno (Apple/Stripe Design)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #FBFBFD; }
    
    /* Contenedores principales */
    .main { background-color: #FBFBFD; }
    
    /* Tarjetas de Métricas */
    .metric-card {
        background-color: white; 
        padding: 24px; 
        border-radius: 16px;
        border: 1px solid #F0F0F2; 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    
    /* Botones Profesionales */
    div.stButton > button:first-child {
        background-color: #007AFF; 
        color: white; 
        border-radius: 10px; 
        border: none;
        padding: 0.6rem 1.5rem; 
        font-weight: 600; 
        width: 100%;
        transition: all 0.2s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #0063CC;
        box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
    }
    
    /* Inputs Estilizados */
    .stTextInput > div > div > input, .stNumberInput > div > div > input {
        border-radius: 10px !important;
    }

    /* Card de Autenticación */
    .auth-card {
        background-color: white; 
        padding: 48px; 
        border-radius: 28px;
        box-shadow: 0 25px 50px -12px rgba(0,0,0,0.1);
        text-align: center; 
        max-width: 440px; 
        margin: auto; 
        border: 1px solid #E5E7EB;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================================================
# 2. CONEXIÓN Y PERSISTENCIA DE DATOS (SUPABASE)
# =========================================================
conn = st.connection("supabase", type=SupabaseConnection)

# --- SISTEMA DE AUTENTICACIÓN ---
def login_ui():
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        st.image("https://cdn-icons-png.flaticon.com/512/1053/1053210.png", width=70)
        st.markdown("<h2 style='color: #1D1D1F; font-weight: 700;'>CobroYa Pro</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #86868B;'>Ingeniería de Datos aplicada a Préstamos</p>", unsafe_allow_html=True)
        
        email = st.text_input("Usuario (Email)", placeholder="tu@empresa.com")
        pwd = st.text_input("Contraseña", type="password", placeholder="••••••••")
        
        if st.button("Acceder al Panel"):
            try:
                res = conn.client.auth.sign_in_with_password({"email": email, "password": pwd})
                if res.user:
                    st.session_state.user = res.user
                    st.rerun()
            except Exception as e:
                st.error("Credenciales incorrectas o cuenta no verificada.")
        
        st.markdown("<hr style='margin: 20px 0;'>", unsafe_allow_html=True)
        if st.button("¿Olvidaste tu contraseña?"):
            st.info("Contacta al administrador del sistema.")
        st.markdown("</div>", unsafe_allow_html=True)

if 'user' not in st.session_state:
    login_ui()
    st.stop()

# ID Único del usuario para todas las consultas
u_id = st.session_state.user.id

# =========================================================
# 3. CARGA DE CONFIGURACIÓN DE NEGOCIO (SINGLETON)
# =========================================================
if "config_cargada" not in st.session_state or not st.session_state["config_cargada"]:
    try:
        res_c = conn.table("configuracion").select("*").eq("user_id", u_id).execute()
        if res_c.data:
            conf = res_c.data[0]
            st.session_state["mis_clausulas"] = conf.get("clausulas", "Sujeto a términos y condiciones.")
            st.session_state["mi_logo"] = conf.get("logo_base64", None)
            st.session_state["nombre_negocio"] = conf.get("nombre_negocio", "Mi Negocio")
            st.session_state["direccion_negocio"] = conf.get("direccion_negocio", "N/A")
            st.session_state["telefono_negocio"] = conf.get("telefono_negocio", "N/A")
            st.session_state["rnc"] = conf.get("rnc", "N/A")
            st.session_state["config_cargada"] = True
        else:
            # Valores por defecto para nuevos usuarios
            st.session_state["nombre_negocio"] = "CobroYa Pro"
            st.session_state["config_cargada"] = True
    except Exception as e:
        st.warning(f"Sincronizando configuración... {e}")

# =========================================================
# 4. MOTOR DE DATOS (FETCHING)
# =========================================================
@st.cache_data(ttl=300)
def load_all_data(user_id):
    """Obtiene todas las tablas de golpe para reducir latencia."""
    clientes = conn.table("clientes").select("*").eq("user_id", user_id).execute()
    prestamos = conn.table("prestamos").select("*, clientes(nombre)").eq("user_id", user_id).execute()
    pagos = conn.table("pagos").select("*").eq("user_id", user_id).execute()
    gastos = conn.table("gastos").select("*").eq("user_id", user_id).execute()
    
    return (
        pd.DataFrame(clientes.data), 
        pd.DataFrame(prestamos.data), 
        pd.DataFrame(pagos.data),
        pd.DataFrame(gastos.data)
    )

df_clientes, df_prestamos, df_pagos, df_gastos = load_all_data(u_id)

# =========================================================
# 5. UTILIDADES DE FORMATO Y CONVERSIÓN
# =========================================================
def get_image_download_link(img, filename="foto.png"):
    """Convierte imagen PIL a link de descarga."""
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    href = f'<a href="data:image/png;base64,{img_str}" download="{filename}">Descargar Foto</a>'
    return href

# =========================================================
# 6. MOTOR FINANCIERO: AMORTIZACIÓN Y CÁLCULOS
# =========================================================

def calcular_tabla_amortizacion(monto, tasa_anual, cuotas, frecuencia, fecha_inicio=None):
    """
    Genera la proyección de pagos detallada.
    Soporta: Semanal, Quincenal, Mensual.
    """
    if fecha_inicio is None:
        fecha_pago = datetime.now()
    else:
        fecha_pago = datetime.combine(fecha_inicio, datetime.min.time())

    tasa_decimal = tasa_anual / 100
    
    # Ajuste de tasa y saltos según frecuencia
    if frecuencia == "Mensual":
        tasa_periodo = tasa_decimal / 12
        dias_salto = 30
    elif frecuencia == "Quincenal":
        tasa_periodo = tasa_decimal / 24
        dias_salto = 15
    else: # Semanal
        tasa_periodo = tasa_decimal / 52
        dias_salto = 7
        
    # Cálculo de Cuota Fija (Método Francés)
    # Formula: R = P [ i(1 + i)^n ] / [ (1 + i)^n – 1 ]
    if tasa_periodo > 0:
        cuota_fija = (monto * tasa_periodo) / (1 - (1 + tasa_periodo)**-cuotas)
    else:
        cuota_fija = monto / cuotas
    
    tabla = []
    saldo_restante = monto
    
    for i in range(1, cuotas + 1):
        interes_cuota = saldo_restante * tasa_periodo
        capital_cuota = cuota_fija - interes_cuota
        saldo_restante -= capital_cuota
        fecha_pago += timedelta(days=dias_salto)
        
        tabla.append({
            "No.": i,
            "Fecha de Pago": fecha_pago.strftime('%d/%m/%Y'),
            "Cuota": round(cuota_fija, 2),
            "Capital": round(capital_cuota, 2),
            "Interés": round(interes_cuota, 2),
            "Balance": round(max(0, saldo_restante), 2)
        })
    return pd.DataFrame(tabla)

# =========================================================
# 7. GENERACIÓN DE DOCUMENTOS (PDF Y QR)
# =========================================================

def generar_recibo_pdf(datos_pago, cliente_nombre):
    """Crea un recibo con estándares bancarios."""
    pdf = FPDF()
    pdf.add_page()
    
    # --- Encabezado ---
    if st.session_state.get("mi_logo"):
        try:
            logo_data = base64.b64decode(st.session_state["mi_logo"])
            logo_img = Image.open(io.BytesIO(logo_data))
            # Guardar temporalmente para FPDF
            logo_img.save("temp_logo.png")
            pdf.image("temp_logo.png", 10, 8, 33)
        except: pass

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(80)
    pdf.cell(30, 10, st.session_state.get("nombre_negocio", "CobroYa Pro").upper(), 0, 1, 'C')
    
    pdf.set_font("Arial", '', 9)
    pdf.cell(80)
    info_empresa = f"RNC: {st.session_state.get('rnc', '---')} | Tel: {st.session_state.get('telefono_negocio', '---')}"
    pdf.cell(30, 5, info_empresa, 0, 1, 'C')
    pdf.cell(80)
    pdf.cell(30, 5, st.session_state.get("direccion_negocio", "---"), 0, 1, 'C')
    
    pdf.ln(20)
    
    # --- Título del Documento ---
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f" RECIBO DE PAGO # {datos_pago['id']}", 1, 1, 'L', fill=True)
    pdf.ln(5)
    
    # --- Datos de la Transacción ---
    pdf.set_font("Arial", '', 11)
    col_width = 45
    
    data_grid = [
        ("Cliente:", cliente_nombre),
        ("Monto Recibido:", f"${datos_pago['monto']:,.2f}"),
        ("Fecha:", datetime.now().strftime("%d/%m/%Y %H:%M")),
        ("Método de Pago:", datos_pago.get('metodo_pago', 'Efectivo')),
        ("Referencia:", datos_pago.get('referencia', 'N/A'))
    ]
    
    for label, val in data_grid:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(col_width, 8, label, 0)
        pdf.set_font("Arial", '', 11)
        pdf.cell(0, 8, str(val), 0, 1)
    
    # --- Código QR de Verificación ---
    qr_data = f"PAGO_ID:{datos_pago['id']}|CLI:{cliente_nombre}|MONTO:{datos_pago['monto']}"
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")
    
    qr_buf = io.BytesIO()
    img_qr.save(qr_buf, format='PNG')
    pdf.image(qr_buf, 150, 65, 40, 40)
    
    # --- Pie de Página / Cláusulas ---
    pdf.ln(30)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, st.session_state.get("mis_clausulas", ""))
    
    return pdf.output(dest='S').encode('latin-1')

# =========================================================
# 8. MÓDULO DE INTELIGENCIA ARTIFICIAL (RISK ENGINE)
# =========================================================

def analizar_perfil_con_ia(cliente_info, historial_pagos):
    """
    Analiza la salud financiera usando Llama-3 de Groq.
    """
    api_key = st.secrets.get("GROQ_API_KEY")
    if not api_key:
        return "⚠️ Configure su GROQ_API_KEY para habilitar el análisis de IA."

    try:
        client = Groq(api_key=api_key)
        prompt = f"""
        Como experto analista financiero de Silicon Valley, evalúa este cliente:
        Nombre: {cliente_info['nombre']}
        Balance Actual: {cliente_info.get('balance_deuda', 0)}
        Historial de pagos: {historial_pagos}
        
        Responde en formato ejecutivo:
        1. Score de Riesgo (1-100).
        2. Probabilidad de impago.
        3. Estrategia de cobro sugerida.
        """
        
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
            temperature=0.3
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error en motor de IA: {str(e)}"

# =========================================================
# 9. NAVEGACIÓN Y ESTRUCTURA (SIDEBAR PREMIUM)
# =========================================================

with st.sidebar:
    if st.session_state.get("mi_logo"):
        try:
            st.image(base64.b64decode(st.session_state["mi_logo"]), width=200)
        except:
            st.title(f"🏢 {st.session_state.get('nombre_negocio', 'CobroYa')}")
    else:
        st.title(f"🏢 {st.session_state.get('nombre_negocio', 'CobroYa')}")
    
    st.markdown("---")
    menu = st.radio(
        "MENÚ PRINCIPAL",
        ["📊 Panel de Control", "👥 Clientes", "🏦 Préstamos", "💸 Cobros y Pagos", "📉 Gastos", "🤖 IA Risk Advisor", "⚙️ Configuración"],
        index=0
    )
    st.markdown("---")
    
    # Widget de cierre de sesión
    st.caption(f"Usuario: {st.session_state.user.email}")
    if st.button("🚪 Cerrar Sesión Segura"):
        conn.client.auth.sign_out()
        st.session_state.clear()
        st.rerun()

# =========================================================
# 10. VISTA: PANEL DE CONTROL (DASHBOARD)
# =========================================================

if menu == "📊 Panel de Control":
    st.markdown("<h1 style='color: #1D1D1F;'>Dashboard Ejecutivo</h1>", unsafe_allow_html=True)
    
    if not df_prestamos.empty:
        # Cálculos de Cartera
        activos = df_prestamos[df_prestamos['estado'] == 'Activo']
        total_invertido = df_prestamos['monto_prestado'].sum()
        total_pagado = df_pagos['monto'].sum() if not df_pagos.empty else 0
        balance_cartera = total_invertido - total_pagado
        
        # Fila de Métricas
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='metric-card'><p style='color: #86868B; font-size: 0.8rem; font-weight: 700;'>CAPITAL EN CALLE</p><h2 style='color: #1D1D1F;'>${balance_cartera:,.2f}</h2></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-card'><p style='color: #86868B; font-size: 0.8rem; font-weight: 700;'>TOTAL RECAUDADO</p><h2 style='color: #34C759;'>${total_pagado:,.2f}</h2></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-card'><p style='color: #86868B; font-size: 0.8rem; font-weight: 700;'>PRÉSTAMOS ACTIVOS</p><h2 style='color: #007AFF;'>{len(activos)}</h2></div>", unsafe_allow_html=True)
        with m4:
            g_total = df_gastos['monto'].sum() if not df_gastos.empty else 0
            st.markdown(f"<div class='metric-card'><p style='color: #86868B; font-size: 0.8rem; font-weight: 700;'>GASTOS MES</p><h2 style='color: #FF3B30;'>${g_total:,.2f}</h2></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gráficos de Análisis de Datos
        c1, c2 = st.columns([1.5, 1])
        with c1:
            if not df_pagos.empty:
                df_pagos['fecha_pago'] = pd.to_datetime(df_pagos['fecha_pago'])
                fig_trend = px.line(df_pagos.sort_values('fecha_pago'), x='fecha_pago', y='monto', 
                                   title="Tendencia de Recaudación (Cash Flow)",
                                   line_shape='spline', render_mode='svg')
                fig_trend.update_traces(line_color='#007AFF', fill='tozeroy')
                st.plotly_chart(fig_trend, use_container_width=True)
        with c2:
            fig_pie = px.pie(df_prestamos, names='estado', hole=0.6, title="Salud de la Cartera",
                             color_discrete_sequence=['#34C759', '#FF9500', '#FF3B30', '#8E8E93'])
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Aún no hay datos para mostrar. Comienza registrando un préstamo.")

# =========================================================
# 11. VISTA: GESTIÓN DE CLIENTES
# =========================================================

elif menu == "👥 Clientes":
    st.markdown("<h2 style='color: #1D1D1F;'>Directorio de Clientes</h2>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["📋 Listado", "➕ Nuevo Registro"])
    
    with t1:
        if not df_clientes.empty:
            st.dataframe(df_clientes[['nombre', 'cedula', 'telefono', 'direccion', 'id']], 
                         use_container_width=True, hide_index=True)
        else:
            st.write("No hay clientes registrados.")
            
    with t2:
        with st.form("registro_cliente", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nom = col1.text_input("Nombre Completo")
            ced = col2.text_input("Cédula / ID")
            tel = col1.text_input("Teléfono / WhatsApp")
            dir_c = col2.text_input("Dirección de Residencia")
            
            if st.form_submit_button("Guardar Cliente"):
                if nom and ced:
                    conn.table("clientes").insert({
                        "nombre": nom, "cedula": ced, "telefono": tel, 
                        "direccion": dir_c, "user_id": u_id
                    }).execute()
                    st.success("Cliente guardado correctamente.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Nombre y Cédula son obligatorios.")

# =========================================================
# 12. VISTA: GESTIÓN DE PRÉSTAMOS
# =========================================================

elif menu == "🏦 Préstamos":
    st.markdown("<h2 style='color: #1D1D1F;'>Gestión de Créditos</h2>", unsafe_allow_html=True)
    tab_p1, tab_p2 = st.tabs(["🔍 Ver Préstamos", "🚀 Nuevo Préstamo"])
    
    with tab_p1:
        if not df_prestamos.empty:
            # Procesar datos para visualización
            df_p_view = df_prestamos.copy()
            df_p_view['Cliente'] = df_p_view['clientes'].apply(lambda x: x['nombre'] if isinstance(x, dict) else 'N/A')
            
            st.dataframe(
                df_p_view[['id', 'Cliente', 'monto_prestado', 'tasa_interes', 'frecuencia', 'estado']],
                column_config={
                    "monto_prestado": st.column_config.NumberColumn("Principal", format="$ %.2f"),
                    "tasa_interes": st.column_config.NumberColumn("Tasa (%)"),
                },
                use_container_width=True, hide_index=True
            )
        else:
            st.info("No hay préstamos activos.")

    with tab_p2:
        if df_clientes.empty:
            st.warning("Debes registrar al menos un cliente antes de crear un préstamo.")
        else:
            with st.form("nuevo_prestamo"):
                c1, c2 = st.columns(2)
                cli_nombre = c1.selectbox("Seleccionar Cliente", df_clientes['nombre'].unique())
                monto_p = c2.number_input("Monto a Prestar ($)", min_value=100.0, step=500.0)
                
                c3, c4, c5 = st.columns(3)
                tasa_p = c3.number_input("Tasa Anual (%)", value=20.0)
                cuotas_p = c4.number_input("Número de Cuotas", min_value=1, value=12)
                frec_p = c5.selectbox("Frecuencia", ["Mensual", "Quincenal", "Semanal"])
                
                fecha_in = st.date_input("Fecha de Inicio")
                garantia_p = st.text_input("Garantía / Aval")
                
                if st.form_submit_button("Aprobar y Desembolsar"):
                    c_id = int(df_clientes[df_clientes['nombre'] == cli_nombre]['id'].values[0])
                    
                    p_data = {
                        "cliente_id": c_id,
                        "monto_prestado": monto_p,
                        "tasa_interes": tasa_p,
                        "cuotas": cuotas_p,
                        "frecuencia": frec_p,
                        "fecha_inicio": fecha_in.isoformat(),
                        "garantia": garantia_p,
                        "estado": "Activo",
                        "user_id": u_id
                    }
                    
                    conn.table("prestamos").insert(p_data).execute()
                    st.balloons()
                    st.success(f"Préstamo registrado para {cli_nombre}")
                    st.cache_data.clear()
                    st.rerun()

# =========================================================
# 13. VISTA: CENTRO DE COBROS Y PAGOS
# =========================================================

elif menu == "💸 Cobros y Pagos":
    st.markdown("<h2 style='color: #1D1D1F;'>Gestión de Recaudación</h2>", unsafe_allow_html=True)
    
    col_sel, col_pay = st.columns([1, 1.2])
    
    with col_sel:
        st.markdown("### 🔍 Localizar Deuda")
        if not df_clientes.empty:
            c_pago = st.selectbox("Seleccionar Cliente", df_clientes['nombre'].unique())
            id_c_pago = df_clientes[df_clientes['nombre'] == c_pago]['id'].values[0]
            
            # Filtrar préstamos pendientes de este cliente
            pr_pendientes = df_prestamos[(df_prestamos['cliente_id'] == id_c_pago) & (df_prestamos['estado'] != 'Pagado')]
            
            if not pr_pendientes.empty:
                p_id_sel = st.selectbox("ID del Préstamo", pr_pendientes['id'].unique())
                p_info = pr_pendientes[pr_pendientes['id'] == p_id_sel].iloc[0]
                
                # CÁLCULO DE BALANCE EN TIEMPO REAL
                monto_original = p_info['monto_prestado']
                total_abonado = df_pagos[df_pagos['prestamo_id'] == p_id_sel]['monto'].sum() if not df_pagos.empty else 0
                balance_actual = monto_original - total_abonado
                
                st.metric("Balance Pendiente", f"${balance_actual:,.2f}", delta=f"-${total_abonado:,.2f} cobrados", delta_color="normal")
                
                with st.expander("Ver detalle de cuotas"):
                    tab_amort = calcular_tabla_amortizacion(
                        p_info['monto_prestado'], p_info['tasa_interes'], 
                        p_info['cuotas'], p_info['frecuencia']
                    )
                    st.table(tab_amort)
            else:
                st.success("🎉 Este cliente no tiene deudas pendientes.")
        else:
            st.info("No hay clientes registrados.")

    with col_pay:
        if not pr_pendientes.empty:
            st.markdown("### 💵 Registrar Abono")
            with st.container(border=True):
                monto_recibir = st.number_input("Monto a cobrar ($)", min_value=1.0, max_value=float(balance_actual), step=100.0)
                metodo_p = st.selectbox("Método", ["Efectivo", "Transferencia", "Depósito", "Tarjeta"])
                ref_p = st.text_input("Referencia / NAF")
                
                if st.button("🚀 Procesar Pago y Generar Recibo"):
                    nuevo_pago = {
                        "prestamo_id": int(p_id_sel),
                        "monto": monto_recibir,
                        "metodo_pago": metodo_p,
                        "referencia": ref_p,
                        "fecha_pago": datetime.now().isoformat(),
                        "user_id": u_id
                    }
                    
                    # 1. Insertar pago
                    res_pago = conn.table("pagos").insert(nuevo_pago).execute()
                    
                    # 2. Verificar si liquidó la deuda para cerrar préstamo
                    if (balance_actual - monto_recibir) <= 0.01:
                        conn.table("prestamos").update({"estado": "Pagado"}).eq("id", p_id_sel).execute()
                    
                    if res_pago.data:
                        st.success("✅ Pago registrado exitosamente.")
                        # Generar y descargar PDF automáticamente
                        pdf_data = generar_recibo_pdf(res_pago.data[0], c_pago)
                        st.download_button(
                            label="📥 Descargar Recibo Oficial (PDF)",
                            data=pdf_data,
                            file_name=f"Recibo_{c_pago}_{p_id_sel}.pdf",
                            mime="application/pdf"
                        )
                        st.cache_data.clear()
                        time.sleep(2)
                        st.rerun()

# =========================================================
# 14. VISTA: GESTIÓN DE GASTOS
# =========================================================

elif menu == "📉 Gastos":
    st.markdown("<h2 style='color: #1D1D1F;'>Control de Egresos</h2>", unsafe_allow_html=True)
    col_g1, col_g2 = st.columns([1, 2])
    
    with col_g1:
        with st.form("form_gastos", clear_on_submit=True):
            st.markdown("### Registrar Salida")
            g_desc = st.text_input("Concepto / Descripción")
            g_monto = st.number_input("Monto ($)", min_value=1.0)
            g_cat = st.selectbox("Categoría", ["Nómina", "Oficina", "Marketing", "Servicios", "Otros"])
            
            if st.form_submit_button("Guardar Gasto"):
                conn.table("gastos").insert({
                    "descripcion": g_desc, "monto": g_monto, 
                    "categoria": g_cat, "user_id": u_id,
                    "fecha": datetime.now().isoformat()
                }).execute()
                st.cache_data.clear()
                st.rerun()
                
    with col_g2:
        st.markdown("### Historial de Gastos")
        if not df_gastos.empty:
            st.dataframe(df_gastos[['fecha', 'descripcion', 'categoria', 'monto']], use_container_width=True)
        else:
            st.write("No hay gastos registrados este mes.")

# =========================================================
# 15. VISTA: IA RISK ADVISOR
# =========================================================

elif menu == "🤖 IA Risk Advisor":
    st.markdown("<h2 style='color: #1D1D1F;'>Análisis Predictivo</h2>", unsafe_allow_html=True)
    if not df_prestamos.empty:
        c_ia = st.selectbox("Seleccionar Cliente para Auditoría", df_clientes['nombre'].unique())
        if st.button("Ejecutar Análisis de Riesgo"):
            with st.spinner("La IA está analizando comportamientos de pago..."):
                cli_data = df_clientes[df_clientes['nombre'] == c_ia].iloc[0]
                # Obtener historial de pagos simplificado para la IA
                id_c = cli_data['id']
                pagos_cli = df_pagos[df_pagos['prestamo_id'].isin(df_prestamos[df_prestamos['cliente_id']==id_c]['id'])]
                historial_texto = pagos_cli[['fecha_pago', 'monto']].to_string() if not pagos_cli.empty else "Sin pagos realizados"
                
                resultado = analizar_perfil_con_ia(cli_data, historial_texto)
                st.markdown(f"<div style='background-color: white; padding: 25px; border-radius: 15px; border-left: 5px solid #007AFF;'>{resultado}</div>", unsafe_allow_html=True)
    else:
        st.info("Se requiere historial de préstamos para realizar análisis.")

# =========================================================
# 16. VISTA: CONFIGURACIÓN E IDENTIDAD
# =========================================================

elif menu == "⚙️ Configuración":
    st.markdown("<h2 style='color: #1D1D1F;'>Configuración Corporativa</h2>", unsafe_allow_html=True)
    
    with st.form("form_config"):
        st.markdown("### 🏢 Datos del Negocio")
        c1, c2 = st.columns(2)
        n_neg = c1.text_input("Nombre de la Empresa", value=st.session_state.get("nombre_negocio", ""))
        rnc_neg = c2.text_input("RNC / Cédula Jurídica", value=st.session_state.get("rnc", ""))
        tel_neg = c1.text_input("Teléfono de contacto", value=st.session_state.get("telefono_negocio", ""))
        dir_neg = c2.text_input("Dirección Física", value=st.session_state.get("direccion_negocio", ""))
        
        st.markdown("### 📄 Términos Legales (Contratos y Recibos)")
        claus = st.text_area("Cláusulas de pago y morosidad", value=st.session_state.get("mis_clausulas", ""), height=150)
        
        st.markdown("### 🖼️ Identidad Visual")
        upload_logo = st.file_uploader("Subir Logo (PNG recomendado)", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("💾 Guardar Cambios Globales"):
            logo_b64 = st.session_state.get("mi_logo")
            if upload_logo:
                logo_b64 = base64.b64encode(upload_logo.read()).decode()
            
            config_data = {
                "nombre_negocio": n_neg, "rnc": rnc_neg,
                "telefono_negocio": tel_neg, "direccion_negocio": dir_neg,
                "clausulas": claus, "logo_base64": logo_b64,
                "user_id": u_id
            }
            
            conn.table("configuracion").upsert(config_data).execute()
            st.session_state.clear() # Limpiar para forzar recarga de config
            st.success("Configuración actualizada. Reiniciando panel...")
            time.sleep(1.5)
            st.rerun()

    # --- CAMBIO DE CONTRASEÑA ---
    with st.expander("🔐 Seguridad de la Cuenta"):
        nueva_p = st.text_input("Nueva Contraseña", type="password")
        if st.button("Actualizar Credenciales"):
            if len(nueva_p) >= 6:
                conn.client.auth.update_user({"password": nueva_p})
                st.success("Contraseña actualizada.")
            else:
                st.error("Mínimo 6 caracteres.")

# --- PIE DE PÁGINA ---
st.markdown("<br><hr><center><p style='color: #8E8E93; font-size: 0.8rem;'>CobroYa Pro © 2026 | Financial Engineering Platform</p></center>", unsafe_allow_html=True)
