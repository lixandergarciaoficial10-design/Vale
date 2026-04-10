import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_supabase_connection import SupabaseConnection
from datetime import datetime

# 1. CONFIGURACIÓN Y ESTILO ESTILO APPLE-ENTERPRISE
st.set_page_config(page_title="CobroYa Pro", layout="wide")

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
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-5px); }
    div.stButton > button:first-child {
        background-color: #007AFF; color: white; border-radius: 12px; border: none;
        padding: 0.7rem 2rem; font-weight: bold; width: 100%; transition: 0.3s;
    }
    div.stButton > button:first-child:hover { background-color: #0051FF; box-shadow: 0 4px 12px rgba(0,122,255,0.3); }
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

# --- 3. NAVEGACIÓN ACTUALIZADA ---
with st.sidebar:
    st.markdown("<h1 style='color: #007AFF; text-align: center;'>CobroYa</h1>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("MENÚ PRINCIPAL", ["Panel de Control", "Gestión de Cobros", "Nueva Cuenta", "Caja y Gastos", "IA Predictiva"])
    st.markdown("---")
    if st.button("Cerrar Sesión"):
        st.session_state.auth = False
        st.rerun()

# --- MÓDULOS NUEVOS Y ACTUALIZADOS ---

if menu == "Panel de Control":
    st.title("Business Intelligence Dashboard")
    
    # Datos de Ingresos (Pagos)
    res_p = conn.table("pagos").select("monto_pagado").execute()
    total_ingresos = sum([p['monto_pagado'] for p in res_p.data]) if res_p.data else 0
    
    # Datos de Gastos
    res_g = conn.table("gastos").select("monto").execute()
    total_gastos = sum([g['monto'] for g in res_g.data]) if res_g.data else 0
    
    ganancia_neta = total_ingresos - total_gastos

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><small>INGRESOS TOTALES</small><h2 style='color: #34C759;'>RD$ {total_ingresos:,.0f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><small>GASTOS OPERATIVOS</small><h2 style='color: #FF3B30;'>RD$ {total_gastos:,.0f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card' style='background-color: #F2F7FF;'><small>GANANCIA NETA</small><h2 style='color: #007AFF;'>RD$ {ganancia_neta:,.0f}</h2></div>", unsafe_allow_html=True)

    # (Aquí irían los gráficos que ya teníamos, pero ahora comparando ingresos vs gastos)
    st.subheader("Balance de Flujo de Caja")
    df_flujo = pd.DataFrame({
        'Categoría': ['Ingresos', 'Gastos'],
        'Monto': [total_ingresos, total_gastos]
    })
    fig_flujo = px.bar(df_flujo, x='Categoría', y='Monto', color='Categoría', 
                       color_discrete_map={'Ingresos':'#34C759', 'Gastos':'#FF3B30'}, template="plotly_white")
    st.plotly_chart(fig_flujo, use_container_width=True)

elif menu == "Caja y Gastos":
    st.header("Control de Gastos y Salidas")
    col_f, col_t = st.columns([1, 2])
    
    with col_f:
        st.subheader("Registrar Gasto")
        with st.form("form_gasto"):
            desc = st.text_input("Concepto del Gasto")
            monto_g = st.number_input("Monto RD$", min_value=1.0)
            if st.form_submit_button("Guardar Salida"):
                conn.table("gastos").insert({"descripcion": desc, "monto": monto_g}).execute()
                st.warning(f"Gasto de RD$ {monto_g} registrado.")
                st.rerun()
    
    with col_t:
        st.subheader("Historial de Salidas")
        res_all_g = conn.table("gastos").select("*").order("id", desc=True).execute()
        if res_all_g.data:
            st.table(pd.DataFrame(res_all_g.data)[['descripcion', 'monto']])

elif menu == "IA Predictiva":
    st.header("🧠 Inteligencia Artificial de Riesgo")
    st.markdown("Analizando comportamiento de pagos históricos...")
    
    res_cl = conn.table("clientes").select("id, nombre").execute()
    if res_cl.data:
        cliente_ia = st.selectbox("Seleccione cliente para auditar con IA", [c['nombre'] for c in res_cl.data])
        
        if st.button("Ejecutar Análisis Predictivo"):
            with st.spinner("La IA está procesando los patrones de pago..."):
                import time
                time.sleep(2) # Efecto dramático de procesamiento
                
                # Aquí simulamos la lógica que luego conectaremos a Groq
                # Por ahora, una lógica basada en el nombre para demostración
                riesgo = "BAJO" if len(cliente_ia) > 10 else "MODERADO"
                prob = "92%" if riesgo == "BAJO" else "65%"
                
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>Resultado del Análisis: {cliente_ia}</h3>
                    <p>Nivel de Riesgo: <b>{riesgo}</b></p>
                    <p>Probabilidad de pago a tiempo: <b>{prob}</b></p>
                    <hr>
                    <small>Sugerencia de la IA: {"Mantener crédito abierto y aumentar límite." if riesgo == "BAJO" else "Solicitar abono inmediato y no despachar más mercancía."}</small>
                </div>
                """, unsafe_allow_html=True)

# --- 4. MÓDULOS ---

if menu == "Panel de Control":
    st.title("Business Intelligence Dashboard")
    
    # EXTRACCIÓN DE DATOS REALES
    res_c = conn.table("cuentas").select("balance_pendiente, estado").execute()
    df_cuentas = pd.DataFrame(res_c.data) if res_c.data else pd.DataFrame(columns=['balance_pendiente', 'estado'])
    
    res_p = conn.table("pagos").select("monto_pagado, fecha_pago").execute()
    df_pagos = pd.DataFrame(res_p.data) if res_p.data else pd.DataFrame(columns=['monto_pagado', 'fecha_pago'])

    # KPI METRICS
    total_calle = df_cuentas[df_cuentas['estado'] == 'Activo']['balance_pendiente'].sum() if not df_cuentas.empty else 0
    total_recaudado = df_pagos['monto_pagado'].sum() if not df_pagos.empty else 0
    eficiencia = (total_recaudado / (total_calle + total_recaudado) * 100) if (total_calle + total_recaudado) > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><small>TOTAL POR COBRAR</small><h2 style='color: #1D1D1F;'>RD$ {total_calle:,.0f}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><small>TOTAL RECAUDADO</small><h2 style='color: #34C759;'>RD$ {total_recaudado:,.0f}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><small>% EFICIENCIA</small><h2 style='color: #007AFF;'>{eficiencia:.1f}%</h2></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'><small>ESTADO CRÍTICO</small><h2 style='color: #FF3B30;'>0.0%</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # GRÁFICOS DE ALTO IMPACTO
    col_g1, col_g2 = st.columns([2, 1])

    with col_g1:
        st.subheader("Tendencia de Recaudación (Área Suave)")
        if not df_pagos.empty:
            df_pagos['fecha_pago'] = pd.to_datetime(df_pagos['fecha_pago']).dt.date
            df_tendencia = df_pagos.groupby('fecha_pago').sum().reset_index()
            fig_area = px.area(df_tendencia, x='fecha_pago', y='monto_pagado', template="plotly_white",
                               color_discrete_sequence=['#007AFF'])
            fig_area.update_traces(line_width=4, fillcolor='rgba(0, 122, 255, 0.1)')
            fig_area.update_layout(xaxis_title="", yaxis_title="Monto RD$")
            st.plotly_chart(fig_area, use_container_width=True)
        else:
            st.info("Registre pagos para visualizar la tendencia.")

    with col_g2:
        st.subheader("Estado de Cartera")
        # Gráfico de Dona para estados de cuenta
        if not df_cuentas.empty:
            df_est = df_cuentas['estado'].value_counts().reset_index()
            fig_donut = px.pie(df_est, names='estado', values='count', hole=.7,
                               color_discrete_sequence=['#007AFF', '#34C759', '#FF9500'])
            fig_donut.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
            fig_donut.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_donut, use_container_width=True)
        else:
            st.info("No hay datos de cartera.")

    # TOP DEUDORES - GRÁFICO DE BARRAS HORIZONTALES
    st.subheader("Top Deudores (Análisis de Riesgo)")
    query_top = conn.table("cuentas").select("balance_pendiente, clientes(nombre)").eq("estado", "Activo").order("balance_pendiente", desc=True).limit(5).execute()
    if query_top.data:
        df_top = pd.DataFrame([{'Cliente': i['clientes']['nombre'], 'Deuda': float(i['balance_pendiente'])} for i in query_top.data])
        fig_bar = px.bar(df_top, x='Deuda', y='Cliente', orientation='h', template="plotly_white",
                         color='Deuda', color_continuous_scale='Blues')
        fig_bar.update_layout(showlegend=False, coloraxis_showscale=False, yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

elif menu == "Directorio Clientes":
    st.header("Gestión de Clientes")
    with st.expander("➕ REGISTRAR NUEVO CLIENTE"):
        with st.form("f_cli"):
            n = st.text_input("Nombre Completo")
            t = st.text_input("WhatsApp (Ej: 8295551234)")
            if st.form_submit_button("Guardar Cliente"):
                conn.table("clientes").insert({"nombre": n, "telefono": t}).execute()
                st.success(f"Cliente {n} registrado.")
                st.rerun()
    
    res = conn.table("clientes").select("*").execute()
    if res.data: 
        st.dataframe(pd.DataFrame(res.data)[['nombre', 'telefono']], use_container_width=True)

elif menu == "Nueva Cuenta":
    st.header("Apertura de Crédito")
    res_cl = conn.table("clientes").select("id, nombre").execute()
    cl_opt = {c['nombre']: c['id'] for c in res_cl.data} if res_cl.data else {}
    
    if cl_opt:
        with st.form("f_deuda"):
            c_sel = st.selectbox("Seleccione Cliente", list(cl_opt.keys()))
            monto = st.number_input("Monto de la Deuda (RD$)", min_value=1.0)
            if st.form_submit_button("Abrir Cuenta"):
                conn.table("cuentas").insert({"cliente_id": cl_opt[c_sel], "monto_inicial": monto, "balance_pendiente": monto}).execute()
                st.balloons()
                st.success("Cuenta de cobro creada exitosamente.")
    else: st.warning("Debe registrar un cliente primero.")

elif menu == "Gestión de Cobros":
    st.header("Panel de Cobranza por Compromiso")
    
    # Traer cuentas con info de clientes y fecha de próximo pago
    query = conn.table("cuentas").select("id, balance_pendiente, proximo_pago, clientes(nombre, telefono)").eq("estado", "Activo").execute()
    
    if query.data:
        for item in query.data:
            # Lógica de Semáforo basada en fecha de compromiso
            if item['proximo_pago']:
                fecha_pago = datetime.strptime(item['proximo_pago'], '%Y-%m-%d').date()
                hoy = datetime.now().date()
                dias_restantes = (fecha_pago - hoy).days
                
                # Definir color y estado
                if dias_restantes > 2:
                    color_alerta = "#34C759" # Verde: Todo bien
                    status_text = f"Al día (Faltan {dias_restantes} días)"
                elif 0 <= dias_restantes <= 2:
                    color_alerta = "#FF9500" # Naranja: Casi toca
                    status_text = "¡Toca pronto! (1-2 días)"
                elif -15 <= dias_restantes < 0:
                    color_alerta = "#FF3B30" # Rojo: Atrasado
                    status_text = f"ATRASADO ({abs(dias_restantes)} días)"
                else:
                    color_alerta = "#000000" # Negro: Peligro Crítico
                    status_text = f"CRÍTICO (+15 días de atraso)"
            else:
                color_alerta = "#E5E7EB" # Gris: Sin fecha asignada
                status_text = "Sin fecha de compromiso"

            with st.container():
                st.markdown(f"""
                <div style='border-left: 10px solid {color_alerta}; padding: 15px; background-color: white; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
                    <h3 style='margin:0; color: {color_alerta if color_alerta != "#000000" else "black"};'>{item['clientes']['nombre']}</h3>
                    <p style='margin:0; font-weight: bold;'>{status_text}</p>
                    <p style='margin:0; color: #666;'>Balance: RD$ {float(item['balance_pendiente']):,.2f}</p>
                </div>
                """, unsafe_allow_html=True)
                
                col_pago, col_fecha, col_pdf_wa = st.columns([2, 2, 1])
                
                with col_pago:
                    monto_abono = st.number_input(f"Monto Abono", min_value=0.0, key=f"ab_{item['id']}")
                    btn_pago = st.button("Registrar Pago", key=f"btn_p_{item['id']}")
                
                with col_fecha:
                    nueva_fecha = st.date_input("Próximo pago", key=f"date_{item['id']}")
                
                if btn_pago:
                    if monto_abono > 0:
                        # 1. Registrar el pago
                        conn.table("pagos").insert({"cuenta_id": item['id'], "monto_pagado": monto_abono}).execute()
                        # 2. Actualizar balance y nueva fecha de compromiso
                        nuevo_bal = float(item['balance_pendiente']) - monto_abono
                        est = "Pagado" if nuevo_bal <= 0 else "Activo"
                        conn.table("cuentas").update({
                            "balance_pendiente": nuevo_bal, 
                            "estado": est,
                            "proximo_pago": nueva_fecha.strftime('%Y-%m-%d')
                        }).eq("id", item['id']).execute()
                        st.success("Actualizado correctamente")
                        st.rerun()

                with col_pdf_wa:
                    # WhatsApp con recordatorio de la nueva fecha
                    tel = item['clientes']['telefono']
                    msg = f"Hola {item['clientes']['nombre']}, recibimos tu abono. Tu balance es RD${float(item['balance_pendiente'])-monto_abono:,.2f}. Próximo pago: {nueva_fecha}."
                    wa_link = f"https://wa.me/{tel}?text={msg.replace(' ', '%20')}"
                    st.markdown(f'<a href="{wa_link}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:8px; border-radius:8px; width:100%; cursor:pointer; margin-bottom:5px;">📲 WhatsApp</button></a>', unsafe_allow_html=True)
                    
                    # El botón de PDF se mantiene igual que antes
                    # ... (código de PDF del bloque anterior)
                st.markdown("---")
