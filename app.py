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
from groq import Groq
from io import BytesIO
import qrcode # Asegúrate de tener: pip install qrcode
import base64
from fpdf import FPDF
from datetime import datetime

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
# --- CARGA INICIAL DE CONFIGURACIÓN ---
if "config_cargada" not in st.session_state:
    try:
        res_c = conn.table("configuracion").select("*").eq("user_id", u_id).execute()
        if res_c.data:
            conf = res_c.data[0]
            st.session_state["mis_clausulas"] = conf.get("clausulas", "Sujeto a términos legales.")
            # IMPORTANTE: Guardamos el logo en la sesión para el PDF
            st.session_state["mi_logo"] = conf.get("logo_base64", None)
            st.session_state["nombre_negocio"] = conf.get("nombre_negocio", "CobroYa Pro")
            st.session_state["direccion_negocio"] = conf.get("direccion_negocio", "Villa Altagracia, RD")
            st.session_state["telefono_negocio"] = conf.get("telefono_negocio", "829-000-0000")
            st.session_state["config_cargada"] = True
        else:
            # Valores por defecto si el usuario es nuevo
            st.session_state["mi_logo"] = None
            st.session_state["nombre_negocio"] = "CobroYa Pro"
    except Exception as e:
        st.error(f"Error cargando config: {e}")

# --- 3. FUNCIONES AUXILIARES (CORREGIDAS) ---

# --- FUNCIONES AUXILIARES ---
# --- COLOCA ESTO ARRIBA, CERCA DE TUS OTROS IMPORTS ---
def asistente_ia_cobroya(datos_negocio, pregunta_usuario):
    # 1. Configuración del cliente
    client = Groq(api_key=st.secrets["GROQ_API_KEY"]) 
    
    # 2. El mensaje del sistema
    system_prompt = f"""
    Eres el Asistente Senior de Riesgos de 'CobroYa Pro'. 
    Tu objetivo es ayudar al dueño del negocio a tomar decisiones financieras.
    REGLAS: Solo usa estos datos: {datos_negocio}. Habla profesional.
    """

    # 3. Llamada al modelo (Actualizado a llama-3.3-70b-versatile)
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": pregunta_usuario}
        ]
    )
    
    # 4. El retorno (Asegúrate de que esta línea esté alineada con 'completion')
    return completion.choices[0].message.content

def obtener_contexto_privado_ia(u_id_actual):
    """Filtra los datos para que la IA solo vea lo que le toca al usuario logueado"""
    try:
        # Traemos solo préstamos del usuario actual con el nombre del cliente
        res = conn.table("prestamos").select("*, clientes(nombre)").eq("user_id", u_id_actual).execute()
        datos = res.data if res.data else []
        
        if not datos:
            return "No hay préstamos registrados para analizar."

        # Construimos el 'libro de datos' exclusivo
        contexto = "DATOS PRIVADOS DE TU CARTERA (SOLO PARA TUS OJOS):\n"
        for p in datos:
            nombre = p.get('clientes', {}).get('nombre', 'Cliente sin nombre')
            contexto += f"- {nombre}: Debe RD$ {p['balance']:,.2f} | Estado: {p['estado']} | Próximo Pago: {p['proximo_pago']}\n"
        
        return contexto
    except Exception as e:
        return f"Error de seguridad al recuperar datos: {e}"

# --- FUNCIONES DE LÓGICA (Ajustadas para evitar el AttributeError) ---
def obtener_estado_cliente_real(cuentas_del_cliente):
    import datetime as dt # Importación interna para forzar que funcione
    
    if not cuentas_del_cliente:
        return "🟢 Al día", "#22c55e"
    
    hoy = dt.date.today()
    proximos_dias = hoy + dt.timedelta(days=3)
    
    atrasado = False
    pago_incompleto = False
    por_vencer = False
    
    for cuenta in cuentas_del_cliente:
        # Aseguramos que el balance sea numérico
        pendiente = float(cuenta.get('balance_pendiente') or 0)
        fecha_v_str = cuenta.get('proximo_pago')
        
        if pendiente > 0:
            if fecha_v_str:
                # Convertimos el texto de la base de datos a fecha real
                try:
                    fecha_v = dt.datetime.strptime(str(fecha_v_str), '%Y-%m-%d').date()
                    if fecha_v < hoy:
                        atrasado = True
                    elif hoy <= fecha_v <= proximos_dias:
                        por_vencer = True
                    else:
                        pago_incompleto = True
                except:
                    pago_incompleto = True # Si la fecha está mal, asumimos pendiente
            else:
                pago_incompleto = True
                
    if atrasado: return "🔴 Atrasado", "#ef4444"
    if por_vencer: return "🟡 Por Vencer", "#eab308"
    if pago_incompleto: return "🟠 Pago Incompleto", "#f97316"
    
    return "🟢 Al día", "#22c55e"

def calcular_resumen_real(cuentas_del_cliente):
    # Suma simple del balance pendiente
    return sum(float(c.get('balance_pendiente') or 0) for c in cuentas_del_cliente)

def calcular_resumen_real(cuentas_del_cliente):
    """
    Suma el balance pendiente de todas las cuentas del cliente.
    """
    total_deuda = sum(float(c.get('balance_pendiente', 0)) for c in cuentas_del_cliente)
    return total_deuda
    
