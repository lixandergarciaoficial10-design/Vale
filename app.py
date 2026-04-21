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
import streamlit as st

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

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

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
clientes_f = []
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
    
def generar_pdf_recibo_pro(nombre_cliente, monto, balance, user_id, mora=0):
    try:
        monto, balance, mora = float(monto), float(balance), float(mora)
    except:
        monto, balance, mora = 0.0, 0.0, 0.0
    
    # Tamaño estándar ticket 80mm
    pdf = FPDF(format=(80, 160)) 
    pdf.add_page()
    pdf.set_margins(4, 4, 4)
    pdf.set_auto_page_break(False)

    # 1. Recuperar info del negocio (Lo que sentías que faltaba)
    nombre_negocio = st.session_state.get("nombre_negocio", "COBROYA PRO").upper()
    rnc = st.session_state.get("rnc", "")
    direccion = st.session_state.get("direccion_negocio", "Rep. Dominicana")
    telefono = st.session_state.get("telefono_negocio", "")

    # --- ENCABEZADO ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(72, 7, nombre_negocio, ln=True, align='C')
    
    pdf.set_font("Helvetica", "", 8)
    if rnc: pdf.cell(72, 4, f"RNC: {rnc}", ln=True, align='C')
    pdf.cell(72, 4, direccion[:40], ln=True, align='C') # Truncamos para que no desborde
    if telefono: pdf.cell(72, 4, f"TEL: {telefono}", ln=True, align='C')
    
    pdf.cell(72, 4, "="*35, ln=True, align='C')
    
    # --- CUERPO DEL TICKET ---
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(72, 6, "COMPROBANTE DE COBRO", ln=True, align='C')
    pdf.set_font("Helvetica", "", 8)
    pdf.cell(72, 4, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(72, 4, f"No. Trans: {int(datetime.now().timestamp())}", ln=True)
    pdf.cell(72, 4, f"Cliente: {nombre_cliente.upper()}", ln=True)
    pdf.cell(72, 4, "-"*40, ln=True, align='C')

    # --- VALORES ---
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(40, 6, "ABONO RECIBIDO:")
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(32, 6, f"RD$ {monto:,.2f}", ln=True, align='R')

    if mora > 0:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(40, 6, "MORA COBRADA:")
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(32, 6, f"RD$ {mora:,.2f}", ln=True, align='R')

    pdf.ln(2)
    pdf.set_fill_color(245, 245, 245) # Gris muy suave
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(40, 8, " PENDIENTE:", fill=True)
    pdf.cell(32, 8, f"RD$ {balance:,.2f} ", ln=True, align='R', fill=True)
    
    # --- PIE ---
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 7)
    pdf.cell(72, 4, "_______________________", ln=True, align='C')
    pdf.cell(72, 4, "FIRMA DEL CLIENTE", ln=True, align='C')
    
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(72, 4, "¡Gracias por su pago!", ln=True, align='C')

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


def calcular_atraso_dinamico(fecha_proximo_pago):
    """Calcula el tiempo de atraso y devuelve un texto amigable y los días totales."""
    if not fecha_proximo_pago:
        return "Sin fecha", 0
    
    hoy = datetime.now().date()
    # Convertir si es string, si ya es objeto date se queda igual
    f_pago = datetime.strptime(fecha_proximo_pago, '%Y-%m-%d').date() if isinstance(fecha_proximo_pago, str) else fecha_proximo_pago
    
    dias_atraso = (hoy - f_pago).days
    if dias_atraso <= 0:
        return "Al día", 0
    
    if dias_atraso < 30:
        return f"{dias_atraso} días", dias_atraso
    elif dias_atraso < 365:
        meses = dias_atraso // 30
        dias = dias_atraso % 30
        return f"{meses} mes(es) y {dias} día(s)", dias_atraso
    else:
        años = dias_atraso // 365
        meses = (dias_atraso % 365) // 30
        return f"{años} año(s) y {meses} mes(es)", dias_atraso

