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
import re
from st_supabase_connection import SupabaseConnection

# 1. CONFIGURACIÓN INICIAL Y CONEXIÓN
st.set_page_config(page_title="CobroYa Global", layout="wide", initial_sidebar_state="collapsed")
conn = st.connection("supabase", type=SupabaseConnection)

# Inicializar estados de sesión
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "login"

# --- LÓGICA DE CONTROL DE ACCESO (EL MURO) ---
if not st.session_state.authenticated:
    # 2. TU CSS RADICAL (Intacto y Completo)
    st.markdown("""
    <style>
        [data-testid="stHeader"], [data-testid="stSidebar"], footer {display: none !important;}
        
        .main .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            max-width: 100% !important;
        }

        [data-testid="stAppViewContainer"] {
            background: linear-gradient(90deg, #06102B 33%, #F8FAFC 33%);
            height: 100vh;
            width: 100vw;
            overflow: hidden;
        }

        .panel-info {
            width: 33vw;
            padding: 30px 60px;
            color: white;
            height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        @media (max-width: 768px) {
            [data-testid="stAppViewContainer"] {
                background: #F8FAFC !important; 
                overflow-y: auto !important;
                overflow-x: hidden !important;
                height: auto !important;
            }

            [data-testid="stHorizontalBlock"] {
                display: flex !important;
                flex-direction: column-reverse !important;
                align-items: center !important;
                gap: 0px !important;
            }

            [data-testid="column"] {
                width: 100% !important;
                flex: 1 1 100% !important;
                min-width: 100% !important;
                display: flex !important;
                justify-content: center !important;
            }

            [data-testid="column"] > div {
                width: 100% !important;
                max-width: 450px !important;
                margin: 0 auto !important;
            }

            .panel-info {
                width: 100vw !important;
                height: auto !important;
                background-color: #06102B !important; 
                padding: 50px 20px !important;
                margin-top: 60px !important;
            }

            .main .block-container {
                padding: 20px 10px !important;
            }
        }

        .google-btn {
            display: flex; align-items: center; justify-content: center; gap: 10px;
            width: 100%; border: 1px solid #E2E8F0; border-radius: 12px;
            height: 45px; margin-bottom: 15px; font-weight: 500; color: #334155;
            cursor: pointer;
        }
        
        .divider {
            display: flex; align-items: center; text-align: center; color: #94A3B8;
            font-size: 12px; margin: 15px 0;
        }
        .divider::before, .divider::after { content: ''; flex: 1; border-bottom: 1px solid #F1F5F9; }
        .divider:not(:empty)::before { margin-right: 15px; }
        .divider:not(:empty)::after { margin-left: 15px; }

        div[data-testid="stTextInput"] input {
            border-radius: 10px !important;
            border: 1px solid #E2E8F0 !important;
        }
        
        .stElementContainer {
            margin-bottom: -10px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 4. RENDERIZADO DE LA ESTRUCTURA
    c_izq, c_der = st.columns([1, 2.03])

    with c_izq:
        st.markdown(f"""
        <div class="panel-info">
            <div>
                <img src="https://dqwqrzbskjzxjgihqrzc.supabase.co/storage/v1/object/public/logo/IMG_4803-removebg-preview%20(1).png" width="180">
                <div style="margin-top: 40px;">
                    <h2 style="font-size: 28px; line-height: 1.2;">Tu plataforma inteligente<br>para gestionar cobros y clientes</h2>
                    <div style="margin-top: 30px; color: #CBD5E1; font-size: 15px; line-height: 1.8;">
                        <p>✔️ Rápido y seguro</p>
                        <p>✔️ Sin confirmaciones innecesarias</p>
                        <p>✔️ Acceso desde cualquier lugar</p>
                    </div>
                </div>
            </div>
            <div style="font-size: 12px; color: #64748B; padding-bottom: 20px;">
                © 2026 CobroYa. Todos los derechos reservados.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_der:
        st.markdown('<div style="margin-top: 30px;"></div>', unsafe_allow_html=True)
        _, center, _ = st.columns([1, 2.5, 1])
        
        with center:
            # --- VISTA: LOGIN ---
            if st.session_state.page == "login":
                st.markdown("""
                    <div style="text-align: center; margin-bottom: 15px;">
                        <img src="https://dqwqrzbskjzxjgihqrzc.supabase.co/storage/v1/object/public/logo/IMG_4803-removebg-preview%20(1).png" width="180">
                        <h3 style="margin-top: 15px; color: #0F172A; margin-bottom: 5px;">Bienvenido de vuelta</h3>
                        <p style="color: #64748B; font-size: 14px;">Inicia sesión para continuar</p>
                    </div>
                """, unsafe_allow_html=True)
                
                # --- ARREGLO DEL BOTÓN DE GOOGLE ---
                try:
                    res_google = conn.auth.sign_in_with_oauth({"provider": "google"})
                    google_url = res_google.url
                except Exception:
                    google_url = "#"

                st.markdown(f"""
                    <a href="{google_url}" target="_self" style="text-decoration: none;">
                        <div style="display: flex; justify-content: center; align-items: center; border: 1px solid #CBD5E1; border-radius: 8px; padding: 10px; background-color: white; cursor: pointer; transition: 0.3s;">
                            <img src="https://upload.wikimedia.org/wikipedia/commons/c/c1/Google_%22G%22_logo.svg" width="20" style="margin-right: 10px;">
                            <span style="color: #334155; font-weight: 500; font-family: sans-serif; font-size: 15px;">Continuar con Google</span>
                        </div>
                    </a>
                """, unsafe_allow_html=True)

                st.markdown('<div class="divider">o continúa con tu correo</div>', unsafe_allow_html=True)
                
                # Campos de entrada
                email = st.text_input("Correo electrónico", placeholder="ejemplo@correo.com", key="login_email")
                password = st.text_input("Contraseña", type="password", placeholder="Tu contraseña", key="login_pass")
                
                col_check, col_link = st.columns([1, 1])
                with col_check:
                    st.checkbox("Recordarme")
                with col_link:
                    if st.button("¿Olvidaste tu contraseña?", key="btn_forgot"):
                        st.session_state.page = "forgot"
                        st.rerun()
                
                # --- LÓGICA DE INICIO DE SESIÓN ---
                if st.button("Iniciar sesión", type="primary", use_container_width=True):
                    if email and password:
                        try:
                            res = conn.auth.sign_in_with_password({"email": email, "password": password})
                            if res and res.user:
                                st.session_state.user = res.user
                                st.session_state.authenticated = True
                                st.rerun()
                            else:
                                st.error("No se pudo obtener la sesión del usuario.")
                        except Exception as e:
                            st.error("Correo o contraseña incorrectos")
                    else:
                        st.warning("Por favor, completa todos los campos")
                
                st.markdown("<p style='text-align: center; margin-top: 15px; font-size: 14px; color: #64748B;'>¿No tienes cuenta?</p>", unsafe_allow_html=True)
                if st.button("Crear cuenta", use_container_width=True):
                    st.session_state.page = "signup"
                    st.rerun()

# --- VISTA: REGISTRO ---
            elif st.session_state.page == "signup":
                st.markdown("""
                    <div style="text-align: center; margin-bottom: 15px;">
                        <img src="https://dqwqrzbskjzxjgihqrzc.supabase.co/storage/v1/object/public/logo/IMG_4803-removebg-preview.png" width="180">
                        <h3 style="margin-top: 15px; color: #0F172A;">Crear cuenta en CobroYa</h3>
                    </div>
                """, unsafe_allow_html=True)

                reg_company = st.text_input("Nombre de la Empresa", placeholder="Nombre que aparecerá en facturas")
                reg_phone = st.text_input("Número de Teléfono", placeholder="Ej: 8090000000")
                reg_email = st.text_input("Correo electrónico", placeholder="correo@ejemplo.com")
                
                # --- NUEVO: CARGA DE LOGO EN EL REGISTRO ---
                st.markdown("<p style='font-size: 14px; color: #334155; font-weight: 600; margin-top: 15px; margin-bottom: 5px;'>Logo de tu Empresa (Opcional)</p>", unsafe_allow_html=True)
                logo_file_reg = st.file_uploader("Puedes subirlo ahora o configurarlo después", type=["png", "jpg", "jpeg"], key="logo_registro")
                
                st.markdown("<p style='font-size: 12px; color: #64748B; margin-top: 15px;'>La contraseña debe incluir letras y números obligatoriamente.</p>", unsafe_allow_html=True)
                reg_pass = st.text_input("Contraseña", type="password", key="reg_p1")
                reg_pass_conf = st.text_input("Confirmar Contraseña", type="password", key="reg_p2")
                
                if st.button("Registrarse", type="primary", use_container_width=True):
                    if reg_pass != reg_pass_conf:
                        st.error("❌ Las contraseñas no coinciden.")
                    elif not (re.search("[a-zA-Z]", reg_pass) and re.search("[0-9]", reg_pass)):
                        st.error("❌ La contraseña debe tener letras y números.")
                    elif not reg_company or not reg_phone or not reg_email:
                        st.error("❌ Por favor, llena los campos obligatorios (Empresa, Teléfono, Correo).")
                    else:
                        try:
                            # 1. Preparar el logo si el usuario lo subió
                            import base64
                            base64_logo_reg = None
                            if logo_file_reg:
                                bytes_data_reg = logo_file_reg.getvalue()
                                base64_logo_reg = base64.b64encode(bytes_data_reg).decode()

                            # 2. Crear la cuenta en el sistema Auth de Supabase
                            auth_response = conn.auth.sign_up({
                                "email": reg_email, 
                                "password": reg_pass,
                                "options": {
                                    "data": {
                                        "display_name": reg_company,
                                        "phone": reg_phone
                                    }
                                }
                            })

                            # 3. GUARDADO MAESTRO EN 'configuracion'
                            # Extraemos el ID del usuario recién creado para vincular la tabla
                            if auth_response and auth_response.user:
                                nuevo_u_id = auth_response.user.id
                                
                                payload_config = {
                                    "user_id": nuevo_u_id,
                                    "nombre_negocio": reg_company,
                                    "telefono": reg_phone,
                                    "logo_base64": base64_logo_reg,
                                    "estado_plan": "inactivo" # Bloqueo inicial automático
                                }
                                
                                # Insertamos los datos corporativos directamente
                                conn.table("configuracion").insert(payload_config).execute()

                            st.success("✅ ¡Cuenta creada con éxito! Todo tu perfil está listo. Ya puedes iniciar sesión.")
                            
                        except Exception as e:
                            # Capturamos errores específicos (ej. correo ya existe)
                            if "already registered" in str(e).lower():
                                st.error("❌ Este correo electrónico ya está registrado.")
                            else:
                                st.error(f"❌ Error al procesar el registro: {e}")

                if st.button("Volver al login", use_container_width=True):
                    st.session_state.page = "login"
                    st.rerun()

            # --- VISTA: OLVIDÓ CONTRASEÑA ---
            elif st.session_state.page == "forgot":
                st.markdown("""
                    <div style="text-align: center; margin-bottom: 15px;">
                        <img src="https://dqwqrzbskjzxjgihqrzc.supabase.co/storage/v1/object/public/logo/IMG_4803-removebg-preview.png" width="180">
                        <h3 style="margin-top: 15px; color: #0F172A;">Recuperar acceso</h3>
                    </div>
                """, unsafe_allow_html=True)
                reset_email = st.text_input("Ingresa tu correo", key="reset_email")
                if st.button("Enviar enlace", type="primary", use_container_width=True):
                    st.success("Enlace enviado al correo")
                if st.button("Volver", use_container_width=True):
                    st.session_state.page = "login"
                    st.rerun()

    # BLOQUEO DE FLUJO
    st.stop()

# --- SI PASA DE AQUÍ, EL USUARIO ESTÁ DENTRO ---
u_id = st.session_state.user.id

import urllib.parse
from datetime import datetime

# =====================================================================
# INICIO DEL SISTEMA DE PAYWALL Y CHECKOUT (WALL STREET EDITION)
# =====================================================================

# 1. VERIFICACIÓN EN BASE DE DATOS
if "estado_suscripcion" not in st.session_state:
    try:
        res_sub = conn.table("configuracion").select("estado_plan, fecha_vencimiento, nombre_negocio, rnc").eq("user_id", u_id).execute()
        
        if res_sub.data:
            datos_plan = res_sub.data[0]
            estado = datos_plan.get("estado_plan", "inactivo")
            fecha_v = datos_plan.get("fecha_vencimiento")
            
            st.session_state["ws_nombre"] = datos_plan.get("nombre_negocio", st.session_state.user.user_metadata.get("display_name", "Usuario"))
            st.session_state["ws_cedula"] = datos_plan.get("rnc", "No especificada")
            
            if estado == "activo" and fecha_v:
                fecha_vencimiento = datetime.strptime(fecha_v, "%Y-%m-%d").date()
                if datetime.now().date() <= fecha_vencimiento:
                    st.session_state["estado_suscripcion"] = "valido"
                else:
                    st.session_state["estado_suscripcion"] = "vencido"
            else:
                st.session_state["estado_suscripcion"] = "inactivo"
        else:
            st.session_state["estado_suscripcion"] = "inactivo"
            st.session_state["ws_nombre"] = st.session_state.user.user_metadata.get("display_name", "Usuario Nuevo")
            st.session_state["ws_cedula"] = "No registrada"
            
    except Exception as e:
        st.error(f"Error crítico en base de datos: {e}")
        st.stop()

# ESTADO DE LA PASARELA
if "plan_seleccionado" not in st.session_state:
    st.session_state.plan_seleccionado = None

# --- SI EL USUARIO NO TIENE PLAN ACTIVO ---
if st.session_state.get("estado_suscripcion") != "valido":
    
    # CSS MAESTRO PARA REPLICAR LA IMAGEN EXACTA
    st.markdown("""
    <style>
        .pricing-header { text-align: center; margin-bottom: 30px; font-family: sans-serif; }
        .pricing-header img { width: 180px; margin-bottom: 10px; }
        .pricing-header h1 { font-size: 28px; font-weight: 800; color: #0f172a; margin-bottom: 5px; }
        .pricing-header p { font-size: 15px; color: #64748b; margin-top: 0; }
        
        .card-box {
            background: white; border: 1px solid #e2e8f0; border-radius: 12px;
            padding: 24px; text-align: center; font-family: sans-serif; height: 100%;
        }
        .card-pro { border: 2px solid #2563eb; position: relative; }
        .badge {
            background: #2563eb; color: white; font-size: 11px; font-weight: bold;
            padding: 4px 12px; border-radius: 20px; position: absolute;
            top: -12px; left: 50%; transform: translateX(-50%); letter-spacing: 1px;
        }
        .icon { font-size: 24px; color: #475569; margin-bottom: 10px; }
        .title { font-size: 18px; font-weight: bold; color: #0f172a; margin: 0; }
        .subtitle { font-size: 13px; color: #64748b; margin-bottom: 15px; }
        .price { font-size: 32px; font-weight: 900; color: #0f172a; margin: 0; }
        .price span { font-size: 14px; font-weight: normal; color: #64748b; }
        .annual { font-size: 12px; color: #64748b; margin-bottom: 20px; }
        .annual span { color: #16a34a; font-weight: 600; }
        
        .features { list-style: none; padding: 0; margin: 0 0 20px 0; text-align: left; }
        .features li { font-size: 13px; color: #334155; margin-bottom: 10px; border-bottom: 1px solid #f1f5f9; padding-bottom: 5px; }
        .features li::before { content: '✓'; color: #0f172a; font-weight: bold; margin-right: 8px; }
        
        .ideal { font-size: 11px; color: #64748b; padding: 10px; background: #f8fafc; border-radius: 6px; margin-bottom: 15px; min-height: 60px;}
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
    # CONFIGURACIÓN: SISTEMA DE PRECIOS REGIONALES (FASE 1)
    # ---------------------------------------------------------
    PLANES_CONFIG = {
        "Free": {"nombre": "Free"},
        "Starter": {"nombre": "Starter"},
        "Pro": {"nombre": "Pro"},
        "Enterprise": {"nombre": "Enterprise"}
    }

    REGION_PRICING = {
        "RD": {"moneda": "RD$", "codigo": "DOP", "precios": {"Free": 0, "Starter": 799, "Pro": 2499, "Enterprise": 7999, "Extra": 149}},
        "LATAM_STD": {"moneda": "US$", "codigo": "USD", "precios": {"Free": 0, "Starter": 16, "Pro": 39, "Enterprise": 129, "Extra": 3}},
        "LATAM_PREM": {"moneda": "US$", "codigo": "USD", "precios": {"Free": 0, "Starter": 19, "Pro": 45, "Enterprise": 139, "Extra": 4}},
        "USA": {"moneda": "US$", "codigo": "USD", "precios": {"Free": 0, "Starter": 24, "Pro": 59, "Enterprise": 179, "Extra": 5}}
    }
    
    # Simulación de detección de región (Para la Fase 2, esto vendrá de geolocalización o billing country)
    region_detectada = "RD" 
    
    moneda_local = REGION_PRICING[region_detectada]["moneda"]
    codigo_moneda = REGION_PRICING[region_detectada]["codigo"]
    precios_activos = REGION_PRICING[region_detectada]["precios"]

    # ---------------------------------------------------------
    # VISTA 1: APARADOR DE PLANES (REFACTORIZADO SaaS)
    # ---------------------------------------------------------
    if st.session_state.get('plan_seleccionado') is None:
        
        st.markdown("""
        <div class="pricing-header" style="text-align: center; margin-bottom: 2rem;">
            <img src="https://dqwqrzbskjzxjgihqrzc.supabase.co/storage/v1/object/public/logo/IMG_4803-removebg-preview%20(1).png" width="150" alt="CobroYa Logo">
            <h1 style="color: #0f172a;">Planes diseñados para escalar tu negocio</h1>
            <p style="color: #475569;">Transparencia total. Límites claros. Cancela en cualquier momento.</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class="card-box" style="padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; height: 100%; background: white;">
                <div class="icon" style="margin-bottom: 10px;">
                    <svg width="32" height="32" fill="none" stroke="#64748b" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
                </div>
                <p class="title" style="font-size: 18px; font-weight: bold; margin: 5px 0; color: #0f172a;">Free</p>
                <p class="subtitle" style="color: #64748b; font-size: 13px;">Exploración Inteligente</p>
                <p class="price" style="font-size: 24px; font-weight: bold; color: #0f172a;">Gratis</p>
                <p class="annual" style="font-size: 11px; color: #94a3b8;">Uso vitalicio sujeto a límites</p>
                <hr style="border-top: 1px solid #f1f5f9; margin: 12px 0;">
                <ul class="features" style="list-style-type: none; padding: 0; font-size: 13px; color: #334155; line-height: 1.6;">
                    <li>✓ Límite estricto de 5 clientes</li>
                    <li>✓ Máximo 10 préstamos activos</li>
                    <li>✓ Tabla de amortización estándar</li>
                    <li>✓ Gestión operativa básica</li>
                    <li>✓ PDF (Incluye marca de agua)</li>
                    <li style="color:#94a3b8; margin-top: 8px;">✕ Dashboards y Reportes <br><span style="font-size:10px;">(Requiere plan superior)</span></li>
                    <li style="color:#94a3b8; margin-top: 8px;">✕ Módulos IA y WhatsApp <br><span style="font-size:10px;">(Requiere plan superior)</span></li>
                    <li style="color:#94a3b8; margin-top: 8px;">✕ Exportación de datos <br><span style="font-size:10px;">(Requiere plan superior)</span></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Usar Gratis", key="btn_f", use_container_width=True):
                st.session_state.plan_seleccionado = {"nombre": "Free", "precio": precios_activos["Free"]}
                st.rerun()

        with col2:
            st.markdown(f"""
            <div class="card-box" style="padding: 20px; border: 1px solid #e2e8f0; border-radius: 12px; height: 100%; background: white;">
                <div class="icon" style="margin-bottom: 10px;">
                    <svg width="32" height="32" fill="none" stroke="#0f172a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                </div>
                <p class="title" style="font-size: 18px; font-weight: bold; margin: 5px 0; color: #0f172a;">Starter</p>
                <p class="subtitle" style="color: #64748b; font-size: 13px;">Prestamista Individual</p>
                <p class="price" style="font-size: 24px; font-weight: bold; color: #0f172a;">{moneda_local}{precios_activos['Starter']}<span style="font-size: 12px; color: #64748b;">/mes</span></p>
                <p class="annual" style="font-size: 11px; color: #94a3b8;">Facturación en {codigo_moneda}</p>
                <hr style="border-top: 1px solid #f1f5f9; margin: 12px 0;">
                <ul class="features" style="list-style-type: none; padding: 0; font-size: 13px; color: #334155; line-height: 1.6;">
                    <li>✓ Capacidad para 100 clientes</li>
                    <li>✓ Límite de 250 cuentas activas</li>
                    <li>✓ Acceso a Dashboard inicial</li>
                    <li>✓ Gestión de cobros integral</li>
                    <li>✓ Generación PDF sin marcas</li>
                    <li>✓ Integración WhatsApp (Básica)</li>
                    <li>✓ GPS de ubicación básica</li>
                    <li>✓ Motor IA (100 peticiones/mes)</li>
                    <li>✓ Exportación de historial individual</li>
                    <li>✓ Hasta 2 inicios de sesión simultáneos</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Comenzar", key="btn_s", use_container_width=True):
                st.session_state.plan_seleccionado = {"nombre": "Starter", "precio": precios_activos["Starter"]}
                st.rerun()

        with col3:
            st.markdown(f"""
            <div class="card-box card-pro" style="padding: 20px; border: 2px solid #2563eb; border-radius: 12px; height: 100%; position: relative; background-color: #f8fafc;">
                <div class="badge" style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #2563eb; color: white; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: bold; letter-spacing: 1px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">RECOMENDADO</div>
                <div class="icon" style="margin-bottom: 10px;">
                    <svg width="32" height="32" fill="none" stroke="#2563eb" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
                </div>
                <p class="title" style="font-size: 18px; font-weight: bold; margin: 5px 0; color: #0f172a;">Pro</p>
                <p class="subtitle" style="color: #64748b; font-size: 13px;">Operación Comercial</p>
                <p class="price" style="font-size: 24px; font-weight: bold; color: #2563eb;">{moneda_local}{precios_activos['Pro']}<span style="font-size: 12px; color: #64748b;">/mes</span></p>
                <p class="annual" style="font-size: 11px; color: #94a3b8;">Facturación en {codigo_moneda}</p>
                <hr style="border-top: 1px solid #e2e8f0; margin: 12px 0;">
                <ul class="features" style="list-style-type: none; padding: 0; font-size: 13px; color: #334155; line-height: 1.6;">
                    <li>✓ Capacidad para 1,000 clientes</li>
                    <li>✓ Límite de 2,500 cuentas activas</li>
                    <li>✓ Acceso a todos los Dashboards</li>
                    <li>✓ GPS con planificador de rutas</li>
                    <li>✓ Códigos QR en facturación</li>
                    <li>✓ Motor IA Avanzado (300 peticiones)</li>
                    <li>✓ Exportación parcial y reportes</li>
                    <li>✓ Soporte técnico prioritario</li>
                    <li>✓ Asesoría operativa semanal</li>
                    <li>✓ Hasta 5 inicios de sesión simultáneos</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Comenzar ahora", key="btn_p", type="primary", use_container_width=True):
                st.session_state.plan_seleccionado = {"nombre": "Pro", "precio": precios_activos["Pro"]}
                st.rerun()

        with col4:
            # Aquí cambiamos el diseño: ya no es oscuro, es limpio pero con un borde distintivo (gris oscuro) para darle presencia corporativa
            st.markdown(f"""
            <div class="card-box" style="padding: 20px; border: 1px solid #475569; border-radius: 12px; height: 100%; background: #ffffff;">
                <div class="icon" style="margin-bottom: 10px;">
                    <svg width="32" height="32" fill="none" stroke="#0f172a" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="20" rx="2" ry="2"></rect><path d="M9 22v-4h6v4"></path><path d="M8 6h.01"></path><path d="M16 6h.01"></path><path d="M12 6h.01"></path><path d="M12 10h.01"></path><path d="M12 14h.01"></path><path d="M16 10h.01"></path><path d="M16 14h.01"></path><path d="M8 10h.01"></path><path d="M8 14h.01"></path></svg>
                </div>
                <p class="title" style="font-size: 18px; font-weight: bold; margin: 5px 0; color: #0f172a;">Enterprise</p>
                <p class="subtitle" style="color: #64748b; font-size: 13px;">Infraestructura a Escala</p>
                <p class="price" style="font-size: 24px; font-weight: bold; color: #0f172a;">{moneda_local}{precios_activos['Enterprise']}<span style="font-size: 12px; color: #64748b;">/mes</span></p>
                <p class="annual" style="font-size: 11px; color: #94a3b8;">Facturación en {codigo_moneda}</p>
                <hr style="border-top: 1px solid #e2e8f0; margin: 12px 0;">
                <ul class="features" style="list-style-type: none; padding: 0; font-size: 13px; color: #334155; line-height: 1.6;">
                    <li>✓ Capacidad ampliada (10,000 clientes)</li>
                    <li>✓ Infraestructura de alta disponibilidad</li>
                    <li>✓ Dashboards analíticos completos</li>
                    <li>✓ Motor IA (Sujeto a políticas de uso)</li>
                    <li>✓ Exportación total de bases de datos</li>
                    <li>✓ Protocolo de Backup empresarial</li>
                    <li>✓ Asistencia en migración de datos</li>
                    <li>✓ Soporte técnico dedicado 24/7</li>
                    <li>✓ Consultoría estratégica incluida</li>
                    <li>✓ Hasta 20 inicios de sesión simultáneos</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Seleccionar", key="btn_e", use_container_width=True):
                st.session_state.plan_seleccionado = {"nombre": "Enterprise", "precio": precios_activos["Enterprise"]}
                st.rerun()

    # ---------------------------------------------------------
    # VISTA 2: LA PASARELA (CHECKOUT / FACTURA MULTIMONEDA)
    # ---------------------------------------------------------
    else:
        plan_actual = st.session_state.plan_seleccionado
        
        # 1. ACTUALIZAR SUPABASE INMEDIATAMENTE (Intención de compra)
        try:
            conn.table("configuracion").update({
                "tipo_plan": plan_actual["nombre"],
                "estado_plan": "pendiente" # Se queda pendiente de validación administrativa
            }).eq("user_id", u_id).execute()
        except Exception as e:
            st.warning("No se pudo pre-registrar el estado del plan en la base de datos.")

        # 2. DISEÑO DE LA FACTURA
        st.markdown("<h2 style='text-align:center; color:#0f172a; margin-bottom: 30px;'>Resumen de Facturación</h2>", unsafe_allow_html=True)
        
        _, col_center, _ = st.columns([1, 2, 1])
        with col_center:
            es_gratis = (plan_actual["precio"] == 0)
            precio_display = "Gratis (Exento)" if es_gratis else f"{moneda_local}{plan_actual['precio']:,.2f} {codigo_moneda}"

            st.markdown(f"""
            <div style="background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 25px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 20px;">
                <h4 style="margin-top:0; color:#0f172a; font-weight: 600;">Detalle de la Orden</h4>
                <hr style="margin: 15px 0; border-top: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; font-size: 15px; margin-bottom: 12px; color:#334155;">
                    <span>Suscripción:</span>
                    <strong>Plan {plan_actual["nombre"]}</strong>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 15px; margin-bottom: 12px; color:#334155;">
                    <span>Región de facturación:</span>
                    <span><strong>{region_detectada}</strong></span>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 15px; margin-bottom: 12px; color:#334155;">
                    <span>Ciclo:</span>
                    <span>Mensual (Renovación automática)</span>
                </div>
                <hr style="margin: 15px 0; border-top: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; font-size: 22px; color: #0f172a; font-weight: bold; align-items: center;">
                    <span>Total a procesar:</span>
                    <span style="color: #2563eb;">{precio_display}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if not es_gratis:
                st.markdown("""
                <div style="background: #f8fafc; border-left: 4px solid #2563eb; padding: 15px; border-radius: 4px; margin-bottom: 20px; border-right: 1px solid #e2e8f0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0;">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <svg width="20" height="20" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 8px;"><rect x="2" y="5" width="20" height="14" rx="2" ry="2"></rect><line x1="2" y1="10" x2="22" y2="10"></line></svg>
                        <h5 style="margin: 0; color:#0f172a;">Instrucciones para Transferencia</h5>
                    </div>
                    <p style="font-size: 14px; color:#475569; margin-bottom:8px;">Por favor, transfiere el monto exacto a una de las siguientes cuentas institucionales:</p>
                    <ul style="font-size: 14px; color:#0f172a; padding-left: 20px; line-height: 1.6; margin-bottom: 0;">
                        <li><strong>Banco Popular:</strong> 123456789 (Titular: Lixander García)</li>
                        <li><strong>Banreservas:</strong> 987654321 (Titular: Lixander García)</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            # CONFIGURACIÓN WHATSAPP DINÁMICA
            import urllib.parse
            numero_whatsapp = "18290000000" # AQUI VA TU NUMERO REAL
            nombre_ws = st.session_state.get("ws_nombre", "Usuario")
            cedula_ws = st.session_state.get("ws_cedula", "N/A")
            
            if es_gratis:
                mensaje = f"Hola equipo CobroYa. Solicito la habilitación de mi cuenta en el nivel gratuito.\n\n📊 *Plan:* {plan_actual['nombre']}\n👤 *Titular:* {nombre_ws}\n🔑 *Identificador:* {str(u_id)}\n\nQuedo a la espera de confirmación."
                texto_boton = "Solicitar Activación"
            else:
                mensaje = f"Hola equipo CobroYa. Adjunto el comprobante de pago para la activación de mi suscripción.\n\n📊 *Suscripción:* {plan_actual['nombre']}\n🌍 *Zona:* {region_detectada}\n💵 *Importe:* {precio_display}\n👤 *Titular:* {nombre_ws}\n🪪 *Documento:* {cedula_ws}\n🔑 *Identificador:* {str(u_id)}\n\n*Comprobante adjunto:*"
                texto_boton = "Enviar Comprobante Oficial"

            link_wa = f"https://wa.me/{numero_whatsapp}?text={urllib.parse.quote(mensaje)}"

            st.link_button(texto_boton, link_wa, type="primary", use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("← Modificar selección de plan", use_container_width=True):
                st.session_state.plan_seleccionado = None
                st.rerun()

    # BLOQUEO MAESTRO: Detiene la ejecución aquí hasta que el estado en BD cambie de 'pendiente' a 'activo'
    st.stop()

# =====================================================================
# FIN DEL SISTEMA DE PAYWALL
# =====================================================================

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


# --- 0. INICIALIZACIÓN (Evita errores de variable no definida) ---
if "menu_principal" not in st.session_state:
    st.session_state["menu_principal"] = "Panel de Control"

# --- 1. CARGA DE DATOS SUPABASE (Lógica Intacta) ---
if "user" in st.session_state and st.session_state.user:
    if "datos_validados" not in st.session_state:
        try:
            res = conn.table("configuracion").select("*").eq("user_id", st.session_state.user.id).execute()
            if res.data:
                conf = res.data[0]
                st.session_state["nombre_negocio"] = conf.get("nombre_negocio", "Mi Negocio")
                st.session_state["rnc"] = conf.get("rnc", "---")
                st.session_state["telefono_negocio"] = conf.get("telefono", "---")
                st.session_state["direccion_negocio"] = conf.get("direccion", "---")
                st.session_state["mi_logo"] = conf.get("logo_base64")
                st.session_state["datos_validados"] = True
                st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# --- 2. SIDEBAR (DISEÑO BLOQUEADO A 200PX) ---
with st.sidebar:
    import base64
    
    URL_LOGO_COBROYA = "https://dqwqrzbskjzxjgihqrzc.supabase.co/storage/v1/object/public/logo/IMG_4803-removebg-preview%20(1).png" 

    # Variables de sesión
    biz_name = st.session_state.get("nombre_negocio", "MI NEGOCIO").upper()
    biz_rnc  = st.session_state.get("rnc", "---")
    biz_dir  = st.session_state.get("direccion_negocio", "---")
    biz_tel  = st.session_state.get("telefono_negocio", "---")
    logo_b64 = st.session_state.get("mi_logo")
    u_email  = st.session_state.user.email if st.session_state.get("user") else "Sesión Activa"

# --- 1. SOLUCIÓN AL NAMEERROR: Definición previa de src_logo ---
    try:
        if 'logo_b64' in locals() and logo_b64:
            img_data = logo_b64.split(",")[1] if "," in str(logo_b64) else logo_b64
            src_logo = f"data:image/png;base64,{img_data}"
        else:
            src_logo = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
    except Exception:
        src_logo = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"

# --- 1. CSS: Estética Minimalista y Profesional ---
    st.markdown(f"""
        <style>
            /* EXPANSIÓN Y SIDEBAR */
            [data-testid="stSidebar"][aria-expanded="true"] {{
                min-width: 300px !important;
                max-width: 300px !important;
                background-color: #FBFBFD !important;
            }}
            [data-testid="stSidebar"][aria-expanded="false"] {{
                min-width: 0px !important;
                max-width: 0px !important;
                width: 0px !important;
            }}

            /* BOTÓN DE MENÚ */
            [data-testid="stSidebarHeader"] {{
                padding: 0px !important;
                background-color: transparent !important;
            }}
            button[data-testid="stSidebarCollapseButton"] {{
                background-color: #1D1D1F !important;
                color: white !important;
                border-radius: 8px !important;
                margin: 10px !important;
                z-index: 100000 !important;
            }}

            /* LOGO AL TECHO */
            [data-testid="stSidebarUserContent"] {{
                padding-top: 0px !important;
                margin-top: -50px !important; 
            }}

            .client-brand-card {{
                text-align: center; 
                padding: 15px; 
                background: white;
                border-bottom: 1px solid #F2F2F7;
                margin-bottom: 20px;
            }}
            
            .client-logo-img {{
                max-width: 90%;
                height: 55px;
                object-fit: contain;
            }}

            /* NAVEGACIÓN */
            div[role="radiogroup"] {{
                gap: 12px !important;
                padding-left: 10px !important;
            }}
            div[role="radio"] p {{ 
                font-size: 14px !important; 
                color: #1D1D1F !important;
                font-weight: 400;
                padding: 6px 0 !important;
            }}

            /* FOOTER PROFESIONAL (Minimalista) */
            .absolute-footer {{
                margin-top: 40px !important;
                padding: 20px 0px 10px 0px !important;
                border-top: 1px solid #F2F2F7;
                text-align: center;
                display: flex;
                flex-direction: column;
                align-items: center;
                width: 100%;
            }}

            .powered-by {{
                font-size: 9px !important;
                color: #A1A1A6;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                font-weight: 500;
                margin-bottom: 10px;
            }}

            .footer-logo-img {{
                width: 100px; /* Tamaño equilibrado para verse serio */
                height: auto;
                opacity: 0.8;
            }}

            [data-testid="stAppViewBlockContainer"] {{
                max-width: 100% !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    # --- 2. CONTENIDO SUPERIOR: LOGO Y MARCA ---
    st.sidebar.markdown(f"""
        <div class="client-brand-card">
            <img src="{src_logo}" class="client-logo-img">
            <div style="font-family: sans-serif; margin-top: 10px;">
                <b style="font-size:14px; color:#1D1D1F;">{biz_name}</b>
                <div style="font-size:10px; color:#86868B; margin-top:5px;">
                    <p style="margin:0;">RNC: {biz_rnc} | 📞 {biz_tel}</p>
                    <p style='color:#1D1D1F; font-weight:600; margin-top:3px;'>{u_email}</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- 3. NAVEGACIÓN (Corregida para 1 solo clic) ---
    opciones = ["Panel de Control", "Gestión de Cobros", "👥 Todos mis Clientes", "Nueva Cuenta por Cobrar", "Cuentas por Pagar", "IA Predictiva", "Configuración"]
    
    mapeo_visual = {
        "Panel de Control": "🏠 Panel de Control",
        "Gestión de Cobros": "💰 Gestión de Cobros",
        "👥 Todos mis Clientes": "👥 Todos mis Clientes",
        "Nueva Cuenta por Cobrar": "➕ Nueva Cuenta por Cobrar",
        "Cuentas por Pagar": "📉 Cuentas por Pagar",
        "IA Predictiva": "🧠 IA Predictiva",
        "Configuración": "⚙️ Configuración"
    }

    # Al usar key="menu_principal", el radio lee y escribe 
    # directamente en st.session_state["menu_principal"]
    menu = st.sidebar.radio(
        "NAV",
        opciones,
        key="menu_principal",
        format_func=lambda x: mapeo_visual.get(x, x),
        label_visibility="collapsed"
    )

    # --- 4. FOOTER: DISTRIBUCIÓN DE EMPRESA SERIA ---
    st.sidebar.markdown(f"""
        <div class="absolute-footer">
            <span class="powered-by">Powered by Lixander García</span>
            <img src="https://dqwqrzbskjzxjgihqrzc.supabase.co/storage/v1/object/public/logo/IMG_4803-removebg-preview%20(1).png" 
                 class="footer-logo-img" 
                 onerror="this.style.display='none'">
        </div>
    """, unsafe_allow_html=True)
    
# --- 5. MÓDULOS DE NEGOCIO (LÓGICA DE PRESTAMISTA REAL) ---
if menu == "Panel de Control":
    from datetime import datetime, timedelta

    st.title("💼 Business Intelligence Dashboard")
    
    # --- 1. MEMORIA DEL FILTRO (SESSION STATE) ---
    # Si es la primera vez que entra, por defecto ponemos "Todo el tiempo"
    if 'filtro_bi_default' not in st.session_state:
        st.session_state.filtro_bi_default = "Todo el tiempo"

    # --- 2. BOTÓN DE FILTRADO CON MEMORIA ---
    with st.popover(f"🔍 Filtro: {st.session_state.filtro_bi_default}"):
        opciones = ["Hoy", "Últimos 7 días", "Este mes", "Últimos 3 meses", "Último año", "Todo el tiempo"]
        
        # El index se calcula buscando dónde está guardado nuestro filtro actual
        idx_actual = opciones.index(st.session_state.filtro_bi_default)
        
        seleccion = st.radio(
            "Selecciona el rango para mantener fijado:",
            opciones,
            index=idx_actual
        )
        
        # Si el usuario cambia la selección, actualizamos la memoria y refrescamos
        if seleccion != st.session_state.filtro_bi_default:
            st.session_state.filtro_bi_default = seleccion
            st.rerun()

    # Usamos la variable guardada para toda la lógica siguiente
    filtro_tiempo = st.session_state.filtro_bi_default

    # --- 3. LÓGICA DE FECHAS (SIN FALLOS) ---
    hoy = datetime.now()
    fecha_inicio = None
    if filtro_tiempo == "Hoy": fecha_inicio = hoy.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filtro_tiempo == "Últimos 7 días": fecha_inicio = hoy - timedelta(days=7)
    elif filtro_tiempo == "Este mes": fecha_inicio = hoy.replace(day=1, hour=0, minute=0, second=0)
    elif filtro_tiempo == "Últimos 3 meses": fecha_inicio = hoy - timedelta(days=90)
    elif filtro_tiempo == "Último año": fecha_inicio = hoy - timedelta(days=365)

    # --- 4. EXTRACCIÓN DE DATOS (TUS QUERIES ORIGINALES) ---
    q_c = conn.table("cuentas").select("balance_pendiente, monto_inicial, estado, fecha_creacion, cliente:clientes(nombre)").eq("user_id", u_id)
    q_p = conn.table("pagos").select("monto_pagado, fecha_pago").eq("user_id", u_id)
    q_g_pagados = conn.table("gastos").select("monto, fecha_gasto").eq("user_id", u_id).eq("estado", "Pagado").eq("visible_usuario", True)
    q_g_pendientes = conn.table("gastos").select("monto, fecha_gasto").eq("user_id", u_id).eq("estado", "Pendiente").eq("visible_usuario", True)

    if fecha_inicio:
        f_iso = fecha_inicio.isoformat()
        q_c = q_c.gte("fecha_creacion", f_iso)
        q_p = q_p.gte("fecha_pago", f_iso)
        q_g_pagados = q_g_pagados.gte("fecha_gasto", f_iso)
        q_g_pendientes = q_g_pendientes.gte("fecha_gasto", f_iso)

    res_c = q_c.execute()
    res_p = q_p.execute()
    res_g_pagados = q_g_pagados.execute()
    res_g_pendientes = q_g_pendientes.execute()

    # --- 5. CÁLCULOS ---
    total_cobrado = sum([p['monto_pagado'] for p in res_p.data]) if res_p.data else 0
    total_gastado_real = sum([g['monto'] for g in res_g_pagados.data]) if res_g_pagados.data else 0
    total_compromisos = sum([g['monto'] for g in res_g_pendientes.data]) if res_g_pendientes.data else 0
    capital_en_calle = sum([c['balance_pendiente'] for c in res_c.data if c['estado'] == 'Activo']) if res_c.data else 0
    caja_actual = total_cobrado - total_gastado_real

    # --- 6. UI DE TARJETAS ---
    st.markdown("""
        <style>
            .metric-card {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 15px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
                text-align: center;
                border: 1px solid #f0f0f5;
                margin-bottom: 10px;
            }
            .metric-card small { color: #8e8e93; font-weight: 600; text-transform: uppercase; }
            .metric-card h2 { margin-top: 10px; font-size: 26px; }
        </style>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='metric-card'><small>💰 EN LA CALLE</small><h2 style='color:#007AFF;'>RD$ {capital_en_calle:,.0f}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='metric-card'><small>🏦  RECIBIDO EN CAJA</small><h2 style='color:#34C759;'>RD$ {caja_actual:,.0f}</h2></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='metric-card'><small>📉 GASTOS</small><h2 style='color:#FF3B30;'>RD$ {total_gastado_real:,.0f}</h2></div>", unsafe_allow_html=True)

    st.markdown(f"<p style='text-align:right; color:gray; font-size:12px;'>Vista fijada: {filtro_tiempo}</p>", unsafe_allow_html=True)
    st.markdown("---")
    

    # --- 5. GRÁFICOS (PROTECCIÓN CONTRA ERRORES DE FECHA) ---
    import pandas as pd
    import plotly.express as px

    col_l, col_r = st.columns([1.2, 0.8])

    with col_l:
        st.subheader("🏆 Top 5 Deudores")
        if res_c.data:
            df_deudores = pd.DataFrame([{'C': c['cliente']['nombre'], 'D': c['balance_pendiente']} for c in res_c.data if c['estado'] == 'Activo'])
            if not df_deudores.empty:
                df_top = df_deudores.groupby('C').sum().sort_values('D', ascending=False).head(5).reset_index()
                fig_top = px.bar(df_top, x='D', y='C', orientation='h', color='D', color_continuous_scale='Blues', text_auto=',.0f')
                fig_top.update_layout(showlegend=False, height=350, margin=dict(l=0, r=10, t=20, b=0))
                st.plotly_chart(fig_top, use_container_width=True)

    with col_r:
        st.subheader("📊 Recuperación")
        m_inicial = sum([c['monto_inicial'] for c in res_c.data]) if res_c.data else 0
        recup = max(0, m_inicial - capital_en_calle)
        df_pie = pd.DataFrame({'T': ['Recuperado', 'Pendiente'], 'M': [recup, capital_en_calle]})
        fig_pie = px.pie(df_pie, values='M', names='T', hole=0.6, color_discrete_sequence=['#34C759', '#007AFF'])
        fig_pie.update_layout(margin=dict(l=0, r=0, t=20, b=0), height=350)
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- 6. ANÁLISIS DE FLUJO (Aquí estaba el ValueError) ---
    st.markdown("---")
    st.subheader("📈 Flujo de Recaudación Diario")
    
    if res_p.data and len(res_p.data) > 0:
        df_p = pd.DataFrame(res_p.data)
        
        # PASO CRÍTICO: Conversión segura
        df_p['fecha_pago'] = pd.to_datetime(df_p['fecha_pago'], errors='coerce', utc=True)
        
        # Eliminamos nulos producidos por la conversión o la DB
        df_p = df_p.dropna(subset=['fecha_pago'])
        
        if not df_p.empty:
            # Agrupación por día
            df_hist = df_p.set_index('fecha_pago').resample('D')['monto_pagado'].sum().reset_index()
            
            fig_area = px.area(df_hist, x='fecha_pago', y='monto_pagado')
            fig_area.update_traces(line_color='#007AFF', fillcolor='rgba(0, 122, 255, 0.1)')
            fig_area.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0), xaxis_title="", yaxis_title="RD$")
            st.plotly_chart(fig_area, use_container_width=True)
        else:
            st.info("No hay fechas válidas para mostrar el historial.")
    else:
        st.info("Aún no hay registros de cobros.")
            
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

# --- 4. DETECTOR MAESTRO DE RECIBOS (FUERA DE TODO BUCLE) ---
    # Esto debe ejecutarse antes que cualquier filtro para que no importe si la cuenta se saldó
    for key in list(st.session_state.keys()):
        if key.startswith("recibo_"):
            id_para_recibo = key.replace("recibo_", "")
            # Buscamos la data directamente en la tabla para asegurar que tenemos el nombre
            # sin importar si está saldada o no
            res_recibo = conn.table("cuentas").select("*, clientes(nombre, telefono)").eq("id", id_para_recibo).single().execute()
            
            if res_recibo.data:
                item_recibo = res_recibo.data
                item_recibo['aux_nombre'] = item_recibo.get('clientes', {}).get('nombre', 'Cliente')
                
                # Lanzamos la modal y limpiamos el estado
                mostrar_recibo_modal(item_recibo, st.session_state[key], u_id)
                del st.session_state[key]
                # No hacemos rerun aquí, dejamos que la modal se procese

# --- 5. CONTROLES SUPERIORES (Buscador + Filtro Pro) ---
    col_search, col_filter, col_view = st.columns([2, 1.2, 0.8])
    
    with col_search:
        # Buscador principal
        search_term = st.text_input("🔍 Buscar cliente...", placeholder="Nombre, Cédula o Teléfono...", label_visibility="collapsed").lower()
    
    with col_filter:
        # Filtro de tiempo minimalista - AGREGADA OPCIÓN "AL DÍA"
        opcion_filtro = st.selectbox(
            "Filtrar cobros",
            options=["📋 Todos", "🔥 Urgentes", "📅 Cobrarles Hoy", "⏳ Próx. 7 Días", "🚨 Atrasados", "🟢 Al Día"],
            label_visibility="collapsed"
        )
    
    with col_view:
        # Toggle de estado
        modo_analisis = st.toggle("📈 Análisis", help="Ver cuentas saldadas")

    # --- 6. CONSULTA DE DATOS PARA LA LISTA ---
    query = conn.table("cuentas").select("*, clientes(nombre, telefono, cedula)").eq("user_id", u_id)
    if modo_analisis:
        query = query.lte("balance_pendiente", 0)
    else:
        query = query.gt("balance_pendiente", 0)
        
    res = query.execute()
    
    if res.data:
        datos_procesados = []
        for c in res.data:
            cliente_info = c.get('clientes', {})
            nombre = cliente_info.get('nombre', 'Cliente')
            cedula = cliente_info.get('cedula', '')
            telefono = cliente_info.get('telefono', '')
            
            # 1. Calculamos atraso primero para poder filtrar
            txt_atraso_base, dias_num = calcular_atraso_dinamico(c.get('proximo_pago'))
            
            # 2. LÓGICA DEL FILTRO DE FECHA ESTRICTA (CORREGIDA PARA PRÓXIMOS 7 DÍAS)
            pasa_fecha = False
            if opcion_filtro == "📋 Todos":
                pasa_fecha = True
            elif opcion_filtro == "🔥 Urgentes":
                pasa_fecha = (dias_num >= 0) # Solo hoy y atrasados
            elif opcion_filtro == "📅 Cobrarles Hoy":
                pasa_fecha = (dias_num == 0)
            elif opcion_filtro == "⏳ Próx. 7 Días":
                # Filtra desde hoy (0) hasta 7 días en el futuro (-7)
                pasa_fecha = (-7 <= dias_num <= 0)
            elif opcion_filtro == "🚨 Atrasados":
                pasa_fecha = (dias_num > 0)
            elif opcion_filtro == "🟢 Al Día":
                pasa_fecha = (dias_num <= 0)

            # 3. LÓGICA DEL BUSCADOR
            if pasa_fecha and (search_term in nombre.lower() or 
                search_term in str(cedula).lower() or 
                search_term in str(telefono).lower()):
                
                c['aux_nombre'] = nombre
                # Ajuste de texto para que diga "Paga hoy" si dias_num es 0
                if dias_num == 0:
                    c['aux_atraso_txt'] = "Paga hoy"
                else:
                    c['aux_atraso_txt'] = f"Atraso: {dias_num} días" if dias_num > 0 else txt_atraso_base
                
                c['aux_dias_num'] = dias_num
                c['aux_prioridad'] = obtener_prioridad(dias_num, float(c.get('balance_pendiente', 0)))
                datos_procesados.append(c)

        # Ordenamos según tu prioridad original
        datos_procesados = sorted(datos_procesados, key=lambda x: x['aux_prioridad'], reverse=True)

        # --- DIBUJADO DE LA LISTA (CON TODAS TUS FUNCIONES ORIGINALES) ---
        for item in datos_procesados:
            token = item['id']
            m_pend = float(item.get('balance_pendiente', 0))

            with st.container(border=True):
                c_nom, c_status, c_inputs, c_btn = st.columns([1.2, 1, 1.2, 0.8])
                
                with c_nom:
                    st.markdown(f"**{item['aux_nombre']}**")
                    st.caption(f"Debe: RD$ {m_pend:,.2f}")
                    if st.button("🔍 Ver Historial", key=f"hist_{token}", use_container_width=True):
                        mostrar_historial_modal(item, u_id)

                with c_status:
                    # SEMÁFORO CORREGIDO
                    if modo_analisis: 
                        st.info("✅ SALDADO")
                    elif item['aux_dias_num'] > 0: 
                        st.error(f"🚨 {item['aux_atraso_txt']}")
                    elif item['aux_dias_num'] == 0:
                        st.warning("⚠️ Paga hoy mismo")
                    else: 
                        st.success("🟢 Al día")
                        
                with c_inputs:
                    if not modo_analisis:
                        cuota_acordada = float(item.get('cuota_esperada', 0))
                        valor_default = min(cuota_acordada, m_pend) if cuota_acordada > 0 else m_pend
                        st.caption(f"Cuota: RD$ {cuota_acordada:,.2f}")
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
                        if st.button("📄 Detalles", key=f"det_{token}", use_container_width=True):
                            mostrar_historial_modal(item, u_id)

                # AQUÍ ESTÁ TU BLOQUE DE MORA QUE NO QUERÍAS PERDER
                if not modo_analisis:
                    with st.expander("⚖️ Penalidad (Mora)"):
                        st.number_input("Monto de Mora", min_value=0.0, key=f"mora_{token}")
    else:
        st.info("No se encontraron registros.")
        
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
                    
                    # --- DÍA FIJO (MODIFICADO: SE AGREGÓ "Diario") ---
                    # Reemplazamos "Cada 7 día" por la lógica de cobro todos los días
                    dias_semana = {
                        "Diario (Todos los días)": "diario", 
                        "Lunes": MO, 
                        "Martes": TU, 
                        "Miércoles": WE, 
                        "Jueves": TH, 
                        "Viernes": FR, 
                        "Sábado": SA, 
                        "Domingo": SU
                    }
                    
                    if freq_sel == "Semanal":
                        dia_input = st.selectbox("Día de cobro fijo", list(dias_semana.keys()), index=0)
                        dia_fijo = dias_semana[dia_input]
                    else:
                        dia_fijo = st.number_input("Día del mes (0 = Igual a hoy)", min_value=0, max_value=31, value=0)
                
                with col3:
                    cuotas_n = st.number_input("Cantidad de Cuotas", min_value=1, value=4)
                    fecha_desembolso = st.date_input("Fecha de desembolso", value=datetime.now().date())

                # --- MOTOR DE CÁLCULO DE FECHAS (SINTAXIS CORREGIDA) ---
                fechas_proyectadas = []
                referencia = fecha_desembolso 

                for i in range(cuotas_n):
                    if freq_sel == "Semanal":
                        # Nueva lógica para "Todos los días"
                        if dia_fijo == "diario":
                            next_date = referencia + relativedelta(days=i+1)
                        elif dia_fijo is None:
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

                # --- LÓGICA DE WHATSAPP CON MENSAJE PREDETERMINADO ---
                if cliente_obj:
                    import urllib.parse
                    tel_raw = "".join(filter(str.isdigit, str(cliente_obj.get('telefono', ''))))
                    # Formato internacional: agregamos el '1' si tiene 10 dígitos (RD/USA)
                    tel_final = f"1{tel_raw}" if len(tel_raw) == 10 else tel_raw
                    
                    # Mensaje personalizado con negritas de WhatsApp
                    texto_msj = (
                        f"Hola *{cliente_obj['nombre']}*, se ha generado tu factura en *CobroYa*.\n"
                        f"💰 *Monto Total:* RD$ {total_f:,.2f}\n"
                        f"🗓️ *Cuotas:* {cuotas_n}\n"
                        f"¡Gracias por tu confianza!"
                    )
                    msj_encoded = urllib.parse.quote(texto_msj)
                    st.session_state['wa_link'] = f"https://wa.me/{tel_final}?text={msj_encoded}"
                    
                if st.button("🚀 REGISTRAR Y ACTIVAR", use_container_width=True, disabled=not (capital > 0 and continuar and cliente_obj is not None)):
                    # GENERACIÓN DE DATOS REALES PARA AUDITORÍA
                    import uuid
                    codigo_fac = f"FAC-{str(uuid.uuid4())[:8].upper()}"
                    
                    # IMPORTANTE: Tomamos la fecha de la tabla, por si el usuario la editó
                    primera_fecha_final = df_e.iloc[0]['Fecha']
                    
                    # 1. Insertar en CUENTAS (Capturando Capital Real y Código)
                    res_c = conn.table("cuentas").insert({
                        "cliente_id": cliente_obj['id'], 
                        "codigo_factura": codigo_fac,
                        "capital_puro": float(capital),
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
                                 f"📄 *Factura:* {codigo_fac}\n" \
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
            # Buscador principal
            search_query = st.text_input("🔍", placeholder="Buscar cliente...", label_visibility="collapsed")
        
        with col_filter:
            # FILTRO DIVIDIDO: Se eliminó "Próximos/Hoy" y se agregaron "Hoy" y "Esta Semana"
            opciones = ["🌍 Todos", "🔴 Atrasados", "🟢 Al Día", "🟠 Pagan hoy", "🗓️ Prox. 7 dias"]
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
                
                # --- NUEVA LÓGICA: HOY ---
                elif sel_filtro == "🟠 Pagan hoy":
                    if prox_pago:
                        dias_dif = (prox_pago - hoy).days
                        # Si la diferencia es 0 es porque toca cobrar hoy mismo
                        if dias_dif == 0 and balance > 0:
                            match_estado = True

                # --- NUEVA LÓGICA: ESTA SEMANA (7 DÍAS) ---
                elif sel_filtro == "🗓️ Prox. 7 dias":
                    if prox_pago:
                        dias_dif = (prox_pago - hoy).days
                        # Filtra pagos desde hoy (0) hasta dentro de 7 días (7)
                        if 0 <= dias_dif <= 7 and balance > 0:
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

@st.dialog("📦 EXPEDIENTE MAESTRO DE CLIENTE", width="large")
def modal_detalle(cliente, cuentas, pagos, u_id=None):
    # --- CÁLCULO DE DEUDA GLOBAL (Para la esquina superior derecha) ---
    mis_ctas = [ct for ct in cuentas if ct['cliente_id'] == cliente['id']]
    total_monto_inicial = sum(float(ct.get('monto_inicial', 0)) for ct in mis_ctas)
    
    # Sumar todos los pagos de todas las cuentas de este cliente
    ids_mis_ctas = [ct['id'] for ct in mis_ctas]
    total_abonado_global = sum(float(p['monto_pagado']) for p in pagos if p.get('cuenta_id') in ids_mis_ctas)
    
    deuda_global_pendiente = total_monto_inicial - total_abonado_global

    # --- CSS: TU DISEÑO PREMIUM ---
    st.markdown(f"""
        <style>
        .global-debt-container {{
            text-align: right; background: #fff5f5; padding: 12px;
            border-radius: 12px; border: 1px solid #feb2b2; margin-bottom: 15px;
        }}
        .resumen-box {{
            background-color: #f8faff; border: 1px solid #e1e8f0;
            border-radius: 12px; padding: 15px; font-size: 0.9rem;
        }}
        .resumen-item {{ display: flex; justify-content: space-between; margin-bottom: 5px; color: #4a5568; }}
        .resumen-valor {{ font-weight: 700; color: #2d3748; }}
        .narrativa-apertura {{
            background-color: #f0f7ff; padding: 15px; border-radius: 10px;
            font-size: 0.95rem; color: #1e3a8a; border-left: 5px solid #1a73e8;
        }}
        .movimiento-row {{
            padding: 12px; margin-bottom: 8px; border-radius: 8px;
            display: flex; justify-content: space-between; align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); background: white;
        }}
        .status-verde {{ border-left: 5px solid #28a745; }}
        </style>
    """, unsafe_allow_html=True)

    # --- CABECERA CON DEUDA TOTAL ---
    col_tit, col_bal = st.columns([2, 1])
    with col_tit:
        st.title(f"👤 {cliente['nombre'].upper()}")
        st.caption(f"ID: {cliente.get('id')} | Cédula: {cliente.get('cedula', 'N/A')}")
    
    with col_bal:
        st.markdown(f"""
            <div class="global-debt-container">
                <small style="color: #c53030; font-weight: 600;">DEUDA TOTAL PENDIENTE</small><br>
                <span style="font-size: 1.4rem; font-weight: 800; color: #c53030;">RD$ {deuda_global_pendiente:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)

    tab_historial, tab_abonos, tab_plan, tab_perfil = st.tabs([
        "📜 HISTORIAL COMPLETO", "💵 ABONOS REALES", "📅 PLAN IDEAL", "⚙️ PERFIL"
    ])

# --- PESTAÑA 1: HISTORIAL COMPLETO ---
    with tab_historial:
        for idx, ct in enumerate(mis_ctas):
            c_id = ct['id']
            cod_fac = ct.get('codigo_factura', f"FAC-{str(c_id)[:6].upper()}")
            
            # 1. Cálculos de la cuenta
            monto_ini = float(ct.get('monto_inicial', 0))
            cap_puro = float(ct.get('capital_puro', 0))
            ganancia = monto_ini - cap_puro
            f_inicio = pd.to_datetime(ct['fecha_creacion']).strftime('%d/%m/%Y')
            
            # Intentar buscar la fecha final en el plan de cuotas si existe
            res_plan = conn.table("plan_cuotas").select("fecha_esperada").eq("cuenta_id", c_id).order("numero_cuota", desc=True).limit(1).execute()
            f_final = pd.to_datetime(res_plan.data[0]['fecha_esperada']).strftime('%d/%m/%Y') if res_plan.data else "Final del ciclo"

            # 2. Pagos de esta cuenta
            mis_pagos_cta = [p for p in pagos if p.get('cuenta_id') == c_id]
            total_abonado = sum(float(p['monto_pagado']) for p in mis_pagos_cta)
            faltante = monto_ini - total_abonado
            
            # EXPANDER PRINCIPAL
            with st.expander(f"📄 Factura: {cod_fac} | 🔴 Faltante: RD$ {faltante:,.2f}", expanded=(idx==0)):
                
                # Layout: Narrativa (Izquierda) | Resumen (Derecha)
                col_info, col_res = st.columns([2.2, 1])
                
                with col_info:
                    st.markdown(f"""
                    <div class="narrativa-apertura">
                        <span style="font-weight: 800; font-size: 1.1rem; color: #1e3a8a; display: block; margin-bottom: 8px;">
                            🚀 INICIO DE OPERACIÓN
                        </span>
                        Se generó una factura por un total de <b>RD$ {monto_ini:,.2f}</b> al cliente 
                        <b>{cliente['nombre'].upper()}</b> el día {f_inicio}. 
                        <br><br>
                        Esta operación cuenta con un capital base de <b>RD$ {cap_puro:,.2f}</b>, 
                        con el cual se espera obtener una ganancia neta de <b>RD$ {ganancia:,.2f}</b> 
                        al completar el ciclo de cobros pautado para el <b>{f_final}</b>.
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_res:
                    st.markdown(f"""
                        <div class="resumen-box">
                            <div style="font-weight:800; color:#1e3a8a; border-bottom:1px solid #e1e8f0; margin-bottom:10px; padding-bottom:5px;">
                                DATOS CLAVE
                            </div>
                            <div class="resumen-item"><span>Total Factura:</span><span class="resumen-valor">RD$ {monto_ini:,.2f}</span></div>
                            <div class="resumen-item"><span>Inversión:</span><span class="resumen-valor">RD$ {cap_puro:,.2f}</span></div>
                            <div class="resumen-item" style="margin-top:8px; padding-top:8px; border-top:1px dashed #cbd5e0;">
                                <span>Restante:</span><span class="resumen-valor" style="color:#e53e3e; font-size:1rem;">RD$ {faltante:,.2f}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                st.write("") # Espaciador
                st.markdown("**🔍 DETALLE DE MOVIMIENTOS**")
                
                if not mis_pagos_cta:
                    st.info("No hay abonos registrados para esta factura.")
                else:
                    # Mostrar movimientos con el indicador lateral
                    for p in sorted(mis_pagos_cta, key=lambda x: x['fecha_pago']):
                        st.markdown(f"""
                        <div class="movimiento-row status-verde">
                            <div>
                                <span style="color:#28a745;">●</span> 
                                <b>{pd.to_datetime(p['fecha_pago']).strftime('%d/%m/%Y')}</b> — 
                                <span style="font-size:1.05rem;">RD$ {float(p['monto_pagado']):,.2f}</span>
                                <br><small style="color:gray; margin-left:18px;">Abono recibido correctamente</small>
                            </div>
                            <div style="text-align:right;">
                                <code style="color:#a0aec0; font-size:0.75rem;">REF-{str(p['id'])[:6].upper()}</code>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

# --- PESTAÑA 2: ABONOS REALES (VERSIÓN CON INDENTACIÓN CORREGIDA) ---
    with tab_abonos:
        st.markdown("### 💵 Gestión de Cobros y Auditoría")
        
        # 1. Inyectar CSS (Asegurando que el timeline y el mensaje de vacío se vean bien)
        st.markdown("""
            <style>
            .timeline-container { 
                border-left: 2px solid #E2E8F0; 
                margin-left: 15px; 
                padding-left: 20px; 
            }
            .item-wrapper {
                position: relative;
                margin-bottom: 20px;
            }
            .timeline-dot {
                position: absolute; left: -35px;
                width: 28px; height: 28px; border-radius: 50%;
                display: flex; align-items: center; justify-content: center;
                font-size: 0.75rem; font-weight: bold; color: white;
                background: #2D3748; box-shadow: 0 0 0 4px white; z-index: 10;
            }
            .dot-atraso { background: #ED8936; }
            .dot-peligro { background: #E53E3E; }
            .pago-card {
                background: #ffffff; border-radius: 12px; padding: 15px 20px;
                border: 1px solid #E2E8F0; box-shadow: 0 1px 3px rgba(0,0,0,0.02);
            }
            .flex-row {
                display: flex; justify-content: space-between; align-items: flex-end;
            }
            .badge-atraso { background: #fff5f5; color: #c53030; padding: 4px 10px; border-radius: 8px; font-weight: 800; font-size: 0.7rem; border: 1px solid #fed7d7; }
            .badge-tiempo { background: #f0fff4; color: #2f855a; padding: 4px 10px; border-radius: 8px; font-weight: 800; font-size: 0.7rem; border: 1px solid #c6f6d5; }
            .alerta-seguridad { 
                background: #fffaf0; border: 1px solid #feebc8; padding: 10px; 
                border-radius: 8px; color: #7b341e; font-size: 0.8rem; margin-bottom: 15px;
            }
            .text-muted { color: #A0AEC0; font-size: 0.70rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
            .monto-principal { font-size: 1.15rem; font-weight: 800; color: #1A202C; }
            .empty-info { 
                background: #F7FAFC; border: 2px dashed #E2E8F0; padding: 30px; 
                border-radius: 12px; text-align: center; color: #718096; 
                margin-bottom: 20px; font-weight: 500;
            }
            </style>
        """, unsafe_allow_html=True)

        # 2. LÓGICA DE ORDENAMIENTO (Facturas con abonos arriba)
        cuentas_preparadas = []
        for ct in mis_ctas:
            c_id = ct['id']
            p_cta = sorted([p for p in pagos if p.get('cuenta_id') == c_id], key=lambda x: x['fecha_pago'])
            cuentas_preparadas.append({
                'datos': ct,
                'pagos': p_cta,
                'tiene_pagos': len(p_cta) > 0
            })

        # Ordenar: Las que tienen abonos primero
        cuentas_ordenadas = sorted(cuentas_preparadas, key=lambda x: x['tiene_pagos'], reverse=True)

        # 3. RENDERIZADO
        for item in cuentas_ordenadas:
            ct = item['datos']
            mis_pagos_cta = item['pagos']
            c_id = ct['id']
            cod_fac = ct.get('codigo_factura', f"FAC-{str(c_id)[:6].upper()}")
            res_plan = conn.table("plan_cuotas").select("*").eq("cuenta_id", c_id).order("numero_cuota").execute().data

            # --- LÓGICA DE ESTADO ---
            estado_cta = str(ct.get('estado', '')).strip().lower()
            es_saldada = estado_cta in ['saldada', 'cerrada', 'pagada']
            
            monto_total_fac = float(ct.get('monto_total', 0))
            if monto_total_fac > 0:
                total_abonado = sum(float(p['monto_pagado']) for p in mis_pagos_cta)
                if total_abonado >= monto_total_fac:
                    es_saldada = True

            # --- CONTENEDOR UI ---
            if es_saldada:
                contenedor_UI = st.expander(f"📁 Historial de Cobros: {cod_fac} (SALDADA)", expanded=False)
            else:
                st.markdown(f"<h4 style='color:#2D3748; margin-top:30px; margin-bottom:15px;'>📊 Línea de Tiempo de Cobros: {cod_fac}</h4>", unsafe_allow_html=True)
                contenedor_UI = st.container()

            with contenedor_UI:
                if not mis_pagos_cta:
                    st.markdown(f"""
                        <div class="empty-info">
                            <span style="font-size: 1.5rem;">ℹ️</span><br><br>
                            Esta factura todavía no tiene abonos registrados.
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown('<div class="timeline-container">', unsafe_allow_html=True)
                    
                    for p_idx, p in enumerate(mis_pagos_cta):
                        f_pago = pd.to_datetime(p['fecha_pago']).date()
                        dia_mes = f_pago.strftime('%d')
                        
                        msg_atraso = '<span class="badge-tiempo">A TIEMPO</span>'
                        dot_class = "timeline-dot"
                        dias_txt = "0 días"
                        
                        if res_plan and p_idx < len(res_plan):
                            f_esp = pd.to_datetime(res_plan[p_idx]['fecha_esperada']).date()
                            if f_pago > f_esp:
                                dias_reales = (f_pago - f_esp).days
                                msg_atraso = f'<span class="badge-atraso">ATRASADO</span>'
                                dias_txt = f"{dias_reales} días"
                                dot_class = "timeline-dot dot-atraso" if dias_reales <= 5 else "timeline-dot dot-peligro"

                        creado = pd.to_datetime(p.get('created_at', p.get('fecha_pago')), utc=True)
                        es_editable = (pd.to_datetime('now', utc=True) - creado).total_seconds() / 3600 <= 48

                        lbl_fecha  = '<div class="text-muted" style="margin-bottom: 4px;">MES ABONADO</div>' if p_idx == 0 else ''
                        lbl_estado = '<div class="text-muted" style="margin-bottom: 4px;">CONDICIÓN</div>' if p_idx == 0 else ''
                        lbl_tiempo = '<div class="text-muted" style="margin-bottom: 4px;">ATRASO DE</div>' if p_idx == 0 else ''
                        lbl_mora   = '<div class="text-muted" style="margin-bottom: 4px;">MORA COBRADA</div>' if p_idx == 0 else ''

                        col_data, col_btn = st.columns([6, 1]) 
                        
                        with col_data:
                            dot_top = "25px" if p_idx == 0 else "12px"
                            st.markdown(f"""
                            <div class="item-wrapper">
                                <div class="{dot_class}" style="top: {dot_top};">{dia_mes}</div>
                                <div class="pago-card">
                                    <div class="flex-row">
                                        <div style="flex: 1.2;">
                                            {lbl_fecha}
                                            <div class="text-muted" style="font-size: 0.85rem; color: #718096; font-weight: 500;">{f_pago.strftime('%d de %B %Y')}</div>
                                            <div class="monto-principal">RD$ {float(p['monto_pagado']):,.2f}</div>
                                        </div>
                                        <div style="flex: 1; text-align: center;">
                                            {lbl_estado}
                                            <div>{msg_atraso}</div>
                                        </div>
                                        <div style="flex: 1; text-align: center; color: #718096; font-size: 0.85rem;">
                                            {lbl_tiempo}
                                            <div style="font-weight: 600;">{dias_txt}</div>
                                        </div>
                                        <div style="flex: 1; text-align: right;">
                                            {lbl_mora}
                                            <div style="font-weight: 700; color: #4A5568;">RD$ {float(p.get('mora_pagada', 0)):,.2f}</div>
                                        </div>
                                    </div>
                                </div>
                            </div>""", unsafe_allow_html=True)

                        with col_btn:
                            margin_top = "30px" if p_idx == 0 else "15px"
                            st.markdown(f"<div style='height: {margin_top};'></div>", unsafe_allow_html=True)
                            
                            if es_editable:
                                with st.popover("📝", use_container_width=True):
                                    st.markdown('<div class="alerta-seguridad">🚨 <b>AUDITORÍA ACTIVA</b><br>Su IP está siendo registrada.</div>', unsafe_allow_html=True)
                                    new_m = st.number_input("Nuevo Monto", value=float(p['monto_pagado']), key=f"nm_{p['id']}")
                                    new_f = st.date_input("Nueva Fecha", value=f_pago, key=f"nf_{p['id']}")
                                    
                                    st.divider()
                                    c1 = st.checkbox("Confirmo corrección", key=f"c1_{p['id']}")
                                    c2 = st.checkbox("Dinero verificado", key=f"c2_{p['id']}")
                                    
                                    if c1 and c2:
                                        if st.button("💾 GUARDAR", key=f"sv_{p['id']}", type="primary", use_container_width=True):
                                            conn.table("pagos").update({"monto_pagado": new_m, "fecha_pago": str(new_f)}).eq("id", p['id']).execute()
                                            st.rerun()
                                    
                                    st.divider()
                                    with st.expander("🗑️ ELIMINAR ABONO"):
                                        st.error("Esta acción es irreversible.")
                                        if st.checkbox("Autorizo borrado", key=f"del_chk_{p['id']}"):
                                            if st.text_input("Escribe ELIMINAR", key=f"del_in_{p['id']}") == "ELIMINAR":
                                                if st.button("🔥 BORRAR", key=f"btn_del_{p['id']}", type="primary"):
                                                    conn.table("pagos").delete().eq("id", p['id']).execute()
                                                    st.rerun()
                            else:
                                st.markdown("<div style='text-align:center; padding-top:10px; font-size:1.2rem; color:#E2E8F0;'>🔒</div>", unsafe_allow_html=True)

                    st.markdown('</div>', unsafe_allow_html=True)
                
# --- PESTAÑA 3: PLAN IDEAL (CRONOGRAMA VS REALIDAD) ---
    with tab_plan:
        st.markdown("### 📅 Plan de Pagos por Factura")
        
        for idx, ct in enumerate(mis_ctas):
            c_id = ct['id']
            # Obtener el código de factura o un genérico si no existe
            cod_fac = ct.get('codigo_factura', f"FACTURA SIN CÓDIGO (ID: {str(c_id)[:4]})")
            
            # Título directo sin expander
            st.markdown(f"#### 📄 {cod_fac}")
            
            # 1. Obtener Plan y Pagos (Ordenados para comparar uno a uno)
            res_plan_db = conn.table("plan_cuotas").select("*").eq("cuenta_id", c_id).order("numero_cuota").execute().data
            mis_pagos_cta = sorted([p for p in pagos if p.get('cuenta_id') == c_id], key=lambda x: x['fecha_pago'])
            progreso_total = sum(float(p['monto_pagado']) for p in mis_pagos_cta)

            if not res_plan_db:
                st.info(f"ℹ️ No hay un plan de cuotas generado para la factura {cod_fac}.")
                st.divider() # Separador entre facturas
            else:
                datos_visuales = []
                saldo_recorrido = progreso_total
                
                for p_idx, cuota in enumerate(res_plan_db):
                    m_esp = float(cuota['monto_cuota'])
                    f_esp = pd.to_datetime(cuota['fecha_esperada']).date()
                    
                    # --- LÓGICA DE ESTADO Y RETRASO ---
                    retraso_txt = "-" # Por defecto si no está pagada o no hay retraso
                    
                    if saldo_recorrido >= (m_esp - 0.01):
                        estado = '<span style="color:#28a745; font-weight:bold;">✅ PAGADA</span>'
                        
                        # Calculamos retraso si hay un pago real asociado a esta posición de cuota
                        if p_idx < len(mis_pagos_cta):
                            f_pago_real = pd.to_datetime(mis_pagos_cta[p_idx]['fecha_pago']).date()
                            if f_pago_real > f_esp:
                                dias = (f_pago_real - f_esp).days
                                retraso_txt = f'<span style="color:#d93025;">{dias} días de retraso</span>'
                            else:
                                retraso_txt = '<span style="color:#28a745;">Al día</span>'
                        
                        saldo_recorrido -= m_esp
                        
                    elif saldo_recorrido > 0:
                        estado = f'<span style="color:#fd7e14; font-weight:bold;">⚠️ ABONO (Faltó RD$ {m_esp-saldo_recorrido:,.2f})</span>'
                        saldo_recorrido = 0
                        retraso_txt = "Incompleto"
                    else:
                        vencida = f_esp < datetime.now().date()
                        txt = "🚨 VENCIDA" if vencida else "⏳ PENDIENTE"
                        color = "#d93025" if vencida else "#5f6368"
                        estado = f'<span style="color:{color}; font-weight:bold;">{txt}</span>'
                        
                        if vencida:
                            dias_vencida = (datetime.now().date() - f_esp).days
                            retraso_txt = f'<b>{dias_vencida} días vencida</b>'

                    datos_visuales.append({
                        "CUOTA": f"#{cuota['numero_cuota']}",
                        "FECHA ESPERADA": f_esp.strftime('%d/%m/%Y'),
                        "MONTO": f"RD$ {m_esp:,.2f}",
                        "ESTADO": estado,
                        "AUDITORÍA DE PAGO": retraso_txt
                    })
                
                # --- CAMBIO REALIZADO AQUÍ PARA AJUSTE MÓVIL ---
                df_v = pd.DataFrame(datos_visuales)
                # Convertimos a HTML
                html_tabla = df_v.to_html(escape=False, index=False, classes="dataframe")
                # Envolvemos en un div con scroll horizontal para que no se corte en el celular
                st.write(
                    f'<div style="overflow-x:auto; width:100%; border-radius:5px;">{html_tabla}</div>', 
                    unsafe_allow_html=True
                )
                st.divider() # Espacio visual entre facturas

    # --- PESTAÑA 4: PERFIL (GESTIÓN DE DATOS) ---
    with tab_perfil:
        # Formulario con Key Única por cliente
        with st.form(key=f"form_perfil_master_{cliente['id']}"):
            st.subheader("📝 Información del Cliente")
            col1, col2 = st.columns(2)
            n_nom = col1.text_input("Nombre Completo", value=cliente['nombre'])
            n_ced = col2.text_input("Cédula/ID", value=cliente.get('cedula', ''))
            n_tel = col1.text_input("Teléfono de Contacto", value=cliente.get('telefono', ''))
            
            if st.form_submit_button("💾 ACTUALIZAR EXPEDIENTE"):
                conn.table("clientes").update({
                    "nombre": n_nom, 
                    "cedula": n_ced, 
                    "telefono": n_tel
                }).eq("id", cliente['id']).execute()
                st.success("Información actualizada.")
                st.rerun()

    # --- CIERRE FINAL DEL DIALOG ---
    st.divider()
    if st.button("❌ CERRAR EXPEDIENTE", use_container_width=True, key="btn_final_close"):
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
                        # --- LÓGICA INTERNACIONAL ---
                        # Extraemos SOLO los dígitos (esto elimina +, espacios, guiones, etc.)
                        tel_raw = "".join(filter(str.isdigit, str(cl.get('telefono', ''))))
                        
                        # Si el número empieza por '00', lo corregimos al formato que le gusta a WA (sin ceros iniciales)
                        if tel_raw.startswith("00"):
                            tel_final = tel_raw[2:]
                        # "Seguro" para RD/USA: Si el usuario solo pone 10 dígitos, asumimos código 1
                        elif len(tel_raw) == 10:
                            tel_final = f"1{tel_raw}"
                        else:
                            # Para cualquier otro país (Venezuela 58, Colombia 57, etc.) 
                            # el sistema usará el número tal cual si ya trae su código.
                            tel_final = tel_raw
                            
                        wa_url = f"https://wa.me/{tel_final}"
                        
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
    from datetime import datetime, date, timedelta
    
    # --- 1. AJUSTE DE ZONA HORARIA (RD: UTC-4) ---
    # Esto asegura que 'hoy' y 'ahora' sean los de Santo Domingo, no los del servidor
    ahora_rd = datetime.utcnow() - timedelta(hours=4)
    hoy = ahora_rd.date()
    ahora_rd_str = ahora_rd.strftime("%Y-%m-%d %H:%M:%S")

    # --- 2. CONSULTA GLOBAL DE DATOS ---
    res_gastos = conn.table("gastos").select("*").eq("user_id", u_id).eq("visible_usuario", True).order("fecha_gasto", desc=True).execute()
    datos_gastos = res_gastos.data if res_gastos.data else []

    # Segmentación de datos
    gastos_rapidos = [g for g in datos_gastos if g.get("nombre_suplidor") == "Gasto de Caja" and g["estado"] == "Pagado"]
    compromisos_pendientes = [g for g in datos_gastos if g["estado"] == "Pendiente"]
    todo_lo_pagado = [g for g in datos_gastos if g["estado"] == "Pagado"]

    # --- 3. MODALES Y ALERTAS ---
    @st.dialog("⚠️ ADVERTENCIA CRÍTICA")
    def modal_reset_historial():
        st.error("### ¿ESTÁS ABSOLUTAMENTE SEGURO?")
        st.write("Escribe **CONFIRMAR** para proceder:")
        confirmacion = st.text_input("Palabra de seguridad")
        if st.button("🔥 BORRAR TODO EL HISTORIAL", type="primary", use_container_width=True):
            if confirmacion == "CONFIRMAR":
                conn.table("gastos").update({"visible_usuario": False}).eq("user_id", u_id).eq("estado", "Pagado").execute()
                st.rerun()

    @st.dialog("🎯 Registro Exitoso")
    def modal_decision_pago(gasto_id, concepto):
        st.write(f"Registro: **{concepto}**")
        st.markdown("¿Se pagó en este momento?")
        c1, c2 = st.columns(2)
        if c1.button("💵 SÍ, PAGAR AHORA", type="primary", use_container_width=True):
            conn.table("gastos").update({"estado": "Pagado"}).eq("id", gasto_id).execute()
            st.rerun()
        if c2.button("⏳ LUEGO", use_container_width=True):
            st.rerun()

    # Notificaciones preventivas
    if compromisos_pendientes:
        avisos = []
        for g in compromisos_pendientes:
            if g.get('fecha_gasto'):
                # Validamos fecha para evitar errores de tipo
                try:
                    f_venc = datetime.strptime(g['fecha_gasto'][:10], "%Y-%m-%d").date()
                    dias = (f_venc - hoy).days
                    if 0 <= dias <= 4:
                        avisos.append(f"🔔 **{g['descripcion']}** vence en {dias} días.")
                    elif dias < 0:
                        avisos.append(f"🚨 **{g['descripcion']}** está vencido.")
                except: pass
        if avisos:
            with st.expander("📢 ALERTAS DE PAGO", expanded=True):
                for a in avisos: st.write(a)

    # --- 4. ESTRUCTURA DE PESTAÑAS ---
    st.title("Gastos y Compromisos")
    t1, t2, t3 = st.tabs(["⚡ Gasto Rápido", "📅 Compromisos", "📜 Historial de Gastos"])

    # --- PESTAÑA 1: GASTO RÁPIDO ---
    with t1:
        with st.form("f_rapido", clear_on_submit=True):
            st.markdown("### Gasto de Caja Directo")
            col1, col2 = st.columns([2, 1])
            concepto_r = col1.text_input("Concepto", placeholder="Gasolina, café, etc.")
            monto_r = col2.number_input("Monto RD$", min_value=0.0, step=50.0)
            
            if st.form_submit_button("🚀 REGISTRAR Y DESCONTAR", use_container_width=True):
                if concepto_r and monto_r > 0:
                    # SE GUARDA CON LA HORA EXACTA DE RD (ahora_rd_str)
                    conn.table("gastos").insert({
                        "descripcion": concepto_r, 
                        "monto": monto_r, 
                        "user_id": u_id,
                        "estado": "Pagado", 
                        "nombre_suplidor": "Gasto de Caja",
                        "sector": "Varios", 
                        "fecha_gasto": ahora_rd_str, 
                        "visible_usuario": True
                    }).execute()
                    st.rerun()
        
        st.markdown("---")
        st.caption("Gastos rápidos recientes (Hoy)")
        for g in gastos_rapidos[:5]:
            # Formateamos la hora para que se vea limpia en la lista
            hora = g['fecha_gasto'][11:16] if g.get('fecha_gasto') else "--:--"
            st.text(f"🕒 {hora} | {g['descripcion']} - RD$ {g['monto']:,.0f}")

# --- PESTAÑA 2: COMPROMISOS ---
    with t2:
        # 1. MÉTRICA SUPERIOR ESTILO APPLE
        total_pendientes_monto = sum(g["monto"] for g in compromisos_pendientes)
        st.markdown(f"""
            <div style='background-color:#1E1E1E; padding:15px; border-radius:12px; border: 1px solid #333; margin-bottom:20px;'>
                <p style='color:#8E8E93; margin:0; font-size:0.8rem;'>TOTAL PENDIENTE</p>
                <h2 style='color:#FFFFFF; margin:0;'>RD$ {total_pendientes_monto:,.2f}</h2>
                <p style='color:#FF9F0A; margin:0; font-size:0.7rem;'>{len(compromisos_pendientes)} compromisos activos</p>
            </div>
        """, unsafe_allow_html=True)

        # --- FUNCIONES DE EDICIÓN Y BORRADO (MODALES) ---
        @st.dialog("📝 Editar Compromiso")
        def editar_compromiso(gasto):
            with st.form("edit_form"):
                n_desc = st.text_input("Concepto", value=gasto['descripcion'])
                n_monto = st.number_input("Monto RD$", value=float(gasto['monto']))
                n_sup = st.text_input("Suplidor", value=gasto.get('nombre_suplidor', ''))
                n_fec = st.date_input("Vencimiento", value=datetime.strptime(gasto['fecha_gasto'][:10], "%Y-%m-%d") if gasto.get('fecha_gasto') else hoy)
                n_rec = st.checkbox("¿Es recurrente mensual?", value=gasto.get('es_recurrente', False))
                
                st.caption("Al guardar, se actualizarán los datos del compromiso.")
                if st.form_submit_button("Guardar Cambios", use_container_width=True):
                    conn.table("gastos").update({
                        "descripcion": n_desc, "monto": n_monto, 
                        "nombre_suplidor": n_sup, "fecha_gasto": str(n_fec),
                        "es_recurrente": n_rec
                    }).eq("id", gasto['id']).execute()
                    st.rerun()

        @st.dialog("🗑️ Eliminar")
        def eliminar_compromiso(gasto_id, desc):
            st.write(f"¿Seguro que quieres eliminar **{desc}**?")
            st.caption("Esta acción quitará el pendiente de tu lista.")
            if st.button("Sí, eliminar ahora", type="primary", use_container_width=True):
                conn.table("gastos").update({"visible_usuario": False}).eq("id", gasto_id).execute()
                st.rerun()

        # --- FORMULARIO DE REGISTRO ---
        with st.expander("➕ Programar Nuevo Pago", expanded=False):
            with st.form("f_plan_new", clear_on_submit=True):
                c1, c2 = st.columns([2, 1])
                conc = c1.text_input("¿Qué hay que pagar?")
                mon = c2.number_input("Monto RD$", min_value=0.0)
                c3, c4 = st.columns(2)
                sup = c3.text_input("Suplidor")
                fec = c4.date_input("Fecha límite", value=hoy)
                rec = st.checkbox("Hacer este gasto recurrente (Todos los meses)")
                
                if st.form_submit_button("Guardar Compromiso", use_container_width=True):
                    if conc and mon > 0:
                        res = conn.table("gastos").insert({
                            "descripcion": conc, "monto": mon, "user_id": u_id,
                            "estado": "Pendiente", "nombre_suplidor": sup if sup else "General",
                            "sector": "Programado", "fecha_gasto": str(fec), 
                            "es_recurrente": rec, "visible_usuario": True
                        }).execute()
                        if res.data: modal_decision_pago(res.data[0]['id'], conc)

        st.markdown("---")

        # --- LISTADO DE PENDIENTES ---
        if not compromisos_pendientes:
            st.info("✅ Todo al día.")
        else:
            for g in compromisos_pendientes:
                with st.container(border=True):
                    # Diseño de 4 columnas para que quepan los tres puntitos al final
                    col_info, col_monto, col_pago, col_menu = st.columns([2, 1, 0.8, 0.4])
                    
                    with col_info:
                        # Etiqueta de recurrencia
                        rec_tag = "🔄 " if g.get('es_recurrente') else ""
                        st.markdown(f"**{rec_tag}{g['descripcion']}**")
                        st.caption(f"🏢 {g['nombre_suplidor']}")
                        
                        # Lógica de Vencido vs Próximo
                        if g.get('fecha_gasto'):
                            fv = datetime.strptime(g['fecha_gasto'][:10], "%Y-%m-%d").date()
                            if fv < hoy:
                                st.markdown(f"<span style='color:#FF4B4B; font-size:0.8rem;'>⚠️ Vencido ({fv})</span>", unsafe_allow_html=True)
                            else:
                                st.caption(f"📅 Vence: {fv}")

                    with col_monto:
                        st.markdown(f"**RD$ {g['monto']:,.0f}**")

                    with col_pago:
                        if st.button("💵", key=f"pay_btn_{g['id']}", help="Marcar como pagado"):
                            # Si es recurrente, antes de marcar como pagado, podríamos crear el del mes que viene
                            if g.get('es_recurrente'):
                                f_actual = datetime.strptime(g['fecha_gasto'][:10], "%Y-%m-%d").date()
                                f_siguiente = f_actual + timedelta(days=30)
                                conn.table("gastos").insert({
                                    "descripcion": g['descripcion'], "monto": g['monto'], "user_id": u_id,
                                    "estado": "Pendiente", "nombre_suplidor": g['nombre_suplidor'],
                                    "sector": g['sector'], "fecha_gasto": str(f_siguiente), 
                                    "es_recurrente": True, "visible_usuario": True
                                }).execute()

                            conn.table("gastos").update({"estado": "Pagado", "fecha_gasto": ahora_rd_str}).eq("id", g['id']).execute()
                            st.rerun()

                    with col_menu:
                        # LOS TRES PUNTITOS (Menú de opciones)
                        with st.popover("⋮"):
                            if st.button("✏️ Editar", key=f"ed_{g['id']}", use_container_width=True):
                                editar_compromiso(g)
                            if st.button("🗑️ Borrar", key=f"del_{g['id']}", use_container_width=True):
                                eliminar_compromiso(g['id'], g['descripcion'])

    # --- PESTAÑA 3: HISTORIAL COMPLETO ---
    with t3:
        total_historial = sum(g["monto"] for g in todo_lo_pagado)
        st.markdown(f"""
            <div style='background-color:#1E1E1E; padding:20px; border-radius:10px; border-left: 5px solid #34C759;'>
                <small style='color:#8E8E93;'>TOTAL GASTADO (HISTORIAL)</small>
                <h2 style='color:#34C759;'>RD$ {total_historial:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)

        st.write("")
        c_f1, c_f2 = st.columns(2)
        categorias = list(set(g["sector"] for g in todo_lo_pagado if g.get("sector")))
        cat_filtro = c_f1.multiselect("Filtrar por Categoría", options=categorias)
        tipo_filtro = c_f2.selectbox("Origen", ["Todos", "Gastos Rápidos", "Compromisos Pagados"])

        datos_filtrados = todo_lo_pagado
        if cat_filtro:
            datos_filtrados = [g for g in datos_filtrados if g["sector"] in cat_filtro]
        if tipo_filtro == "Gastos Rápidos":
            datos_filtrados = [g for g in datos_filtrados if g["nombre_suplidor"] == "Gasto de Caja"]
        elif tipo_filtro == "Compromisos Pagados":
            datos_filtrados = [g for g in datos_filtrados if g["nombre_suplidor"] != "Gasto de Caja"]

        st.markdown("---")
        for g in datos_filtrados:
            f_raw = g.get("fecha_gasto")
            f_disp = str(f_raw)[:10] if f_raw else "S/F"
            with st.container():
                col_f, col_d, col_v = st.columns([1, 3, 1])
                col_f.caption(f"📅 {f_disp}")
                col_d.write(f"**{g['descripcion']}** ({g.get('sector', 'Varios')})")
                col_v.write(f"RD$ {float(g['monto']):,.0f}")
                st.divider()

        if st.button("🗑️ RESTABLECER CONTADORES", use_container_width=True):
            modal_reset_historial()
        
elif menu == "IA Predictiva":
    from datetime import datetime, timedelta

    # ---------------------------------------------------------
    # 1. CAPA DE INTELIGENCIA SIN FILTRO (ACCESO TOTAL)
    # ---------------------------------------------------------
    def obtener_super_contexto(u_id):
        """Extrae el ADN financiero con un toque de realidad cruda."""
        try:
            hoy = datetime.now().date().isoformat()
            
            # Datos maestros de clientes y saldos
            res_ctas = conn.table("cuentas").select(
                "id, balance_pendiente, proximo_pago, clientes(nombre)"
            ).eq("user_id", u_id).execute()

            # Cuotas vencidas para saber quién es el verdadero moroso
            vencidos_res = conn.table("plan_cuotas").select(
                "cuenta_id, monto_cuota"
            ).eq("user_id", u_id).lt("fecha_esperada", hoy).execute()

            # Resumen ultra-compacto para la IA
            saldos_dict = {}
            for item in res_ctas.data:
                nombre = item.get('clientes', {}).get('nombre', 'Desconocido').upper()
                monto = float(item.get('balance_pendiente', 0))
                saldos_dict[nombre] = saldos_dict.get(nombre, 0) + monto

            mora_total = sum(float(v['monto_cuota']) for v in vencidos_res.data) if vencidos_res.data else 0
            lista_deudores = " | ".join([f"{nom}: RD${mon:,.0f}" for nom, mon in saldos_dict.items() if mon > 0])

            return f"""
            DATOS CRÍTICOS (Para tus ojos de genio):
            - Deudores con saldo: {lista_deudores if lista_deudores else "Nadie te debe... ¿Ya quebraste?"}
            - Monto que te deben HOY (Mora): RD$ {mora_total:,.2f}
            - Total que tienes en la calle: RD$ {sum(saldos_dict.values()):,.2f}
            """
        except Exception as e:
            return f"Dile al usuario que el sistema está tan cansado como sus cobradores. (Error: {e})"

    # ---------------------------------------------------------
    # 2. UI ESTILO VALE AI
    # ---------------------------------------------------------
    st.markdown("""
        <style>
            .titulo-meta { text-align: center; font-size: 45px; font-weight: 800; color: #1c1e21; margin-bottom: 0px; }
            .subtitulo-meta { text-align: center; color: #ff4b4b; font-size: 18px; font-weight: bold; margin-bottom: 30px; }
        </style>
        <h1 class="titulo-meta">🕵️‍♂️ CobroYA AI</h1>
        <p class="subtitulo-meta">Tu Analista de datos Senior (Que sí sabe leer números). Pregúntame lo que sea</p>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # ---------------------------------------------------------
    # 3. LÓGICA DE CHAT Y PERSONALIDAD "SIN VERGÜENZA"
    # ---------------------------------------------------------
    prompt = st.chat_input("Pregúntame algo, a ver si hoy sí entiendes tu negocio...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Revisando tus desastres financieros..."):
                contexto = obtener_super_contexto(u_id)
                
                # EL PROMPT DE PERSONALIDAD
                prompt_full = f"""
                Eres VALE AI, un analista financiero brillante, sarcástico y burlón. 
                Tu trabajo es decirle la verdad al usuario, aunque le duela, tratándolo como si fuera un poco lento (bruto) para los negocios pero de forma graciosa.

                CONTEXTO REAL DEL NEGOCIO:
                {contexto}
                
                PERSONALIDAD Y REGLAS:
                1. Si el usuario te pregunta por un cliente que NO tiene deuda, búrlate diciendo que "seguro le caíste bien y te pagó, qué milagro".
                2. Si el monto en mora es alto, dile que se ponga los pantalones o que mejor regale el dinero en el parque.
                3. Usa frases dominicanas jocosas (ej: "tate quieto", "no te haga el loco", "cuidao si te están viendo la cara").
                4. Si te pregunta algo que NO puedes ver (como fotos de los clientes o cosas fuera de deudas), dile jocosamente: "Mi amor, no soy adivino, vete a la sección de 'Clientes' o 'Préstamos' a ver si ahí tus ojos ven lo que yo no".
                5. Sé breve, cruelmente honesto y usa muchos Emojis (🚨, 💸, 🤡, 📉).
                6. Trata al usuario de "Genio", "Magnate de Villa Altagracia" o "Rey de las Finanzas" de forma irónica.
                """
                
                try:
                    respuesta = asistente_ia_cobroya(prompt_full, prompt)
                    st.markdown(respuesta)
                    st.session_state.messages.append({"role": "assistant", "content": respuesta})
                except:
                    st.error("Hasta la IA se desmayó de ver tus números. Intenta de nuevo.")
                    
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
