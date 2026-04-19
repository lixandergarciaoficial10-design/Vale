import streamlit as st
import pandas as pd
from datetime import datetime
import requests
import time
import folium

from streamlit_folium import st_folium
from streamlit_js_eval import streamlit_js_eval

# Supabase
from supabase import create_client, Client

# ==============================
# 🔐 CONFIGURACIÓN
# ==============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

conn: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# 🧠 FUNCIONES BASE
# ==============================

def limpiar_sesion(keys):
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

# ==============================
# 📄 MODAL: EXPEDIENTE CLIENTE
# ==============================
@st.dialog("📄 Expediente de Facturación")
def modal_detalle(cliente, cuentas, pagos):
    hoy_dt = datetime.now().date()

    # --- CABECERA ---
    col_icon, col_data = st.columns([1, 4])
    with col_icon:
        st.markdown("<h1 style='text-align:center; margin:0;'>👤</h1>", unsafe_allow_html=True)
    with col_data:
        st.markdown(f"### {cliente['nombre']}")
        st.caption(f"🆔 Cédula: {cliente.get('cedula', 'N/A')} | 📞 {cliente.get('telefono', 'N/A')}")

    # --- DEUDA TOTAL ---
    mis_ctas = [ct for ct in cuentas if ct['cliente_id'] == cliente['id']]
    total_deuda = sum(float(ct.get('balance_pendiente', 0)) for ct in mis_ctas)

    st.markdown(f"""
        <div style="background: #1e293b; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px;">
            <p style="margin: 0; color: #94a3b8; font-size: 14px; font-weight: bold;">DEUDA TOTAL PENDIENTE</p>
            <h2 style="margin: 0; color: #ffffff; font-size: 32px; white-space: nowrap;">RD$ {total_deuda:,.2f}</h2>
        </div>
    """, unsafe_allow_html=True)

    # --- ESTADO ---
    atrasos = 0
    for ct in mis_ctas:
        if ct.get('proximo_pago'):
            if pd.to_datetime(ct['proximo_pago']).date() < hoy_dt and float(ct.get('balance_pendiente', 0)) > 0:
                atrasos += 1

    c_ctas, c_est = st.columns(2)
    c_ctas.markdown(f"<div style='background:#f3f4f6; padding:10px; border-radius:10px; text-align:center;'><small>Cuentas</small><br><b>{len(mis_ctas)} Registradas</b></div>", unsafe_allow_html=True)

    color_at = "#ef4444" if atrasos > 0 else "#10b981"
    c_est.markdown(f"<div style='background:#f3f4f6; padding:10px; border-radius:10px; text-align:center;'><small>Estado</small><br><b style='color:{color_at};'>{atrasos} Facturas en Mora</b></div>", unsafe_allow_html=True)

    st.divider()

    # --- TABLA ---
    st.markdown("#### 📅 Plan de Pagos vs. Realizado")

    if not mis_ctas:
        st.info("No hay facturas para este cliente.")
    else:
        for ct in mis_ctas:
            with st.container(border=True):
                st.markdown(f"**Factura: #{str(ct['id'])[:6].upper()}**")

                abonos_f = [p for p in pagos if p.get('cuenta_id') == ct['id']]

                if not abonos_f:
                    st.caption("No se han registrado abonos aún.")
                    df_vacio = pd.DataFrame(columns=["Fecha Cuota", "Monto Esperado", "Monto Pagado", "Estado"])
                    st.table(df_vacio)
                else:
                    data_amort = []
                    for ab in abonos_f:
                        m_pagado = float(ab.get('monto_pagado', 0))
                        m_esperado = float(ct.get('monto_inicial', 0))

                        if m_pagado >= m_esperado:
                            est = "✅ COMPLETO"
                        elif m_pagado > 0:
                            est = "🟡 PARCIAL"
                        else:
                            est = "❌ NO PAGO"

                        data_amort.append({
                            "Fecha": ab.get('fecha_pago'),
                            "Abonado": f"RD$ {m_pagado:,.2f}",
                            "Estado": est
                        })

                    st.table(pd.DataFrame(data_amort))

    # --- BOTONES ---
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        tel = "".join(filter(str.isdigit, str(cliente.get('telefono', ''))))
        st.markdown(f'''<a href="https://wa.me/{tel}" target="_blank">
            <div style="background:#25D366; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold;">WhatsApp</div>
        </a>''', unsafe_allow_html=True)

    with col2:
        lat, lon = cliente.get('latitud'), cliente.get('longitud')
        if lat and str(lat) not in ["0", "0.0", "None", ""]:
            map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            st.markdown(f'''<a href="{map_url}" target="_blank">
                <div style="background:#4285F4; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold;">Abrir Mapa</div>
            </a>''', unsafe_allow_html=True)
        else:
            st.button("📵 Sin Ubicación", disabled=True, use_container_width=True)

    if st.button("Cerrar", use_container_width=True):
        st.rerun()