def obtener_prioridad(dias, balance, impagos=0):
    """Calcula el Score de Prioridad basado en los pesos confirmados."""
    # Pesos: Días (50%), Monto (30%), Impagos (20%)
    # Normalizamos el balance (ej: dividir entre 10,000) para que sea comparable a días
    score = (dias * 0.5) + ((balance / 1000) * 0.3) + (impagos * 0.2)
    return score

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
    st.header("⚡ Centro de Recaudación")
    
    # --- 1. FUNCIÓN DE HISTORIAL (PLAN VS REAL) CON LÓGICA DINÁMICA ---
    @st.dialog("📜 ESTADO DE CUENTA DETALLADO")
    def mostrar_historial_modal(item, u_id):
        st.subheader(f"Análisis: {item['aux_nombre']}")
        
        # Consultamos el Plan y los Pagos Reales
        res_plan = conn.table("plan_cuotas").select("*").eq("cuenta_id", item['id']).order("numero_cuota").execute()
        res_pagos = conn.table("pagos").select("*").eq("cuenta_id", item['id']).order("fecha_pago").execute()
        
        plan = res_plan.data if res_plan.data else []
        pagos = res_pagos.data if res_pagos.data else []
        
        tab1, tab2 = st.tabs(["📅 Plan Original (Seguimiento)", "💵 Historial de Pagos Recibidos"])
        
        with tab1:
            if plan:
                # LÓGICA DE ESTADO DE CUENTA DINÁMICO
                total_pagado_acumulado = sum(float(p.get('monto_pagado', 0)) for p in pagos)
                progreso = total_pagado_acumulado
                
                datos_plan = []
                for cuota in plan:
                    monto_esperado = float(cuota['monto_cuota'])
                    
                    if progreso >= monto_esperado:
                        estado_actual = "✅ COMPLETA"
                        progreso -= monto_esperado
                    elif progreso > 0:
                        estado_actual = "⚠️ INCOMPLETA"
                        progreso = 0
                    else:
                        estado_actual = "⏳ PENDIENTE"
                    
                    datos_plan.append({
                        "Cuota #": cuota['numero_cuota'],
                        "Fecha de Pago": cuota['fecha_esperada'],
                        "Monto (RD$)": f"{monto_esperado:,.2f}",
                        "Estatus": estado_actual
                    })
                
                st.table(pd.DataFrame(datos_plan))
            else:
                st.warning("No hay un plan registrado para esta cuenta.")
        
        with tab2:
            if pagos:
                df_pagos = pd.DataFrame(pagos)
                col_fecha = 'fecha_pago' if 'fecha_pago' in df_pagos.columns else 'created_at'
                df_pagos['Fecha'] = pd.to_datetime(df_pagos[col_fecha]).dt.date
                
                df_pagos['Abono Capital'] = df_pagos['monto_pagado'].apply(lambda x: f"RD$ {float(x):,.2f}")
                df_pagos['Mora Pagada'] = df_pagos['mora_pagada'].apply(lambda x: f"RD$ {float(x):,.2f}")
                
                cols_finales = ['codigo_factura', 'Fecha', 'Abono Capital', 'Mora Pagada']
                df_mostrar = df_pagos[[c for c in cols_finales if c in df_pagos.columns]]
                df_mostrar.columns = ['Factura #', 'Fecha Cobro', 'Abono Capital', 'Mora Pagada']
                st.table(df_mostrar)
                
                total_cap = sum(float(p.get('monto_pagado', 0)) for p in pagos)
                total_mora = sum(float(p.get('mora_pagada', 0)) for p in pagos)
                
                c1, c2 = st.columns(2)
                c1.metric("Total Capital Recibido", f"RD$ {total_cap:,.2f}")
                c2.metric("Total Moras Recibidas", f"RD$ {total_mora:,.2f}")
            else:
                st.info("Aún no se han registrado pagos reales.")

    # --- 2. FUNCIÓN DE CONFIRMACIÓN CON GENERACIÓN DE CÓDIGO ---
    @st.dialog("⚠️ VERIFICAR TRANSACCIÓN")
    def confirmar_cobro_modal(item, monto, fecha, mora, u_id):
        import random
        import string
        
        codigo_random = f"FAC-{''.join(random.choices(string.digits, k=4))}"
        
        st.warning(f"¿Estás seguro de registrar este pago para **{item['aux_nombre']}**?")
        st.markdown(f"""
        **Resumen del Cobro:**
        * 🎫 **Factura #:** {codigo_random}
        * 💵 **Abono Capital:** RD$ {monto:,.2f}
        * ⚖️ **Mora Aplicada:** RD$ {mora:,.2f}
        * 📅 **Próximo Pago:** {fecha}
        """)
        
        c_conf1, c_conf2 = st.columns(2)
        with c_conf1:
            if st.button("✅ CONFIRMAR Y REGISTRAR", type="primary", use_container_width=True):
                try:
                    conn.table("pagos").insert({
                        "cuenta_id": str(item['id']),
                        "monto_pagado": float(monto),
                        "mora_pagada": float(mora),
                        "codigo_factura": codigo_random,
                        "user_id": str(u_id)
                    }).execute()
                    
                    n_bal = float(item.get('balance_pendiente', 0)) - monto
                    conn.table("cuentas").update({
                        "balance_pendiente": n_bal,
                        "estado": "Saldado" if n_bal <= 0 else "Activo",
                        "proximo_pago": str(fecha),
                        "mora_acumulada": 0
                    }).eq("id", item['id']).execute()
                    
                    st.session_state[f"recibo_{item['id']}"] = {
                        "monto": monto, "mora": mora, "pend": n_bal, "fecha": str(fecha), "factura": codigo_random
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"Error crítico en base de datos: {e}")
        
        with c_conf2:
            if st.button("❌ CANCELAR", use_container_width=True):
                st.rerun()

    # --- 3. FUNCIÓN DE RECIBO FINAL ---
    @st.dialog("🎯 ¡COBRO REALIZADO CON ÉXITO!")
    def mostrar_recibo_modal(item, r, u_id):
        st.balloons()
        st.success(f"Pago registrado: **{r['factura']}**")
        
        c1, c2 = st.columns(2)
        c1.metric("Monto Cobrado", f"RD$ {r['monto']:,.2f}")
        c2.metric("Nuevo Balance", f"RD$ {r['pend']:,.2f}")
        
        st.divider()
        pdf_bytes = generar_pdf_recibo_pro(item['aux_nombre'], r['monto'], r['pend'], u_id, mora=r['mora'])
        st.download_button(
            label="🖨️ IMPRIMIR RECIBO TÉRMICO",
            data=pdf_bytes,
            file_name=f"Recibo_{r['factura']}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
        
        import urllib.parse
        clean_tel = "".join(filter(str.isdigit, str(item['clientes']['telefono'])))
        msg = (f"✅ *RECIBO DE PAGO ({r['factura']})*\n\n"
               f"Cliente: *{item['aux_nombre']}*\n"
               f"Abono: *RD$ {r['monto']:,.2f}*\n"
               f"Mora: *RD$ {r['mora']:,.2f}*\n"
               f"Balance Pendiente: *RD$ {r['pend']:,.2f}*\n"
               f"Próximo Pago: {r['fecha']}\n\n"
               f"¡Gracias por su puntualidad!")
        url = f"https://wa.me/1{clean_tel}?text={urllib.parse.quote(msg)}"
        st.markdown(f'<a href="{url}" target="_blank"><button style="width:100%;background-color:#25D366;color:white;border:none;padding:12px;border-radius:10px;font-weight:bold;cursor:pointer;">WhatsApp 💬</button></a>', unsafe_allow_html=True)
        
        if st.button("✅ FINALIZAR", use_container_width=True):
            st.rerun()

    # --- 4. CONTROLES SUPERIORES ---
    col_search, col_view = st.columns([2, 1])
    with col_search:
        search_term = st.text_input("🔍 Buscar cliente...", placeholder="Nombre, Cédula o Teléfono...").lower()
    with col_view:
        modo_analisis = st.toggle("📈 Modo Análisis", help="Ver cuentas saldadas")

    # --- 5. CONSULTA DE DATOS ---
    # Traemos nombre, cedula y telefono para el filtrado multidimensional
    query = conn.table("cuentas").select("*, clientes(nombre, telefono, cedula)").eq("user_id", u_id)
    query = query.lte("balance_pendiente", 0) if modo_analisis else query.gt("balance_pendiente", 0)
    res = query.execute()
    
    if res.data:
        datos_procesados = []
        for c in res.data:
            cliente_info = c.get('clientes', {})
            nombre = cliente_info.get('nombre', 'Cliente')
            cedula = cliente_info.get('cedula', '')
            telefono = cliente_info.get('telefono', '')
            
            # Lógica de búsqueda: Nombre OR Cédula OR Teléfono
            if (search_term in nombre.lower() or 
                search_term in str(cedula).lower() or 
                search_term in str(telefono).lower()):
                
                txt_atraso_base, dias_num = calcular_atraso_dinamico(c.get('proximo_pago'))
                if dias_num > 0:
                    txt_atraso = f"Han pasado {dias_num} días desde la fecha de pago acordada"
                else:
                    txt_atraso = txt_atraso_base
                
                c['aux_nombre'] = nombre
                c['aux_atraso_txt'] = txt_atraso
                c['aux_dias_num'] = dias_num
                c['aux_prioridad'] = obtener_prioridad(dias_num, float(c.get('balance_pendiente', 0)))
                datos_procesados.append(c)

        datos_procesados = sorted(datos_procesados, key=lambda x: x['aux_prioridad'], reverse=True)

        for item in datos_procesados:
            token = item['id']
            m_pend = float(item.get('balance_pendiente', 0))
            
            if f"recibo_{token}" in st.session_state:
                mostrar_recibo_modal(item, st.session_state[f"recibo_{token}"], u_id)
                del st.session_state[f"recibo_{token}"]

            with st.container(border=True):
                c_nom, c_status, c_inputs, c_btn = st.columns([1.2, 1, 1.2, 0.8])
                
                with c_nom:
                    st.markdown(f"**{item['aux_nombre']}**")
                    st.caption(f"Debe: RD$ {m_pend:,.2f}")
                    if st.button("🔍 Ver Historial", key=f"hist_{token}", use_container_width=True):
                        mostrar_historial_modal(item, u_id)

                with c_status:
                    if modo_analisis: st.info("✅ SALDADO")
                    elif item['aux_dias_num'] > 0: st.error(f"⚠️ {item['aux_atraso_txt']}")
                    else: st.success("🟢 Al día")
                        
                with c_inputs:
                    if not modo_analisis:
                        cuota_acordada = float(item.get('cuota_esperada', 0))
                        valor_default = min(cuota_acordada, m_pend) if cuota_acordada > 0 else m_pend
                        
                        st.caption(f"Cuota acordada: RD$ {cuota_acordada:,.2f}")
                        abono_input = st.number_input("Monto", min_value=0.0, value=float(valor_default), key=f"val_{token}", label_visibility="collapsed")
                        f_prox_input = st.date_input("Próxima", key=f"date_{token}", label_visibility="collapsed")
                    else:
                        st.write(f"Saldó el: {item.get('proximo_pago')}")

                with c_btn:
                    if not modo_analisis:
                        st.write("")
                        if st.button("💵 COBRAR", key=f"reg_{token}", type="primary", use_container_width=True):
                            v_mora = st.session_state.get(f"mora_{token}", 0.0)
                            confirmar_cobro_modal(item, abono_input, f_prox_input, v_mora, u_id)
                    else:
                        st.button("📄 Detalles", key=f"info_{token}", use_container_width=True)

                if not modo_analisis:
                    with st.expander("⚖️ Penalidad (Mora)"):
                        st.caption("Este monto se guarda como ingreso por mora y no resta capital.")
                        st.number_input("Monto de Mora", min_value=0.0, key=f"mora_{token}")
    else:
        st.info("No se encontraron clientes activos.")
        
elif menu == "Nueva Cuenta por Cobrar":
    st.header("🏢 Registro de Nueva Factura")
    
    # Librería esencial para saltos de meses y días de semana exactos
    from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

    contenedor_formulario = st.empty()

    # 0. AUDITORÍA DE DEUDAS Y CARGA DE CLIENTES ORDENADOS
    # Se añade .order("fecha_registro", desc=True) para que los más recientes aparezcan primero
    res_cli = conn.table("clientes").select("id, nombre, cedula, telefono").eq("user_id", u_id).order("fecha_registro", desc=True).execute()
    res_activas = conn.table("cuentas").select("cliente_id, balance_pendiente").eq("user_id", u_id).gt("balance_pendiente", 0).execute()
    
    resumen_deudas = {}
    if res_activas.data:
        for d in res_activas.data:
            c_id = d['cliente_id']
            resumen_deudas[c_id] = resumen_deudas.get(c_id, {'cantidad': 0, 'total': 0})
            resumen_deudas[c_id]['cantidad'] += 1
            resumen_deudas[c_id]['total'] += float(d['balance_pendiente'])

    if "prestamo_exitoso" in st.session_state:
        # --- UI DE ÉXITO ---
        with st.container(border=True):
            st.balloons()
            st.success(f"### ✅ ¡Préstamo Activado para {st.session_state.last_name}!")
            st.write("La cuenta y su calendario de pagos han sido registrados correctamente.")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.download_button("📥 Descargar Contrato PDF", data=st.session_state.pdf_ready, file_name=f"Factura_{st.session_state.last_name}.pdf", use_container_width=True)
            with c2:
                st.markdown(f'''<a href="{st.session_state.wa_link}" target="_blank"><button style="width:100%; background:#25D366; color:white; border:none; padding:10px; border-radius:10px; cursor:pointer; font-weight:bold; height:45px;">💬 Enviar WhatsApp</button></a>''', unsafe_allow_html=True)
            with c3:
                if st.button("🔄 Crear otra factura", use_container_width=True):
                    for k in ["prestamo_exitoso", "pdf_ready", "wa_link", "last_name"]:
                        if k in st.session_state: del st.session_state[k]
                    st.rerun()
    else:
        with contenedor_formulario.container():
            if res_cli.data:
                col1, col2, col3 = st.columns(3)
                with col1:
                    # IMPLEMENTACIÓN DE BUSCADOR POR NOMBRE, CÉDULA O TELÉFONO
                    # index=None asegura que no haya un cliente seleccionado por defecto
                    cliente_obj = st.selectbox(
                        "Seleccionar Cliente", 
                        options=res_cli.data, 
                        index=None,
                        placeholder="Buscar por nombre, cédula o teléfono...",
                        format_func=lambda x: f"{x['nombre']} ({x.get('cedula', 'S/C')}) - {x.get('telefono', 'S/T')}" if x else ""
                    )
                    
                    capital = st.number_input("Capital/Venta (RD$)", min_value=0.0, step=100.0)
                    
                    # Lógica de validación si hay un cliente seleccionado
                    continuar = False
                    if cliente_obj:
                        if cliente_obj['id'] in resumen_deudas:
                            info = resumen_deudas[cliente_obj['id']]
                            st.error(f"⚠️ EL CLIENTE YA DEBE: RD$ {info['total']:,.2f}")
                            continuar = st.checkbox("Autorizar nueva factura manual")
                        else:
                            st.success("✅ Cliente al día")
                            continuar = True
                    else:
                        st.info("Por favor, selecciona un cliente para continuar.")
                
                with col2:
                    porcentaje = st.number_input("Interés (%)", min_value=0, value=20)
                    freq_sel = st.selectbox("Frecuencia de Pago", ["Semanal", "Quincenal", "Mensual"], index=0)
                    
                    # --- DÍA FIJO ---
                    dias_semana = {"Cada 7 día": None, "Lunes": MO, "Martes": TU, "Miércoles": WE, "Jueves": TH, "Viernes": FR, "Sábado": SA, "Domingo": SU}
                    
                    if freq_sel == "Semanal":
                        dia_input = st.selectbox("Día de cobro fijo", list(dias_semana.keys()), index=0)
                        dia_fijo = dias_semana[dia_input]
                    else:
                        dia_fijo = st.number_input("Día del mes (0 = Igual a hoy)", min_value=0, max_value=31, value=0)
                
                with col3:
                    cuotas_n = st.number_input("Cantidad de Cuotas", min_value=1, value=4)
                    fecha_desembolso = st.date_input("Fecha de desembolso", value=datetime.now().date())

                # --- MOTOR DE CÁLCULO DE FECHAS ---
                fechas_proyectadas = []
                referencia = fecha_desembolso 

                for i in range(cuotas_n):
                    if freq_sel == "Semanal":
                        if dia_fijo is None:
                            next_date = referencia + relativedelta(weeks=i+1)
                        else:
                            next_date = referencia + relativedelta(weeks=i+1, weekday=dia_fijo)
                    
                    elif freq_sel == "Quincenal":
                        next_date = referencia + relativedelta(days=(i+1)*15)
                    
                    elif freq_sel == "Mensual":
                        if dia_fijo == 0:
                            next_date = referencia + relativedelta(months=i+1)
                        else:
                            next_date = referencia + relativedelta(months=i+1, day=dia_fijo)

                    fechas_proyectadas.append(next_date)

                total_esp = capital * (1 + (porcentaje / 100))
                monto_c_base = total_esp / cuotas_n if cuotas_n > 0 else 0

                st.markdown("#### 📊 Resumen de la Operación")
                m1, m2, m3 = st.columns(3)
                m1.metric("Inversión", f"RD$ {capital:,.2f}")
                m2.metric("Ganancia", f"RD$ {total_esp - capital:,.2f}")
                m3.metric("Total a Cobrar", f"RD$ {total_esp:,.2f}")

                # Función para formatear fecha a "Día de Mes de Año"
                def fecha_legible(f):
                    meses = ["enero", "febrero", "marzo", "abril", "mayo", "junio", 
                             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
                    return f"{f.day} de {meses[f.month - 1]} del {f.year}"

                # Tabla interactiva
                df_p = pd.DataFrame([{
                    "Nº": i + 1,
                    "Fecha": fechas_proyectadas[i],
                    "Monto Cuota (RD$)": round(monto_c_base, 2)
                } for i in range(cuotas_n)])
                
                st.info("💡 **Puedes editar la fecha o el monto directamente en la tabla** si necesitas ajustar el plan.")
                
                # Mostramos el editor
                df_e = st.data_editor(df_p, use_container_width=True, key="editor_p")
                
                # Recalcular totales DESDE LO QUE ESTÁ EN LA TABLA EDITADA
                total_f = float(df_e["Monto Cuota (RD$)"].sum())
                cuota_esperada_f = total_f / cuotas_n

                if st.button("🚀 REGISTRAR Y ACTIVAR", use_container_width=True, disabled=not (capital > 0 and continuar and cliente_obj is not None)):
                    # IMPORTANTE: Tomamos la fecha de la tabla, por si el usuario la editó
                    primera_fecha_final = df_e.iloc[0]['Fecha']
                    
                    # 1. Insertar en CUENTAS
                    res_c = conn.table("cuentas").insert({
                        "cliente_id": cliente_obj['id'], 
                        "monto_inicial": total_f,
                        "balance_pendiente": total_f, 
                        "user_id": u_id,
                        "estado": "Activo", 
                        "proximo_pago": str(primera_fecha_final),
                        "cuota_esperada": float(cuota_esperada_f),
                        "frecuencia_pago": freq_sel
                    }).execute()

                    if res_c.data:
                        nueva_id = res_c.data[0]['id']
                        # 2. Insertar PLAN_CUOTAS (Respetando cada edición de fecha y monto)
                        filas_plan = []
                        for _, row in df_e.iterrows():
                            filas_plan.append({
                                "cuenta_id": nueva_id,
                                "numero_cuota": int(row["Nº"]),
                                "fecha_esperada": str(row["Fecha"]), 
                                "monto_cuota": float(row["Monto Cuota (RD$)"]),
                                "estado": "Pendiente",
                                "user_id": u_id
                            })
                        conn.table("plan_cuotas").insert(filas_plan).execute()

                        # 3. Documentos y WhatsApp
                        pdf_out = generar_pdf_contrato_legal(
                            cliente_obj['nombre'], cliente_obj.get('cedula', 'S/N'), 
                            float(capital), float(total_f), df_e, freq_sel,
                            st.session_state.get("mis_clausulas", "Sujeto a mora por retraso.")
                        )

                        st.session_state.pdf_ready = pdf_out
                        st.session_state.last_name = cliente_obj['nombre']
                        st.session_state.prestamo_exitoso = True
                        
                        # Formato legible para WhatsApp
                        import pandas as pd
                        f_obj = pd.to_datetime(df_e.iloc[0]['Fecha'])
                        fecha_wa = fecha_legible(f_obj)
                        
                        wa_msg = f"✅ *NUEVO CRÉDITO REGISTRADO*\n\n" \
                                 f"Hola {cliente_obj['nombre']},\n" \
                                 f"Detalles de tu cuenta:\n" \
                                 f"💰 *Total:* RD$ {total_f:,.2f}\n" \
                                 f"🗓️ *{cuotas_n} pagos* de RD$ {cuota_esperada_f:,.2f}\n" \
                                 f"📅 *Primer pago:* {fecha_wa}"
                        
                        import requests
                        st.session_state.wa_link = f"https://wa.me/{cliente_obj.get('telefono', '')}?text={requests.utils.quote(wa_msg)}"
                        st.rerun()
                    else:
                        st.error("Error al guardar en base de datos.")
                    
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

        # --- VENTANA DE HISTORIAL (MODAL REDISEÑADO "ULTRA PREMIUM") ---
# --- FUNCIONES DE APOYO (Deben ir fuera del modal o antes de él) ---
def reajustar_cuenta_post_borrado(c_id, monto_recuperado, balance_actual):
    """Recalcula el balance y el estado de la cuenta automáticamente."""
    nuevo_balance = float(balance_actual) + float(monto_recuperado)
    # Si el balance es mayor a 0, la cuenta vuelve a estar 'AL DÍA' o 'PENDIENTE'
    nuevo_estado = "AL DÍA" if nuevo_balance > 0 else "PAGADA"
    
    conn.table("cuentas").update({
        "balance_pendiente": nuevo_balance,
        "estado": nuevo_estado
    }).eq("id", c_id).execute()
    return nuevo_balance, nuevo_estado

def registrar_log(accion, tabla, registro_id, antes, despues, u_id):
    """Registra cada movimiento para auditoría."""
    conn.table("logs_financieros").insert({
        "user_id": u_id,
        "accion": accion,
        "tabla_afectada": tabla,
        "registro_id": registro_id,
        "datos_antes": antes,
        "datos_despues": despues
    }).execute()

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time

# --- 1. LÓGICA DE SEGURIDAD Y LIMPIEZA DE DATOS (PROCESAMIENTO) ---

def limpiar_fecha(f):
    """Evita errores de ordenamiento asegurando un objeto datetime válido para el historial."""
    if f is None:
        return datetime.now()
    try:
        # Convertir a datetime y quitar zona horaria para poder comparar correctamente
        return pd.to_datetime(f).replace(tzinfo=None)
    except:
        return datetime.now()

def puede_gestionar_48h(fecha_registro):
    """Candado de seguridad de 48 horas para ediciones y borrados de abonos."""
    if not fecha_registro: return False
    ahora = datetime.now()
    try:
        f_reg = pd.to_datetime(fecha_registro).replace(tzinfo=None)
        return (ahora - f_reg) < timedelta(hours=48)
    except: return False

def registrar_log_detallado(accion, tabla, registro_id, antes, despues, u_id, nota=""):
    """Guarda rastro de cada movimiento para auditoría total del negocio."""
    detalles = {
        "user_id": u_id,
        "accion": accion,
        "tabla_afectada": tabla,
        "registro_id": registro_id,
        "datos_antes": antes,
        "datos_despues": despues,
        "nota_adicional": nota,
        "fecha_log": datetime.now().isoformat()
    }
    conn.table("logs_financieros").insert(detalles).execute()

# --- 2. MODAL DE GESTIÓN (DISEÑO APPLE-INTUITIVO Y COMPLETO) ---

@st.dialog("📦 Expediente Digital de Cliente", width="large")
def modal_detalle(cliente, cuentas, pagos, u_id=None):
    if u_id is None: u_id = st.session_state.get('user_id', '0000')

    # CSS para estética Premium (Pestañas limpias y bordes suaves)
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: #f0f2f6;
            border-radius: 10px 10px 0px 0px;
            padding: 10px 20px;
            font-weight: 600;
        }
        .stTabs [aria-selected="true"] { background-color: #007AFF !important; color: white !important; }
        .log-entry { padding: 10px; border-bottom: 1px solid #eee; font-family: 'Courier New', Courier, monospace; font-size: 13px; }
        </style>
    """, unsafe_allow_html=True)

    # Cabecera de Identidad
    st.title(f"👤 {cliente['nombre']}")
    st.caption(f"ID Cliente: {cliente.get('id')} | Cédula: {cliente.get('cedula', 'N/A')}")

    # Sistema de Navegación por Pestañas (Navegación Intuitiva)
    tab_abonos, tab_plan, tab_historial, tab_perfil = st.tabs([
        "💰 ABONOS REALES", "📅 PLAN IDEAL", "📜 HISTORIAL COMPLETO", "⚙️ PERFIL"
    ])

    mis_ctas = [ct for ct in cuentas if ct['cliente_id'] == cliente['id']]
    
    # --- PESTAÑA 4: PERFIL (Fuera del bucle para evitar error de duplicados) ---
    with tab_perfil:
        st.markdown("### Datos del Titular")
        # Clave única para el formulario basada en el cliente
        with st.form(key=f"form_perfil_{cliente['id']}"):
            n_nom = st.text_input("Nombre Completo", value=cliente['nombre'])
            n_ced = st.text_input("Cédula / Pasaporte", value=cliente.get('cedula',''))
            n_tel = st.text_input("Teléfono de Contacto", value=cliente.get('telefono',''))
            
            if st.form_submit_button("Guardar Cambios en Perfil", use_container_width=True):
                conn.table("clientes").update({
                    "nombre": n_nom, 
                    "cedula": n_ced, 
                    "telefono": n_tel
                }).eq("id", cliente['id']).execute()
                st.success("✅ Información del perfil actualizada.")
                time.sleep(0.5)
                st.rerun()

    if not mis_ctas:
        st.warning("Este cliente no tiene facturas activas en el sistema.")
        return

    # Iteración por facturas para las pestañas de datos financieros
    for ct in mis_ctas:
        c_id = ct['id']
        mis_pagos_cta = [p for p in pagos if p.get('cuenta_id') == c_id]
        
# --- PESTAÑA 1: ABONOS REALES (INTERFAZ TIPO CAJA / EXCEL) ---
        with tab_abonos:
            st.markdown(f"### 📄 Factura: {str(c_id)[:8].upper()}")
            st.metric("💰 Balance Pendiente", f"RD$ {float(ct['balance_pendiente']):,.2f}")
            
            if not mis_pagos_cta:
                st.info("No hay abonos registrados en esta factura.")
            else:
                # 1. Preparar el DataFrame para la "Libreta de Cobros"
                data_libreta = []
                for p in mis_pagos_cta:
                    data_libreta.append({
                        "ID": p["id"],
                        "Fecha": pd.to_datetime(p.get('fecha_pago')).strftime('%d/%m/%Y'),
                        "Código": p.get('codigo_factura', 'ABONO'),
                        "Monto (RD$)": float(p['monto_pagado']),
                        "Estado": "🔓 Editable" if puede_gestionar_48h(p.get('created_at')) else "🔒 Cerrado"
                    })
                
                df_original = pd.DataFrame(data_libreta)

                # 2. Renderizar el Editor tipo Excel
                st.write("📝 **Libreta de Abonos** (Edita el monto directamente)")
                edited_df = st.data_editor(
                    df_original,
                    use_container_width=True,
                    hide_index=True,
                    disabled=["ID", "Fecha", "Código", "Estado"], # Solo el Monto es editable
                    column_config={
                        "ID": None, # Columna oculta
                        "Monto (RD$)": st.column_config.NumberColumn(
                            "Monto (RD$)", 
                            format="RD$ %.2f", 
                            min_value=0,
                            help="Presiona Enter para confirmar el cambio"
                        ),
                        "Estado": st.column_config.TextColumn("Seguridad", width="small")
                    },
                    key=f"editor_caja_{c_id}"
                )

                # 3. Lógica de Sincronización Automática
                if not edited_df.equals(df_original):
                    # Identificar la fila que cambió
                    for i, row in edited_df.iterrows():
                        orig_row = df_original.iloc[i]
                        
                        if row["Monto (RD$)"] != orig_row["Monto (RD$)"]:
                            # Validar seguridad antes de procesar
                            if "🔓" in row["Estado"]:
                                dif = row["Monto (RD$)"] - orig_row["Monto (RD$)"]
                                n_bal = float(ct['balance_pendiente']) - dif
                                
                                # Ejecutar actualización dual
                                conn.table("cuentas").update({"balance_pendiente": n_bal}).eq("id", c_id).execute()
                                conn.table("pagos").update({"monto_pagado": row["Monto (RD$)"]}).eq("id", row["ID"]).execute()
                                
                                registrar_log_detallado("EDICION_EXCEL", "pagos", row["ID"], orig_row["Monto (RD$)"], row["Monto (RD$)"], u_id)
                                st.toast(f"✅ Pago {row['Código']} actualizado")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Este registro está bloqueado (pasaron más de 48h).")
                                time.sleep(1)
                                st.rerun()

                # 4. Sección de Borrado Rápido (Fuera de la tabla para evitar errores de edición)
                with st.expander("🗑️ Eliminar un registro"):
                    id_a_borrar = st.selectbox("Seleccione el abono a eliminar", 
                                             options=df_original[df_original["Estado"].str.contains("🔓")]["ID"],
                                             format_func=lambda x: f"ID: {x} - RD$ {df_original[df_original['ID']==x]['Monto (RD$)'].values[0]:,.2f}")
                    
                    if st.button("Confirmar Eliminación", type="primary", use_container_width=True):
                        monto_borrar = df_original[df_original["ID"] == id_a_borrar]["Monto (RD$)"].values[0]
                        n_bal_del = float(ct['balance_pendiente']) + monto_borrar
                        
                        conn.table("cuentas").update({"balance_pendiente": n_bal_del}).eq("id", c_id).execute()
                        conn.table("pagos").delete().eq("id", id_a_borrar).execute()
                        
                        registrar_log_detallado("BORRADO_EXCEL", "pagos", id_a_borrar, monto_borrar, 0, u_id)
                        st.toast("🗑️ Abono eliminado correctamente")
                        time.sleep(0.5)
                        st.rerun()

        # --- PESTAÑA 2: PLAN IDEAL (CON DESPLIEGUE) ---
        with tab_plan:
            st.markdown(f"### Plan Original - Factura {str(c_id)[:8].upper()}")
            
            with st.expander("👁️ Ver desglose de cuotas acordadas", expanded=False):
                res_plan = conn.table("plan_cuotas").select("*").eq("cuenta_id", c_id).order("numero_cuota").execute()
                
                st.divider()
                # Disclaimer invasivo para edición
                edit_plan_mode = st.checkbox("🔓 Activar Edición del Plan (Modo Error)", key=f"chk_plan_{c_id}")
                if edit_plan_mode:
                    st.error("⚠️ Estás editando el PLAN IDEAL. Úsalo solo para corregir errores de creación.")

                if res_plan.data:
                    progreso_recorrido = sum(float(p['monto_pagado']) for p in mis_pagos_cta)
                    for cuota in res_plan.data:
                        m_cuota = float(cuota['monto_cuota'])
                        f_venc = pd.to_datetime(cuota['fecha_esperada']).date()
                        
                        # Lógica de estados clara
                        if progreso_recorrido >= m_cuota:
                            st.success(f"Cuota {cuota['numero_cuota']} - PAGADA (RD$ {m_cuota:,.2f})")
                            progreso_recorrido -= m_cuota
                        elif progreso_recorrido > 0:
                            st.warning(f"Cuota {cuota['numero_cuota']} - ABONO PARCIAL (Resta RD$ {m_cuota-progreso_recorrido:,.2f})")
                            progreso_recorrido = 0
                        else:
                            vencida = f_venc < datetime.now().date()
                            color = "red" if vencida else "gray"
                            txt = "VENCIDA" if vencida else "PENDIENTE"
                            st.markdown(f"**Cuota {cuota['numero_cuota']}** - <span style='color:{color}'>{txt} ({f_venc.strftime('%d/%m/%Y')})</span>", unsafe_allow_html=True)
                        
                        if edit_plan_mode:
                            with st.popover(f"Editar Cuota {cuota['numero_cuota']}"):
                                n_m_c = st.number_input("Nuevo Monto", value=m_cuota, key=f"p_edit_{cuota['id']}")
                                if st.button("Guardar", key=f"p_save_{cuota['id']}"):
                                    conn.table("plan_cuotas").update({"monto_cuota": n_m_c}).eq("id", cuota['id']).execute()
                                    registrar_log_detallado("EDIT_PLAN_IDEAL", "plan_cuotas", cuota['id'], m_cuota, n_m_c, u_id)
                                    st.rerun()

        # --- PESTAÑA 3: HISTORIAL (TEXTO CLARO E INMÓVIL) ---
        with tab_historial:
            st.markdown(f"### Auditoría de Factura {str(c_id)[:8].upper()}")
            logs_db = conn.table("logs_financieros").select("*").eq("registro_id", c_id).execute().data
            
            timeline = []
            # Evento inicial de la cuenta
            timeline.append({
                "f": limpiar_fecha(ct.get('fecha_creacion')), 
                "m": f"REGISTRO INICIAL: Factura creada por RD$ {float(ct['monto_inicial']):,.2f}."
            })
            # Registro de pagos realizados
            for p in mis_pagos_cta:
                timeline.append({
                    "f": limpiar_fecha(p.get('created_at') or p.get('fecha_pago')), 
                    "m": f"PAGO REGISTRADO: Recibido abono de RD$ {float(p['monto_pagado']):,.2f} (Cód: {p.get('codigo_factura')})."
                })
            # Registro de cambios por sistema (Logs)
            if logs_db:
                for l in logs_db:
                    timeline.append({
                        "f": limpiar_fecha(l.get('fecha_log')), 
                        "m": f"AJUSTE DE SISTEMA: Acción {l['accion']} ejecutada sobre {l['tabla_afectada']}."
                    })
            
            # Ordenamiento robusto (descendente por fecha)
            for item in sorted(timeline, key=lambda x: x['f'], reverse=True):
                st.markdown(f"""
                    <div class="log-entry">
                        <span style="color:#007AFF; font-weight:bold;">[{item['f'].strftime('%d/%m/%Y %I:%M %p')}]</span><br>
                        {item['m']}
                    </div>
                """, unsafe_allow_html=True)

    st.divider()
    if st.button("Cerrar Expediente del Cliente", use_container_width=True):
        st.rerun()

# --- GRID DE CLIENTES (CORREGIDO) ---
if menu == "👥 Todos mis Clientes":
    if not clientes_f:
        st.warning("No hay clientes que coincidan con la búsqueda o filtro.")
    else:
        grid = st.columns(3)
        for idx, cl in enumerate(clientes_f):
            with grid[idx % 3]:
                with st.container(border=True):
                    # 1. Cabecera de Tarjeta
                    st.markdown(f"**{cl['nombre']}**")
                    st.caption(f"🆔 {cl.get('cedula', 'N/A')}")
                    
                    # 2. Botones de Acción
                    b1, b2, b3 = st.columns(3)
                    with b1:
                        if st.button("📂", key=f"h_{cl['id']}", use_container_width=True):
                            modal_detalle(cl, cuentas_db, pagos_db)
                    
                    with b2:
                        tel = "".join(filter(str.isdigit, str(cl.get('telefono', ''))))
                        wa_url = f"https://wa.me/{tel}"
                        st.markdown(f'''<a href="{wa_url}" target="_blank">
                            <button style="width:100%; background:#25D366; border:none; padding:8px; border-radius:10px; cursor:pointer; display:flex; justify-content:center;">
                                <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" width="18">
                            </button></a>''', unsafe_allow_html=True)
                    
                    with b3:
                        lat, lon = cl.get('latitud'), cl.get('longitud')
                        if lat and str(lat) not in ["0", "0.0", "None"]:
                            map_url = f"https://www.google.com/maps?q={lat},{lon}"
                            st.markdown(f'''<a href="{map_url}" target="_blank">
                                <button style="width:100%; background:white; border:1px solid #ddd; padding:8px; border-radius:10px; cursor:pointer; display:flex; justify-content:center;">
                                    <img src="https://upload.wikimedia.org/wikipedia/commons/a/aa/Google_Maps_icon_%282020%29.svg" width="18">
                                </button></a>''', unsafe_allow_html=True)
                        else:
                            st.button("📵", disabled=True, key=f"no_gps_{cl['id']}", use_container_width=True)

                    # 3. Centro de Gestión (Popover)
                    with st.popover("⚙️ Ajustes", use_container_width=True):
                        g1, g2 = st.columns(2)
                        with g1:
                            if st.button("✏️ Editar", key=f"e_b_{cl['id']}", use_container_width=True):
                                st.session_state[f"editing_{cl['id']}"] = True
                                st.rerun()
                        with g2:
                            # CORRECCIÓN: Este botón ya NO borra, solo activa el Paso 1
                            if st.button("🗑️ Borrar", key=f"d_b_{cl['id']}", type="primary", use_container_width=True):
                                st.session_state[f"del_step_{cl['id']}"] = 1
                                st.rerun()

                    # --- LÓGICA DE EDICIÓN ---
                    if st.session_state.get(f"editing_{cl['id']}"):
                        st.markdown("---")
                        st.caption("⚠️ **DISCLAIMER:** La modificación de estos datos es irreversible y afectará los reportes.")
                        
                        e_nom = st.text_input("Nombre", value=cl['nombre'], key=f"en_{cl['id']}")
                        e_ced = st.text_input("Cédula", value=cl.get('cedula', ''), key=f"ec_{cl['id']}")
                        e_tel = st.text_input("Teléfono", value=cl.get('telefono', ''), key=f"et_{cl['id']}")
                        
                        c_la, c_lo = st.columns(2)
                        e_lat = c_la.text_input("Latitud", value=str(cl.get('latitud', '0.0')), key=f"elat_{cl['id']}")
                        e_lon = c_lo.text_input("Longitud", value=str(cl.get('longitud', '0.0')), key=f"elon_{cl['id']}")

                        col_ed1, col_ed2 = st.columns(2)
                        with col_ed1:
                            if st.button("💾 Guardar", key=f"sv_{cl['id']}", type="primary", use_container_width=True):
                                try:
                                    conn.table("clientes").update({
                                        "nombre": e_nom, "cedula": e_ced, "telefono": e_tel,
                                        "latitud": float(e_lat), "longitud": float(e_lon)
                                    }).eq("id", cl['id']).execute()
                                    st.toast("✅ ¡Datos actualizados!")
                                    del st.session_state[f"editing_{cl['id']}"]
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        with col_ed2:
                            if st.button("Cancelar", key=f"can_ed_{cl['id']}", use_container_width=True):
                                del st.session_state[f"editing_{cl['id']}"]
                                st.rerun()

                    # --- LÓGICA DE ELIMINAR (TRIPLE CONFIRMACIÓN REAL) ---
                    step_key = f"del_step_{cl['id']}"
                    actual_step = st.session_state.get(step_key, 0)

                    if actual_step == 1:
                        st.error("🚨 **PASO 1:** ¿Desea borrar este cliente?")
                        if st.button("SÍ, CONTINUAR", key=f"d1_{cl['id']}", use_container_width=True):
                            st.session_state[step_key] = 2
                            st.rerun()
                        if st.button("CANCELAR", key=f"c1_{cl['id']}", use_container_width=True):
                            st.session_state[step_key] = 0
                            st.rerun()
                    
                    elif actual_step == 2:
                        st.warning("⚠️ **PASO 2:** Se perderán los históricos.")
                        if st.button("SÍ, ESTOY SEGURO", key=f"d2_{cl['id']}", type="primary", use_container_width=True):
                            st.session_state[step_key] = 3
                            st.rerun()
                        if st.button("VOLVER", key=f"c2_{cl['id']}", use_container_width=True):
                            st.session_state[step_key] = 1
                            st.rerun()

                    elif actual_step == 3:
                        st.error("❗ **PASO 3:** ÚLTIMA ADVERTENCIA.")
                        # AQUÍ ES EL ÚNICO LUGAR DONDE SE BORRA DE LA BASE DE DATOS
                        if st.button("BORRAR DEFINITIVAMENTE", key=f"d3_{cl['id']}", type="primary", use_container_width=True):
                            try:
                                conn.table("clientes").delete().eq("id", cl['id']).execute()
                                st.toast("🗑️ Registro eliminado exitosamente")
                                st.session_state[step_key] = 0
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al borrar: {e}")
                        if st.button("ABORTAR", key=f"c3_{cl['id']}", use_container_width=True):
                            st.session_state[step_key] = 0
                            st.rerun()

# --- CAMBIO DE SECCIÓN (FUERA DEL BUCLE) ---
elif menu == "Cuentas por Pagar":
    st.header("🏧 Movimientos de Efectivo")
    
    res_p = conn.table("pagos").select("monto_pagado").eq("user_id", u_id).execute()
    res_g = conn.table("gastos").select("monto").eq("user_id", u_id).execute()
    
    total_pagos = sum([p['monto_pagado'] for p in res_p.data]) if res_p.data else 0
    total_gastos = sum([g['monto'] for g in res_g.data]) if res_g.data else 0
    
    st.metric("Total Recaudado", f"${total_pagos:,.2f}")


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