def generar_pdf_recibo_pro(nombre_cliente, monto, balance, u_id, metodo="Efectivo"):
    from fpdf import FPDF
    from datetime import datetime
    
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Recuperar datos de texto de la sesión
    nombre_negocio = st.session_state.get("nombre_negocio", "CobroYa Pro")
    rnc = st.session_state.get("rnc", "N/A")
    direccion = st.session_state.get("direccion_negocio", "República Dominicana")
    telefono = st.session_state.get("telefono_negocio", "")

    # --- ENCABEZADO FORMAL ---
    pdf.set_fill_color(240, 240, 240) # Gris claro profesional
    pdf.rect(0, 0, 210, 45, 'F')
    
    pdf.set_text_color(0, 51, 102) # Azul marino
    pdf.set_xy(15, 12)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(150, 10, nombre_negocio.upper(), ln=True)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_x(15)
    pdf.cell(150, 5, f"RNC/Cédula: {rnc}", ln=True)
    pdf.set_x(15)
    pdf.cell(150, 5, f"Dirección: {direccion}", ln=True)
    pdf.set_x(15)
    pdf.cell(150, 5, f"Teléfono: {telefono}", ln=True)

    # --- CUERPO DEL RECIBO ---
    pdf.ln(25)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 14)
    recibo_id = f"REC-{datetime.now().strftime('%y%m%d%H%M')}"
    pdf.cell(100, 10, f"COMPROBANTE DE PAGO: {recibo_id}")
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(90, 10, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='R')
    
    pdf.line(15, 60, 195, 60)
    pdf.ln(10)

    # Detalle de la Transacción
    detalles = [
        ("EMISOR", nombre_negocio),
        ("CLIENTE (DEUDOR)", nombre_cliente),
        ("CONCEPTO", "Abono a préstamo / Cuota de pago"),
        ("MONTO RECIBIDO", f"RD$ {monto:,.2f}"),
        ("MÉTODO DE PAGO", metodo),
        ("BALANCE PENDIENTE", f"RD$ {balance:,.2f}")
    ]
    
    for concepto, valor in detalles:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(60, 12, f" {concepto}", border=1, fill=True)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(120, 12, f" {valor}", border=1, ln=True)

    # --- ESPACIO PARA FIRMAS (Crucial para legalidad) ---
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 10)
    
    # Firma del Cliente
    pdf.line(20, pdf.get_y(), 80, pdf.get_y())
    pdf.set_xy(20, pdf.get_y() + 2)
    pdf.cell(60, 5, "FIRMA DEL CLIENTE", align='C')
    
    # Firma del Emisor
    pdf.set_xy(120, pdf.get_y() - 2)
    pdf.line(120, pdf.get_y(), 180, pdf.get_y())
    pdf.set_xy(120, pdf.get_y() + 2)
    pdf.cell(60, 5, "RECIBIDO POR (EMISOR)", align='C')

    return bytes(pdf.output())

# =========================================================
# 🧾 RECIBO DE PAGO (SIMPLE Y LIMPIO)
# =========================================================
def generar_recibo_pago_pro(nombre, monto, balance, metodo="Efectivo"):
    pdf = FPDF()
    pdf.add_page()

    fecha = datetime.now().strftime('%d/%m/%Y')
    recibo_id = f"REC-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(190, 10, "RECIBO DE PAGO", ln=True, align="C")

    pdf.ln(5)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(100, 6, f"No: {recibo_id}")
    pdf.cell(90, 6, f"Fecha: {fecha}", ln=True, align="R")

    pdf.ln(8)

    pdf.cell(190, 6, f"Recibimos de: {nombre}", ln=True)
    pdf.cell(190, 6, f"Monto: RD$ {monto:,.2f}", ln=True)
    pdf.cell(190, 6, f"Método de pago: {metodo}", ln=True)
    pdf.cell(190, 6, f"Balance restante: RD$ {balance:,.2f}", ln=True)

    pdf.ln(20)

    pdf.line(60, pdf.get_y(), 150, pdf.get_y())
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(190, 6, "Firma autorizada", align="C")

    return bytes(pdf.output())
    