# ==============================
# 🔍 FUNCIÓN DE FILTRADO (CLAVE)
# ==============================
def filtrar_clientes(clientes_db, cuentas_db, search_query, sel_filtro):
    hoy = datetime.now().date()
    clientes_f = []

    for c in clientes_db:
        cuenta = next((d for d in cuentas_db if d['cliente_id'] == c['id']), None)

        match_estado = False

        if sel_filtro == "🌍 Todos":
            match_estado = True

        elif cuenta:
            prox_pago = pd.to_datetime(cuenta.get('proximo_pago')).date() if cuenta.get('proximo_pago') else None
            balance = cuenta.get('balance_pendiente', 0)

            if sel_filtro == "🔴 Atrasados":
                if prox_pago and hoy > prox_pago and balance > 0:
                    match_estado = True

            elif sel_filtro == "🟢 Al Día":
                if balance <= 0 or (prox_pago and prox_pago > hoy):
                    if not (prox_pago and hoy > prox_pago and balance > 0):
                        match_estado = True

            elif sel_filtro == "🟡 Próximos/Hoy":
                if prox_pago:
                    dias_dif = (prox_pago - hoy).days
                    if dias_dif in [0, 1]:
                        match_estado = True

        match_search = not search_query or (
            search_query.lower() in c['nombre'].lower()
            or search_query in str(c.get('cedula', ''))
        )

        if match_search and match_estado:
            clientes_f.append(c)

    return clientes_f

# ==============================
# 💰 SECCIÓN: NUEVA CUENTA POR COBRAR
# ==============================
def seccion_nueva_cuenta(conn, u_id):

    st.header("🏢 Registro de Nueva Factura")

    contenedor_formulario = st.empty()

    # --- AUDITORÍA DE DEUDAS ---
    res_cli = conn.table("clientes").select("id, nombre, cedula, telefono").eq("user_id", u_id).execute()
    res_activas = conn.table("cuentas").select("cliente_id, balance_pendiente").eq("user_id", u_id).gt("balance_pendiente", 0).execute()

    resumen_deudas = {}
    if res_activas.data:
        for d in res_activas.data:
            c_id = d['cliente_id']
            resumen_deudas[c_id] = resumen_deudas.get(c_id, {'cantidad': 0, 'total': 0})
            resumen_deudas[c_id]['cantidad'] += 1
            resumen_deudas[c_id]['total'] += float(d['balance_pendiente'])

    # --- ÉXITO ---
    if "prestamo_exitoso" in st.session_state:

        with st.container(border=True):
            st.balloons()
            st.success(f"### ✅ ¡Préstamo Activado para {st.session_state.last_name}!")

            c1, c2, c3 = st.columns(3)

            with c1:
                st.download_button(
                    "📥 Descargar Contrato PDF",
                    data=st.session_state.pdf_ready,
                    file_name=f"Factura_{st.session_state.last_name}.pdf",
                    use_container_width=True
                )

            with c2:
                st.markdown(f'''<a href="{st.session_state.wa_link}" target="_blank">
                    <button style="width:100%; background:#25D366; color:white; border:none; padding:10px; border-radius:10px; cursor:pointer; font-weight:bold; height:45px;">
                        💬 Enviar por WhatsApp
                    </button></a>''', unsafe_allow_html=True)

            with c3:
                if st.button("🔄 Crear otra factura", use_container_width=True):
                    limpiar_sesion(["prestamo_exitoso", "pdf_ready", "wa_link", "last_name"])
                    st.rerun()

    else:
        with contenedor_formulario.container():

            if res_cli.data:

                col1, col2, col3 = st.columns(3)

                with col1:
                    cliente_obj = st.selectbox(
                        "Seleccionar Cliente",
                        options=res_cli.data,
                        format_func=lambda x: x['nombre']
                    )

                    capital = st.number_input("Capital Prestado (RD$)", min_value=0.0, step=100.0)

                    if cliente_obj['id'] in resumen_deudas:
                        info = resumen_deudas[cliente_obj['id']]
                        st.error(f"⚠️ YA DEBE: RD$ {info['total']:,.2f} en {info['cantidad']} factura(s)")
                        continuar = st.checkbox("Autorizar nueva deuda")
                    else:
                        st.success("✅ Cliente al día")
                        continuar = True

                with col2:
                    porcentaje = st.number_input("Interés (%)", min_value=0, value=20)
                    freq_sel = st.selectbox("Frecuencia", ["Semanal", "Quincenal", "Mensual"], index=2)

                with col3:
                    cuotas_n = st.number_input("Cuotas", min_value=1, value=4)
                    fecha_inicio = st.date_input("Fecha Inicio", value=datetime.now().date())

                total_esp = capital * (1 + (porcentaje / 100))
                ganancia = total_esp - capital
                monto_c = total_esp / cuotas_n if cuotas_n > 0 else 0

                # --- MÉTRICAS ---
                st.markdown("#### 📊 Proyección de Rentabilidad")

                m1, m2, m3 = st.columns(3)
                m1.metric("Inversión", f"RD$ {capital:,.2f}")
                m2.metric("Ganancia Neta", f"RD$ {ganancia:,.2f}", delta=f"{porcentaje}%")
                m3.metric("Total a Cobrar", f"RD$ {total_esp:,.2f}")

                df_p = pd.DataFrame([{
                    "Nº": i + 1,
                    "Fecha": (fecha_inicio + pd.DateOffset(
                        days=i*7 if freq_sel=="Semanal" else i*14 if freq_sel=="Quincenal" else i*30
                    )).date(),
                    "Monto Cuota (RD$)": round(monto_c, 2)
                } for i in range(cuotas_n)])

                df_e = st.data_editor(df_p, use_container_width=True, key="editor_p")
                total_f = df_e["Monto Cuota (RD$)"].sum()

                if st.button("🚀 ACTIVAR PRÉSTAMO", use_container_width=True, disabled=not (capital > 0 and continuar)):

                    # --- GUARDAR ---
                    conn.table("cuentas").insert({
                        "cliente_id": cliente_obj['id'],
                        "monto_inicial": total_f,
                        "balance_pendiente": total_f,
                        "user_id": u_id,
                        "estado": "Al Día",
                        "proximo_pago": str(df_e.iloc[0]["Fecha"])
                    }).execute()

                    # --- PDF ---
                    pdf_out = generar_pdf_contrato_legal(
                        cliente_obj['nombre'],
                        cliente_obj.get('cedula', 'S/N'),
                        float(capital),
                        float(total_f),
                        df_e,
                        freq_sel,
                        st.session_state.get("mis_clausulas", "Sujeto a términos.")
                    )

                    # --- SESSION ---
                    st.session_state.pdf_ready = pdf_out
                    st.session_state.last_name = cliente_obj['nombre']
                    st.session_state.prestamo_exitoso = True

                    # --- WHATSAPP ---
                    wa_msg = f"✅ *NUEVA FACTURA DISPONIBLE*\n\n" \
                             f"Hola {cliente_obj['nombre']},\n" \
                             f"Se ha generado tu plan de pagos:\n" \
                             f"💰 *Total:* RD$ {total_f:,.2f}\n" \
                             f"🗓️ *{cuotas_n} cuotas* de RD$ {monto_c:,.2f}\n" \
                             f"📅 *Primer pago:* {df_e.iloc[0]['Fecha']}\n\n" \
                             "Te envío el contrato legal adjunto."

                    st.session_state.wa_link = f"https://wa.me/{cliente_obj.get('telefono', '')}?text={requests.utils.quote(wa_msg)}"

                    st.rerun()