def generar_pdf_contrato_legal(nombre_cli, cedula_cli, capital, total, cuotas_df, freq, clausulas_texto):
    pdf = FPDF()
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 10, "CONTRATO DE PRESTAMO Y COMPROMISO DE PAGO", ln=True, align='C')
    pdf.line(10, 22, 200, 22)
    pdf.ln(10)
    
    # Declaración
    pdf.set_font("Helvetica", "", 11)
    nombre_clean = nombre_cli.encode('latin-1', 'replace').decode('latin-1')
    texto_declaracion = (f"Yo, {nombre_clean.upper()}, portador de la cedula {cedula_cli}, declaro haber recibido "
                         f"la suma de RD$ {capital:,.2f} en calidad de prestamo, comprometiendome a pagar "
                         f"un total de RD$ {total:,.2f} bajo los terminos acordados.")
    pdf.multi_cell(190, 7, texto_declaracion)
    pdf.ln(5)
    
    # Cláusulas
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(190, 10, "CLAUSULAS DEL COMPROMISO:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 6, clausulas_texto.encode('latin-1', 'replace').decode('latin-1'))
    pdf.ln(10)
    
    # Tabla
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(30, 8, "Cuota", border=1, align='C', fill=True)
    pdf.cell(80, 8, "Fecha Vencimiento", border=1, align='C', fill=True)
    pdf.cell(80, 8, "Monto Cuota", border=1, align='C', fill=True, ln=True)
    
    pdf.set_text_color(0, 0, 0)
    for i, row in cuotas_df.iterrows():
        if pdf.get_y() > 250:
            pdf.add_page()
        pdf.cell(30, 7, str(int(row['Nº'])), border=1, align='C')
        pdf.cell(80, 7, str(row['Fecha']), border=1, align='C')
        pdf.cell(80, 7, f"RD$ {row['Monto Cuota (RD$)']:,.2f}", border=1, align='C', ln=True)
    
    # Firmas
    pdf.set_y(-40)
    pdf.line(20, pdf.get_y(), 90, pdf.get_y()) 
    pdf.line(120, pdf.get_y(), 190, pdf.get_y()) 
    pdf.set_font("Helvetica", "B", 10)
    pdf.text(35, pdf.get_y() + 5, "FIRMA DEUDOR")
    pdf.text(135, pdf.get_y() + 5, "FIRMA ACREEDOR")
    
    return bytes(pdf.output())
def generar_estado_cuenta(nombre, total_prestado, pagado, pendiente, historial_pagos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(190, 15, "ESTADO DE CUENTA CONSOLIDADO", ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_fill_color(230, 240, 255)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(63, 20, f"PRESTADO: RD$ {total_prestado:,.0f}", border=1, align='C', fill=True)
    pdf.cell(63, 20, f"PAGADO: RD$ {pagado:,.0f}", border=1, align='C', fill=True)
    pdf.cell(64, 20, f"RESTANTE: RD$ {pendiente:,.0f}", border=1, align='C', fill=True, ln=True)
    
    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(190, 8, "HISTORIAL DE ABONOS RECIBIDOS:", ln=True)
    pdf.set_font("Helvetica", "", 10)
    
    pdf.cell(60, 8, "Fecha de Pago", border=1)
    pdf.cell(130, 8, "Monto Abonado", border=1, ln=True)
    
    for pago in historial_pagos:
        pdf.cell(60, 7, str(pago['fecha_pago']), border=1)
        pdf.cell(130, 7, f"RD$ {pago['monto_pagado']:,.2f}", border=1, ln=True)
        
    return bytes(pdf.output())

# --- 4. NAVEGACIÓN ---
# --- 1. CARGA DE DATOS DESDE SUPABASE (Nombres Reales) ---
if "user" in st.session_state and st.session_state.user:
    if "datos_validados" not in st.session_state:
        try:
            # Según tu imagen, la columna es 'user_id'
            res = conn.table("configuracion").select("*").eq("user_id", st.session_state.user.id).execute()
            
            if res.data:
                conf = res.data[0]
                # Ajustamos los nombres exactos de tu Table Editor
                st.session_state["nombre_negocio"] = conf.get("nombre_negocio", "Mi Negocio")
                st.session_state["rnc"] = conf.get("rnc", "---")
                st.session_state["telefono_negocio"] = conf.get("telefono", "---")
                st.session_state["direccion_negocio"] = conf.get("direccion", "---")
                st.session_state["mi_logo"] = conf.get("logo_base64") # Asegúrate que esta columna exista o ignórala
                
                st.session_state["datos_validados"] = True
                st.rerun()
        except Exception as e:
            st.error(f"Error técnico: {e}")
            
# --- 2. SIDEBAR ULTRA-PROFESIONAL (UNIFICADO) ---
with st.sidebar:
    # Recuperamos los datos que acabamos de cargar de Supabase
    # Si no hay nada, ponemos "---" por seguridad
    biz_name = st.session_state.get("nombre_negocio", "SIN NOMBRE").upper()
    biz_rnc  = st.session_state.get("rnc", "---")
    biz_dir  = st.session_state.get("direccion_negocio", "---")
    biz_tel  = st.session_state.get("telefono_negocio", "---")
    logo_b64 = st.session_state.get("mi_logo")

    # --- IDENTIDAD VISUAL ---
    if logo_b64:
        if "," in str(logo_b64): logo_b64 = logo_b64.split(",")[1]
        st.markdown(f"""
            <div style='display: flex; justify-content: center; padding-top: 10px;'>
                <img src='data:image/png;base64,{logo_b64}' 
                     style='width: 65px; height: 65px; object-fit: cover; border-radius: 8px;'>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style='text-align: center; margin-top: 8px; font-family: "Inter", sans-serif;'>
            <h3 style='margin: 0; color: #1e293b; font-size: 0.95rem; font-weight: 700;'>{biz_name}</h3>
            <div style='margin-top: 4px; line-height: 1.2;'>
                <p style='margin: 0; font-size: 0.7rem; color: #64748b;'>RNC: {biz_rnc}</p>
                <p style='margin: 0; font-size: 0.7rem; color: #64748b;'>📍 {biz_dir}</p>
                <p style='margin: 0; font-size: 0.7rem; color: #64748b;'>📞 {biz_tel}</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='margin: 15px 0;'></div>", unsafe_allow_html=True)

    # Sesión del Operador
    u_email = st.session_state.user.email if st.session_state.get("user") else "Sesión Activa"
    st.markdown(f"""
        <div style='padding: 8px 12px; background-color: #f1f5f9; border-radius: 6px; border-left: 2px solid #0284c7;'>
            <p style='font-size: 0.6rem; color: #94a3b8; margin: 0; text-transform: uppercase; font-weight: 600;'>Sesión iniciada como</p>
            <p style='font-size: 0.75rem; font-weight: 500; color: #334155; margin: 0;'>{u_email}</p>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Menú
    menu = st.radio("NAVEGACIÓN", ["Panel de Control", "Gestión de Cobros", "👥 Todos mis Clientes", "Nueva Cuenta por Cobrar", "Cuentas por Pagar", "IA Predictiva", "Configuración"], label_visibility="collapsed")

    if st.button("🚪 Salir del Sistema", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    # Footer Branding
    st.markdown("""
        <style>
            [data-testid="stSidebarContent"] { display: flex; flex-direction: column; }
            .sidebar-footer { margin-top: auto; text-align: center; padding: 20px 0; border-top: 1px solid #f1f5f9; }
        </style>
        <div class='sidebar-footer'>
            <p style='font-size: 0.65rem; color: #94a3b8; margin: 0;'>POWERED BY LIXANDER GARCIA</p>
            <p style='font-size: 0.85rem; font-weight: 800; color: #0284c7; margin: 0;'>CobroYa</p>
        </div>
    """, unsafe_allow_html=True)
    
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
                            # 1. Registrar el dinero
                            conn.table("pagos").insert({"cuenta_id": item['id'], "monto_pagado": abono, "user_id": u_id}).execute()
                            
                            # 2. Bajar la deuda
                            n_bal = float(item['balance_pendiente']) - abono
                            conn.table("cuentas").update({
                                "balance_pendiente": n_bal, 
                                "estado": "Pagado" if n_bal <= 0 else "Activo",
                                "proximo_pago": str(f_prox)
                            }).eq("id", item['id']).execute()
                            
                            st.success(f"Cobro de RD$ {abono} guardado")

                            # --- ESTA ES LA PARTE NUEVA PARA EL PDF ---
                            # Generamos el PDF usando el u_id para que jale tu logo
                            pdf_bin = generar_pdf_recibo_pro(
                                item['clientes']['nombre'], 
                                abono, 
                                n_bal, 
                                u_id, # <--- Aquí le pasamos tu ID de usuario
                                metodo="Efectivo"
                            )
                            
                            st.download_button(
                                label="📥 Descargar Recibo PDF",
                                data=pdf_bin,
                                file_name=f"Recibo_{item['clientes']['nombre']}.pdf",
                                mime="application/pdf",
                                key=f"dl_{item['id']}"
                            )
                            # Quitamos el st.rerun() de aquí arriba para que el usuario pueda darle al botón de descargar antes de que la página se refresque.

elif menu == "Nueva Cuenta por Cobrar":
    st.header("Crear cuenta por Cobrar")
    
    # 0. CARGA DE DATOS Y ESCUDO ANTI-DUPLICADOS
    res_cli = conn.table("clientes").select("id, nombre, cedula").eq("user_id", u_id).execute()
    res_activas = conn.table("cuentas").select("cliente_id").eq("user_id", u_id).eq("estado", "Atrasado").execute()
    ids_con_deuda = [d['cliente_id'] for d in res_activas.data] if res_activas.data else []

    if res_cli.data:
        # 1. PARAMETRIZACIÓN
        col1, col2, col3 = st.columns(3)
        with col1:
            cliente_obj = st.selectbox("Cliente", options=res_cli.data, format_func=lambda x: x['nombre'])
            capital = st.number_input("Capital a Entregar (RD$)", min_value=0.0, step=100.0)
            
            # --- ALERTA VISUAL DE SEGURIDAD ---
            if cliente_obj['id'] in ids_con_deuda:
                st.warning("⚠️ ESTE CLIENTE YA TIENE UNA DEUDA ACTIVA O ATRASADA.")
                continuar = st.checkbox("Entiendo el riesgo y deseo abrir otra deuda")
            else:
                st.success("✅ Cliente libre de deudas actuales.")
                continuar = True
        
        with col2:
            porcentaje = st.number_input("Interés Total (%)", min_value=0, value=20)
            frecuencias = {"Semanal": {"days": 7}, "Quincenal": {"days": 14}, "Mensual": {"months": 1}}
            freq_sel = st.selectbox("Frecuencia de Pagos", list(frecuencias.keys()), index=2)
        
        with col3:
            cuotas_n = st.number_input("Número de Cuotas", min_value=1, value=4)
            fecha_inicio = st.date_input("Fecha de Primera Cuota", value=datetime.now().date())

        # 2. PANEL DE RENTABILIDAD EN TIEMPO REAL
        total_esperado = capital * (1 + (porcentaje / 100))
        ganancia_neta = total_esperado - capital
        monto_sugerido = total_esperado / cuotas_n

        st.markdown("### 📊 Proyección de Negocio")
        met1, met2, met3 = st.columns(3)
        with met1:
            st.metric("💰 Capital Prestado", f"RD$ {capital:,.2f}")
        with met2:
            st.metric("💵 Ganancia Neta", f"RD$ {ganancia_neta:,.2f}", delta=f"{porcentaje}%", delta_color="normal")
        with met3:
            st.metric("📈 Retorno Total", f"RD$ {total_esperado:,.2f}")

        st.markdown("---")
        # Generar Plan de Amortización
        df_plan = pd.DataFrame([{
            "Nº": i + 1,
            "Fecha": (fecha_inicio + pd.DateOffset(days=i*7 if freq_sel=="Semanal" else i*14 if freq_sel=="Quincenal" else i*30)).date(),
            "Monto Cuota (RD$)": round(monto_sugerido, 2)
        } for i in range(cuotas_n)])

        df_editable = st.data_editor(df_plan, use_container_width=True, key="amortizacion_pro")
        total_real = df_editable["Monto Cuota (RD$)"].sum()

        # 3. EL BOTÓN DE GUARDAR CON LÓGICA DE WHATSAPP
        if st.button("🚀 Confirmar y Activar Préstamo", use_container_width=True, disabled=not continuar):
            if capital > 0:
                with st.spinner("Registrando operación..."):
                    # Insertar en DB
                    new_acc = conn.table("cuentas").insert({
                        "cliente_id": cliente_obj['id'],
                        "monto_inicial": total_real,
                        "balance_pendiente": total_real,
                        "user_id": u_id,
                        "estado": "Al Día",
                        "proximo_pago": str(df_editable.iloc[0]["Fecha"])
                    }).execute()
                    
                    # Generar PDF
                    pdf_bin = generar_pdf_contrato_legal(
                        cliente_obj['nombre'], 
                        cliente_obj.get('cedula', '000-0000000-0'), 
                        float(capital), 
                        float(total_real), 
                        df_editable, 
                        freq_sel,
                        st.session_state.get("mis_clausulas", "Sujeto a términos legales.")
                    )
                    
                    st.session_state.pdf_ready = pdf_bin
                    st.session_state.last_client_name = cliente_obj['nombre']
                    
                    # Preparar mensaje de WhatsApp automático
                    mensaje_wa = f"Hola *{cliente_obj['nombre']}*, tu préstamo ha sido activado. ✅\n\n" \
                                 f"🔹 *Capital:* RD$ {capital:,.2f}\n" \
                                 f"🔹 *Total a pagar:* RD$ {total_real:,.2f}\n" \
                                 f"🔹 *Cuotas:* {cuotas_n} de RD$ {monto_sugerido:,.2f}\n" \
                                 f"📅 *Tu primer pago es el:* {df_editable.iloc[0]['Fecha']}\n\n" \
                                 f"Se adjunta tu contrato legal en PDF."
                    
                    st.session_state.wa_link = f"https://wa.me/{cliente_obj.get('telefono', '')}?text={requests.utils.quote(mensaje_wa)}"
                    
                    st.success(f"¡Préstamo activado para {cliente_obj['nombre']}!")
                    st.rerun()

        # 4. BOTONES POST-ACTIVACIÓN
        if "pdf_ready" in st.session_state:
            st.divider()
            st.subheader("✅ Acciones del Préstamo Activo")
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.download_button("📥 Descargar Contrato PDF", data=st.session_state.pdf_ready, file_name="contrato.pdf", use_container_width=True)
            
            with c2:
                # Botón de WhatsApp estilizado
                st.markdown(f'''<a href="{st.session_state.wa_link}" target="_blank">
                    <button style="width:100%; background:#25D366; color:white; border:none; padding:10px; border-radius:10px; cursor:pointer; font-weight:bold;">
                        💬 Enviar Detalles WhatsApp
                    </button></a>''', unsafe_allow_html=True)
            
            with c3:
                if st.button("🧹 Limpiar Pantalla", use_container_width=True):
                    del st.session_state.pdf_ready
                    if "wa_link" in st.session_state: del st.session_state.wa_link
                    st.rerun()
# --- AQUÍ TERMINA LA SECCIÓN ANTERIOR Y EMPIEZA EL DIRECTORIO ---
# --- SECCIÓN A: REGISTRO PREMIUM ---
# --- SECCIÓN A: REGISTRO PREMIUM ---
elif menu == "👥 Todos mis Clientes":
        import datetime as dt
        import time
        import pandas as pd
        import folium
        from streamlit_folium import st_folium
        from streamlit_js_eval import streamlit_js_eval

        hoy_dt = dt.date.today()

        # 1. MEMORIA DE SESIÓN
        for k in ["reg_gps", "reg_nombre", "reg_tel", "reg_ced", "reg_dir"]:
            if k not in st.session_state: st.session_state[k] = ""

        st.markdown("<h1 style='color: #1e293b; font-size: 1.6rem;'>Gestión de Cartera</h1>", unsafe_allow_html=True)

        # 2. REGISTRO DESPLEGABLE
        with st.expander("✨ Registrar Nuevo Cliente", expanded=False):
            
            st.markdown("### 🛰️ Localización Satelital")
            
            # NOTA CON SIGNO DE PREGUNTA (HELP)
            st.caption("⚠️ **Nota sobre precisión:** El GPS puede tener un margen de error de 5 a 50 metros.", 
                       help="Consejo para mayor precisión: Cuando estés en el terreno, asegúrate de que el celular tenga el Wi-Fi encendido (aunque no estés conectado a una red), ya que Google utiliza las redes cercanas para triangular mejor la posición que el puro satélite.")
            
            with st.container(border=True):
                col_gps, col_map = st.columns([1, 1.5])
                
                with col_gps:
                    # Motor de captura con máxima precisión
                    pos = streamlit_js_eval(
                        js_expressions="""
                        new Promise((resolve) => {
                            if (!navigator.geolocation) { resolve("NO_SOPORTADO"); }
                            navigator.geolocation.getCurrentPosition(
                                (p) => resolve(p.coords.latitude + "," + p.coords.longitude),
                                (e) => resolve("ERROR_" + e.code),
                                { 
                                    enableHighAccuracy: true, 
                                    timeout: 15000, 
                                    maximumAge: 0 
                                }
                            )
                        })
                        """,
                        key="GPS_ENGINE_V6_FINAL"
                    )

                    if st.button("🎯 CAPTURAR UBICACIÓN AHORA", use_container_width=True, type="primary"):
                        if pos and not pos.startswith("ERROR") and pos != "NO_SOPORTADO":
                            st.session_state.reg_gps = pos
                            st.success("✅ Ubicación capturada")
                            st.rerun()
                        elif pos and pos.startswith("ERROR"):
                            st.error("🚫 Error de señal. Revisa tus permisos de GPS.")
                    
                    st.session_state.reg_gps = st.text_input("📍 Coordenadas (Ajuste manual)", 
                                                            value=st.session_state.reg_gps,
                                                            placeholder="Lat, Lon")

                with col_map:
                    if st.session_state.reg_gps and "," in st.session_state.reg_gps:
                        try:
                            lat, lon = map(float, st.session_state.reg_gps.split(","))
                            m = folium.Map(location=[lat, lon], zoom_start=19)
                            folium.Marker([lat, lon], icon=folium.Icon(color='red', icon='home')).add_to(m)
                            st_folium(m, height=250, use_container_width=True, key=f"map_p_{lat}_{lon}")
                        except:
                            st.error("Formato inválido.")
                    else:
                        st.info("Captura ubicación para ver el mapa.")

            st.markdown("### 📝 Datos del Cliente")
            c1, c2 = st.columns(2)
            with c1:
                st.session_state.reg_nombre = st.text_input("Nombre Completo *", value=st.session_state.reg_nombre, key="f_n")
                st.session_state.reg_ced = st.text_input("Cédula / ID *", value=st.session_state.reg_ced, key="f_c")
            with c2:
                st.session_state.reg_tel = st.text_input("WhatsApp / Celular *", value=st.session_state.reg_tel, key="f_t")
                st.session_state.reg_dir = st.text_area("Referencia (Color de casa, etc.)", value=st.session_state.reg_dir, height=68, key="f_d")

            # --- BOTONES DE ACCIÓN (LIMPIAR Y GUARDAR) ---
            col_b1, col_b2 = st.columns(2)
            
            with col_b1:
                if st.button("🧹 LIMPIAR CAMPOS", use_container_width=True):
                    for k in ["reg_gps", "reg_nombre", "reg_tel", "reg_ced", "reg_dir"]:
                        st.session_state[k] = ""
                    st.rerun()

            with col_b2:
                btn_guardar = st.button("🚀 GUARDAR EN CARTERA", use_container_width=True, type="primary")

            if btn_guardar:
                # 1. BLOQUEO TOTAL: Solo Nombre y Cédula
                if not st.session_state.reg_nombre or not st.session_state.reg_ced:
                    st.error("❌ El **Nombre** y la **Cédula** son obligatorios.")
                
                else:
                    # 2. MANEJO DE GPS OPCIONAL
                    lat_final, lon_final = 0.0, 0.0
                    if not st.session_state.reg_gps:
                        st.warning("⚠️ **Aviso:** Guardando cliente sin ubicación exacta.")
                    else:
                        try:
                            lat_v, lon_v = st.session_state.reg_gps.split(",")
                            lat_final, lon_final = float(lat_v), float(lon_v)
                        except:
                            pass

                    # 3. EJECUCIÓN DEL GUARDADO
                    try:
                        conn.table("clientes").insert({
                            "nombre": st.session_state.reg_nombre,
                            "telefono": st.session_state.reg_tel,
                            "cedula": st.session_state.reg_ced,
                            "direccion": st.session_state.reg_dir,
                            "latitud": lat_final,
                            "longitud": lon_final,
                            "user_id": u_id,
                            "fecha_registro": str(hoy_dt)
                        }).execute()
                        
                        st.success(f"✅ ¡Cliente {st.session_state.reg_nombre} registrado!")
                        for k in ["reg_gps", "reg_nombre", "reg_tel", "reg_ced", "reg_dir"]: 
                            st.session_state[k] = ""
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.divider()
    
        # --- 4. CENTRO DE CONTROL DE CLIENTES (Lógica Avanzada y Diseño Premium) ---
    
        # 1. CARGA DE DATOS Y ESTADOS (Usando tus columnas reales del CSV)
        res_cl = conn.table("clientes").select("*").eq("user_id", u_id).order("nombre").execute()
        clientes_db = res_cl.data if res_cl.data else []
        res_cuentas = conn.table("cuentas").select("*").execute()
        cuentas_db = res_cuentas.data if res_cuentas.data else []
        res_pagos = conn.table("pagos").select("*").execute()
        pagos_db = res_pagos.data if res_pagos.data else []

        hoy = datetime.now().date()

        # --- BARRA DE COMANDO: BUSCADOR + PILLS ---
        col_search, col_filter = st.columns([1.2, 2])
        with col_search:
            search_query = st.text_input("🔍", placeholder="Buscar cliente...", label_visibility="collapsed")
        
        with col_filter:
            opciones = ["🌍 Todos", "🔴 Atrasados", "🟢 Al Día", "🟡 Próximos/Hoy"]
            sel_filtro = st.pills("Filtro Inteligente:", opciones, selection_mode="single", default="🌍 Todos", label_visibility="collapsed")

        # --- LÓGICA DE FILTRADO "GENIO" ---
        clientes_f = []
        for c in clientes_db:
            # Buscamos la cuenta principal (o la más reciente)
            cuenta = next((d for d in cuentas_db if d['cliente_id'] == c['id']), None)
            
            # Si no hay cuenta, solo aparece en "Todos"
            match_estado = False
            if sel_filtro == "🌍 Todos":
                match_estado = True
            elif cuenta:
                prox_pago = pd.to_datetime(cuenta.get('proximo_pago')).date() if cuenta.get('proximo_pago') else None
                balance = cuenta.get('balance_pendiente', 0)
                
                # Atrasado: Si hoy es después de la fecha y tiene deuda
                if sel_filtro == "🔴 Atrasados":
                    if prox_pago and hoy > prox_pago and balance > 0:
                        match_estado = True
                
                # Al Día: Balance 0 O la fecha es futura y no hay retrasos previos
                elif sel_filtro == "🟢 Al Día":
                    if balance <= 0 or (prox_pago and prox_pago > hoy):
                        # Nota: Si estaba atrasado no entra aquí
                        if not (prox_pago and hoy > prox_pago and balance > 0):
                            match_estado = True
                
                # Próximos/Hoy: Falta 1 día o es hoy mismo
                elif sel_filtro == "🟡 Próximos/Hoy":
                    if prox_pago:
                        dias_dif = (prox_pago - hoy).days
                        if dias_dif == 0 or dias_dif == 1:
                            match_estado = True

            # Match de búsqueda por texto
            match_search = not search_query or (search_query.lower() in c['nombre'].lower() or search_query in str(c.get('cedula', '')))
            
            if match_search and match_estado:
                clientes_f.append(c)

        # --- VENTANA DE HISTORIAL (MODAL) ---
        @st.dialog("📄 Expediente de Facturación")
        def modal_detalle(cliente, cuentas, pagos):
            st.markdown(f"### {cliente['nombre']}")
            st.caption(f"📍 GPS: {cliente.get('latitud', '0')}, {cliente.get('longitud', '0')}")
            st.divider()
            
            mis_ctas = [ct for ct in cuentas if ct['cliente_id'] == cliente['id']]
            if not mis_ctas:
                st.info("Sin cuentas activas.")
            else:
                for ct in mis_ctas:
                    with st.container(border=True):
                        c1, c2 = st.columns([2,1])
                        c1.markdown(f"**Factura ID: {str(ct['id'])[:8]}**")
                        c1.write(f"📅 Próximo cobro: `{ct.get('proximo_pago')}`")
                        c2.metric("Pendiente", f"${ct.get('balance_pendiente', 0):,}")
                        
                        # LÓGICA DE ABONOS ESPECÍFICOS
                        st.markdown("**💰 Desglose de Abonos:**")
                        mis_p = [p for p in pagos if p.get('cuenta_id') == ct['id']]
                        if mis_p:
                            for p in mis_p:
                                st.markdown(f"""
                                <div style='display:flex; justify-content:space-between; background:#f0f2f6; padding:5px 10px; border-radius:8px; margin-bottom:5px;'>
                                    <span>✅ ${p.get('monto_pagado', 0):,}</span>
                                    <span style='color:gray; font-size:12px;'>{str(p.get('fecha_pago'))[:10]}</span>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.caption("No se han registrado abonos a esta factura.")

        # --- GRID DE CLIENTES ---
        if not clientes_f:
            st.warning("No hay clientes en esta categoría.")
        else:
            grid = st.columns(3)
            for idx, cl in enumerate(clientes_f):
                with grid[idx % 3]:
                    with st.container(border=True):
                        # Cabecera Estética
                        st.markdown(f"**{cl['nombre']}**")
                        st.caption(f"🆔 {cl.get('cedula', 'N/A')}")
                        
                        # BOTONES CON LOGOS REALES (Diseño Apple/Premium)
                        b1, b2, b3 = st.columns(3)
                        with b1: # HISTORIAL
                            if st.button("📂", key=f"h_{cl['id']}", use_container_width=True, help="Ver historial y facturas"):
                                modal_detalle(cl, cuentas_db, pagos_db)
                        
                        with b2: # WHATSAPP LOGO EXACTO
                            tel = "".join(filter(str.isdigit, str(cl.get('telefono', ''))))
                            wa_url = f"https://wa.me/{tel}"
                            st.markdown(f'''<a href="{wa_url}" target="_blank">
                                <button style="width:100%; background:#25D366; border:none; padding:8px; border-radius:10px; cursor:pointer; display:flex; justify-content:center;">
                                    <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="20">
                                </button></a>''', unsafe_allow_html=True)
                        
                        with b3: # GOOGLE MAPS LOGO EXACTO
                            lat, lon = cl.get('latitud'), cl.get('longitud')
                            if lat and str(lat) not in ["0", "0.0", "None"]:
                                map_url = f"https://www.google.com/maps?q={lat},{lon}"
                                st.markdown(f'''<a href="{map_url}" target="_blank">
                                    <button style="width:100%; background:white; border:1px solid #ddd; padding:8px; border-radius:10px; cursor:pointer; display:flex; justify-content:center;">
                                        <img src="https://upload.wikimedia.org/wikipedia/commons/a/aa/Google_Maps_icon_%282020%29.svg" width="20">
                                    </button></a>''', unsafe_allow_html=True)
                            else:
                                st.button(
                                    "📵", 
                                    disabled=True, 
                                    key=f"no_gps_{cl['id']}", 
                                    help="No se han guardado las coordenadas GPS de este cliente",
                                    use_container_width=True
                                )

                        # ELIMINAR CON DOBLE ADVERTENCIA
                        with st.popover("⚙️", use_container_width=True):
                            st.write("### 🛠️ Gestión")
                            if st.button("🗑️ Eliminar Cliente", key=f"del_step1_{cl['id']}", type="primary", use_container_width=True):
                                st.session_state[f"confirm_del_{cl['id']}"] = True

                            if st.session_state.get(f"confirm_del_{cl['id']}"):
                                st.error("⚠️ **¿ESTÁS SEGURO?**")
                                st.warning("Se borrarán PERMANENTEMENTE todos los datos: deudas, facturas, abonos y ubicación de este cliente.")
                                
                                c1, c2 = st.columns(2)
                                with c1:
                                    if st.button("SÍ, BORRAR TODO", key=f"del_final_{cl['id']}", type="primary", use_container_width=True):
                                        conn.table("clientes").delete().eq("id", cl['id']).execute()
                                        del st.session_state[f"confirm_del_{cl['id']}"]
                                        st.rerun()
                                with c2:
                                    if st.button("CANCELAR", key=f"cancel_{cl['id']}", use_container_width=True):
                                        del st.session_state[f"confirm_del_{cl['id']}"]
                                        st.rerun()
        
# --- SECCIÓN DE CUENTAS POR PAGAR (FUERA DEL BLOQUE ANTERIOR) ---
elif menu == "Cuentas por Pagar":
    st.header("Movimientos de Efectivo")
    
    # 1. Recuperar datos de Supabase
    res_p = conn.table("pagos").select("monto_pagado").eq("user_id", u_id).execute()
    res_g = conn.table("gastos").select("monto").eq("user_id", u_id).execute()
    
    # 2. Calcular balance neto
    total_pagos = sum([p['monto_pagado'] for p in res_p.data]) if res_p.data else 0
    total_gastos = sum([g['monto'] for g in res_g.data]) if res_g.data else 0
    neto = total_pagos - total_gastos
    
    # 3. Mostrar métrica
    st.metric("Balance Neto en Mano", f"RD$ {neto:,.2f}")
    
    # 4. Formulario de Gastos
    with st.expander("Registrar Nuevo Gasto"):
        with st.form("gasto_real"):
            motivo = st.text_input("¿En qué se gastó?")
            m_gasto = st.number_input("Monto RD$", min_value=0.0, step=100.0)
            
            if st.form_submit_button("Guardar Gasto"):
                if motivo and m_gasto > 0:
                    conn.table("gastos").insert({
                        "descripcion": motivo, 
                        "monto": m_gasto, 
                        "user_id": u_id
                    }).execute()
                    st.success("Gasto registrado correctamente")
                    st.rerun()
                else:
                    st.error("Por favor rellena todos los campos")

elif menu == "IA Predictiva":
    # ---------------------------------------------------------
    # 1. CSS AVANZADO PARA ESTILO META AI (Tarjetas Flotantes)
    # ---------------------------------------------------------
    st.markdown("""
        <style>
            /* Contenedor principal centrado */
            .main .block-container { max-width: 850px; padding-top: 3rem; }
            [data-testid="stHeader"] { display: none; }
            
            /* Título estilo Meta */
            .titulo-meta {
                text-align: center;
                font-size: 42px;
                font-weight: 700;
                margin-bottom: 10px;
                color: #1c1e21;
            }
            .subtitulo-meta {
                text-align: center;
                color: #65676b;
                font-size: 18px;
                margin-bottom: 40px;
            }

            /* Estilo de las Sugerencias Flotantes */
            .sugerencia-card {
                background: white;
                border: 1px solid #e4e6eb;
                border-radius: 12px;
                padding: 15px;
                margin-bottom: 12px;
                transition: all 0.3s ease;
                cursor: pointer;
                display: flex;
                align-items: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .sugerencia-card:hover {
                background-color: #f0f2f5;
                border-color: #0084ff;
                transform: translateY(-2px);
            }
        </style>
        <h1 class="titulo-meta">¿En qué puedo ayudarte?</h1>
        <p class="subtitulo-meta">Analiza tu cartera de cobros y riesgos con IA avanzada.</p>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 2. SISTEMA DE MENSAJES
    # ---------------------------------------------------------
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 3. MOSTRAR HISTORIAL (Si ya hay chat)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ---------------------------------------------------------
    # 4. PREGUNTAS SUGERIDAS (Solo si el chat está vacío)
    # ---------------------------------------------------------
    if not st.session_state.messages:
        col1, col2 = st.columns(2)
        
        # Estas son las "preguntas flotantes" que querías
        with col1:
            if st.button("📈 Simular análisis de riesgo actual", use_container_width=True):
                st.session_state.prompt_temporal = "¿Cuál es el riesgo de mi cartera hoy?"
            if st.button("💸 Calcular efectivo real neto", use_container_width=True):
                st.session_state.prompt_temporal = "¿Cuánto dinero real tengo restando los gastos?"
        
        with col2:
            if st.button("🚀 Proyectar ganancias del mes", use_container_width=True):
                st.session_state.prompt_temporal = "¿Qué proyección de ganancias tengo este mes?"
            if st.button("📊 Informe de rentabilidad global", use_container_width=True):
                st.session_state.prompt_temporal = "Hazme un resumen de la rentabilidad de mi negocio."

    # ---------------------------------------------------------
    # 5. INPUT DE CHAT (Estilo Global)
    # ---------------------------------------------------------
    prompt = st.chat_input("Pregunta a la IA de CobroYa...")

    # Si se usó un botón sugerido, lo capturamos
    if "prompt_temporal" in st.session_state and st.session_state.prompt_temporal:
        prompt = st.session_state.prompt_temporal
        del st.session_state.prompt_temporal

    if prompt:
        # Añadir pregunta del usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Lógica de respuesta (Groq)
        with st.chat_message("assistant"):
            with st.spinner("Procesando datos del negocio..."):
                # Recopilar datos reales
                p = conn.table("pagos").select("monto_pagado").eq("user_id", u_id).execute()
                g = conn.table("gastos").select("monto").eq("user_id", u_id).execute()
                c = conn.table("cuentas").select("balance_pendiente").eq("user_id", u_id).eq("estado", "Activo").execute()
                
                cobrado = sum([i['monto_pagado'] for i in p.data]) if p.data else 0
                gastado = sum([i['monto'] for i in g.data]) if g.data else 0
                riesgo = sum([i['balance_pendiente'] for i in c.data]) if c.data else 0
                
                contexto = f"Cobrado: {cobrado}, Gastado: {gastado}, Riesgo: {riesgo}. Responde como un analista bancario profesional."
                
                try:
                    respuesta = asistente_ia_cobroya(contexto, prompt)
                    st.markdown(respuesta)
                    st.session_state.messages.append({"role": "assistant", "content": respuesta})
                    
                except Exception as e:
                    # Esto nos dirá el error de verdad (ej. "Connection error" o "Rate limit")
                    st.error(f"Error real de la IA: {e}") 

# --- DENTRO DE LA SECCIÓN DEL CHAT DE IA ---
if menu == "IA Analista":
    with st.container():
        # Paso 1: Generar el contexto privado ANTES de que el usuario pregunte
        contexto_seguro = obtener_contexto_privado_ia(u_id) # u_id es el id del usuario logueado

        # Paso 2: Configurar las instrucciones para Gemini
        instrucciones_ia = f"""
        Eres VALE AI, un analista financiero privado y seguro. 
        Tu conocimiento se limita ESTRICTAMENTE a estos datos:
        
        {contexto_seguro}
        
        REGLAS DE ORO:
        - No inventes datos que no estén arriba.
        - No menciones que tienes un archivo de contexto, actúa con naturalidad.
        - Si te preguntan por riesgo, analiza quién debe más y quién tiene pagos cerca.
        - Tu objetivo es ayudar al dueño del negocio a cobrar mejor.
        """

        # Aquí es donde llamas a tu función de chat de Gemini
        st.title("🤖 Tu Analista Senior Privado")
        st.info("Estoy analizando tus datos en tiempo real para darte recomendaciones de cobro.")
        
        prompt = st.chat_input("Pregúntame sobre tus cobros o riesgos...")
        if prompt:
            st.write(f"Analizando tu cartera para responder: '{prompt}'...")

elif menu == "Configuración":
    st.header("⚙️ Configuración del Sistema")
    st.caption("Administra las cláusulas legales de tus contratos y la seguridad de tu cuenta.")

    # 1. Recuperar configuración actual de Supabase
    res_conf = conn.table("configuracion").select("*").eq("user_id", u_id).execute()
    
    clausulas_default = """1. EL DEUDOR se compromete a pagar la suma acordada en las fechas establecidas.
2. El incumplimiento de dos cuotas consecutivas autoriza al ACREEDOR a ejecutar el cobro total.
3. Este contrato tiene fuerza legal y ejecutiva."""
    
    if res_conf.data:
        texto_actual = res_conf.data[0].get("clausulas", clausulas_default)
    else:
        texto_actual = clausulas_default

    # --- SECCIÓN DE CLÁUSULAS LEGALES ---
    with st.expander("📝 Editar Cláusulas del Contrato PDF", expanded=True):
        st.write("Estas cláusulas aparecerán automáticamente en todos los contratos PDF que generes.")
        clausulas_editadas = st.text_area(
            "Texto legal del contrato:", 
            value=texto_actual, 
            height=250,
            help="Escribe aquí las condiciones que tus clientes deben firmar."
        )
        
        if st.button("💾 Guardar Configuración Legal", use_container_width=True):
            with st.spinner("Sincronizando con la base de datos..."):
                try:
                    if res_conf.data:
                        conn.table("configuracion").update({"clausulas": clausulas_editadas}).eq("user_id", u_id).execute()
                    else:
                        conn.table("configuracion").insert({"clausulas": clausulas_editadas, "user_id": u_id}).execute()
                    
                    st.session_state["mis_clausulas"] = clausulas_editadas
                    st.success("✅ Cláusulas actualizadas correctamente.")
                    import time
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # --- SECCIÓN DE DATOS DE EMPRESA ---
    with st.expander("🏢 Perfil del Negocio & Facturación", expanded=False):
        st.markdown("### Configura la identidad de tu empresa")
        
        # 1. Recuperar datos actuales
        biz_data = conn.table("configuracion").select("*").eq("user_id", u_id).execute()
        current_biz = biz_data.data[0] if biz_data.data else {}

        col_logo, col_info = st.columns([1, 2])
        
        with col_logo:
            logo_file = st.file_uploader("Cargar Logo (PNG/JPG)", type=["png", "jpg", "jpeg"])
            
            if logo_file:
                # Caso A: El usuario sube un archivo nuevo
                bytes_data = logo_file.getvalue()
                base64_logo = base64.b64encode(bytes_data).decode()
                st.image(bytes_data, width=150, caption="Nuevo Logo")
            else:
                # Caso B: No hay archivo nuevo, usamos el de la base de datos
                base64_logo = current_biz.get("logo_base64", "")
                if base64_logo:
                    try:
                        # Limpiamos el prefijo base64 si existe para mostrarlo en Streamlit
                        clean_view = base64_logo.split("base64,")[1] if "base64," in base64_logo else base64_logo
                        st.image(base64.b64decode(clean_view), width=150, caption="Logo Actual")
                    except:
                        st.warning("Error al previsualizar el logo guardado")

        with col_info:
            biz_name = st.text_input("Nombre Comercial", value=current_biz.get("nombre_negocio", "CobroYa Pro"))
            biz_id = st.text_input("RNC / Cédula Fiscal", value=current_biz.get("rnc", ""))
            biz_phone = st.text_input("Teléfono de Contacto", value=current_biz.get("telefono", ""))
            biz_addr = st.text_area("Dirección Física", value=current_biz.get("direccion", ""))

        # 2. Botón de Guardado con Sincronización Total
        if st.button("💾 Guardar Perfil Empresarial", use_container_width=True):
            # Aseguramos que el logo guardado sea el "string" limpio
            payload = {
                "nombre_negocio": biz_name,
                "rnc": biz_id,
                "telefono": biz_phone,
                "direccion": biz_addr,
                "logo_base64": base64_logo,
                "user_id": u_id
            }
            
            try:
                if current_biz:
                    conn.table("configuracion").update(payload).eq("user_id", u_id).execute()
                else:
                    conn.table("configuracion").insert(payload).execute()

                # ACTUALIZACIÓN CRÍTICA DEL SESSION_STATE (Para que el PDF lo vea sin refrescar manual)
                st.session_state["nombre_negocio"] = biz_name
                st.session_state["mi_logo"] = base64_logo
                st.session_state["direccion_negocio"] = biz_addr
                st.session_state["telefono_negocio"] = biz_phone
                st.session_state["config_cargada"] = True # Marcamos como cargado
                
                st.success("✅ ¡Identidad corporativa actualizada!")
                time.sleep(1)
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error al guardar en base de datos: {e}")
                
    # --- SECCIÓN DE SEGURIDAD ---
    with st.container(border=True):
        st.subheader("🔐 Seguridad de la Cuenta")
        st.write("Cambia tu contraseña de acceso directamente.")
        
        with st.form("cambio_clave_directo"):
            nueva_p = st.text_input("Nueva Contraseña", type="password", help="Mínimo 6 caracteres")
            confirma_p = st.text_input("Confirmar Nueva Contraseña", type="password")
            
            submit_pass = st.form_submit_button("Actualizar Contraseña Ahora")
            
            if submit_pass:
                if len(nueva_p) < 6:
                    st.error("La contraseña es muy corta.")
                elif nueva_p != confirma_p:
                    st.error("Las contraseñas no coinciden.")
                else:
                    try:
                        conn.client.auth.update_user({"password": nueva_p})
                        st.success("✅ ¡Contraseña actualizada con éxito!")
                        import time
                        time.sleep(2)
                    except Exception as e:
                        st.error(f"Error al actualizar: {e}")