# ==============================
# 👥 SECCIÓN: CLIENTES
# ==============================
def seccion_clientes(conn, u_id):

    import datetime as dt

    hoy_dt = dt.date.today()

    # --- MEMORIA ---
    for k in ["reg_gps", "reg_nombre", "reg_tel", "reg_ced", "reg_dir"]:
        if k not in st.session_state:
            st.session_state[k] = ""

    st.markdown("<h1 style='color: #1e293b; font-size: 1.6rem;'>Gestión de Cartera</h1>", unsafe_allow_html=True)

    # ==============================
    # ✨ REGISTRO CLIENTE
    # ==============================
    with st.expander("✨ Registrar Nuevo Cliente", expanded=False):

        st.markdown("### 🛰️ Localización Satelital")

        st.caption(
            "⚠️ **Nota sobre precisión:** El GPS puede tener un margen de error de 5 a 50 metros.",
            help="Consejo: activa Wi-Fi para mayor precisión."
        )

        with st.container(border=True):

            col_gps, col_map = st.columns([1, 1.5])

            with col_gps:

                pos = streamlit_js_eval(
                    js_expressions="""
                    new Promise((resolve) => {
                        if (!navigator.geolocation) { resolve("NO_SOPORTADO"); }
                        navigator.geolocation.getCurrentPosition(
                            (p) => resolve(p.coords.latitude + "," + p.coords.longitude),
                            (e) => resolve("ERROR_" + e.code),
                            { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 }
                        )
                    })
                    """,
                    key="GPS_ENGINE_FINAL"
                )

                if st.button("🎯 CAPTURAR UBICACIÓN AHORA", use_container_width=True, type="primary"):
                    if pos and not pos.startswith("ERROR") and pos != "NO_SOPORTADO":
                        st.session_state.reg_gps = pos
                        st.success("✅ Ubicación capturada")
                        st.rerun()
                    elif pos and pos.startswith("ERROR"):
                        st.error("🚫 Error de señal. Revisa permisos.")

                st.session_state.reg_gps = st.text_input(
                    "📍 Coordenadas (Ajuste manual)",
                    value=st.session_state.reg_gps
                )

            with col_map:
                if st.session_state.reg_gps and "," in st.session_state.reg_gps:
                    try:
                        lat, lon = map(float, st.session_state.reg_gps.split(","))
                        m = folium.Map(location=[lat, lon], zoom_start=19)
                        folium.Marker([lat, lon]).add_to(m)
                        st_folium(m, height=250, use_container_width=True)
                    except:
                        st.error("Formato inválido.")
                else:
                    st.info("Captura ubicación para ver mapa.")

        # --- DATOS ---
        st.markdown("### 📝 Datos del Cliente")

        c1, c2 = st.columns(2)
        with c1:
            st.session_state.reg_nombre = st.text_input("Nombre Completo *", value=st.session_state.reg_nombre)
            st.session_state.reg_ced = st.text_input("Cédula / ID *", value=st.session_state.reg_ced)
        with c2:
            st.session_state.reg_tel = st.text_input("WhatsApp / Celular *", value=st.session_state.reg_tel)
            st.session_state.reg_dir = st.text_area("Referencia", value=st.session_state.reg_dir)

        col_b1, col_b2 = st.columns(2)

        with col_b1:
            if st.button("🧹 LIMPIAR CAMPOS", use_container_width=True):
                for k in ["reg_gps", "reg_nombre", "reg_tel", "reg_ced", "reg_dir"]:
                    st.session_state[k] = ""
                st.rerun()

        with col_b2:
            guardar = st.button("🚀 GUARDAR EN CARTERA", use_container_width=True)

        if guardar:
            if not st.session_state.reg_nombre or not st.session_state.reg_ced:
                st.error("❌ Nombre y Cédula obligatorios.")
            else:
                lat, lon = 0.0, 0.0
                if st.session_state.reg_gps:
                    try:
                        lat, lon = map(float, st.session_state.reg_gps.split(","))
                    except:
                        pass

                conn.table("clientes").insert({
                    "nombre": st.session_state.reg_nombre,
                    "telefono": st.session_state.reg_tel,
                    "cedula": st.session_state.reg_ced,
                    "direccion": st.session_state.reg_dir,
                    "latitud": lat,
                    "longitud": lon,
                    "user_id": u_id,
                    "fecha_registro": str(hoy_dt)
                }).execute()

                st.success("Cliente guardado")
                for k in ["reg_gps", "reg_nombre", "reg_tel", "reg_ced", "reg_dir"]:
                    st.session_state[k] = ""
                st.rerun()

    st.divider()

    # ==============================
    # 📊 DATOS
    # ==============================
    clientes_db = conn.table("clientes").select("*").eq("user_id", u_id).execute().data or []
    cuentas_db = conn.table("cuentas").select("*").execute().data or []
    pagos_db = conn.table("pagos").select("*").execute().data or []

    # --- FILTROS ---
    col1, col2 = st.columns([1.2, 2])
    with col1:
        search = st.text_input("🔍", placeholder="Buscar...")
    with col2:
        filtro = st.pills("Filtro", ["🌍 Todos", "🔴 Atrasados", "🟢 Al Día", "🟡 Próximos/Hoy"], default="🌍 Todos")

    # 🔥 USAMOS FUNCIÓN (YA NO HAY ERROR)
    clientes_f = filtrar_clientes(clientes_db, cuentas_db, search, filtro)

    # --- GRID ---
    if not clientes_f:
        st.warning("No hay resultados.")
        return

    grid = st.columns(3)

    for i, cl in enumerate(clientes_f):
        with grid[i % 3]:
            with st.container(border=True):

                st.markdown(f"**{cl['nombre']}**")
                st.caption(f"🆔 {cl.get('cedula', 'N/A')}")

                b1, b2, b3 = st.columns(3)

                # 📂 MODAL
                with b1:
                    if st.button("📂", key=f"h_{cl['id']}"):
                        modal_detalle(cl, cuentas_db, pagos_db)

                # 📞 WHATSAPP
                with b2:
                    tel = "".join(filter(str.isdigit, str(cl.get('telefono', ''))))
                    st.markdown(f'<a href="https://wa.me/{tel}" target="_blank">💬</a>', unsafe_allow_html=True)

                # 📍 MAPA
                with b3:
                    lat, lon = cl.get('latitud'), cl.get('longitud')
                    if lat:
                        map_url = f"https://www.google.com/maps?q={lat},{lon}"
                        st.markdown(f'<a href="{map_url}" target="_blank">📍</a>', unsafe_allow_html=True)
                    else:
                        st.write("📵")

# ==============================
# 🚀 MAIN APP (CONTROL CENTRAL)
# ==============================

st.set_page_config(page_title="Sistema de Préstamos", layout="wide")

# --- MENÚ PRINCIPAL ---
menu = st.sidebar.selectbox(
    "📌 Navegación",
    [
        "Nueva Cuenta por Cobrar",
        "👥 Todos mis Clientes",
        "Cuentas por Pagar"
    ]
)

# --- USUARIO (ajústalo si ya lo tienes definido antes) ---
# ⚠️ Si ya tienes u_id definido arriba, NO dupliques esto
try:
    u_id
except:
    u_id = "demo_user"

# ==============================
# 🔀 NAVEGACIÓN
# ==============================

if menu == "Nueva Cuenta por Cobrar":
    seccion_nueva_cuenta(conn, u_id)

elif menu == "👥 Todos mis Clientes":
    seccion_clientes(conn, u_id)

elif menu == "Cuentas por Pagar":
    st.header("🏧 Movimientos de Efectivo")

    res_p = conn.table("pagos").select("monto_pagado").eq("user_id", u_id).execute()
    res_g = conn.table("gastos").select("monto").eq("user_id", u_id).execute()

    total_pagos = sum([p['monto_pagado'] for p in res_p.data]) if res_p.data else 0
    total_gastos = sum([g['monto'] for g in res_g.data]) if res_g.data else 0

    col1, col2 = st.columns(2)
    col1.metric("💰 Ingresos", f"RD$ {total_pagos:,.2f}")
    col2.metric("💸 Gastos", f"RD$ {total_gastos:,.2f}")
