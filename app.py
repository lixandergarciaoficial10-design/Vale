import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from st_supabase_connection import SupabaseConnection

# 1. CONFIGURACIÓN DE PÁGINA PROFESIONAL
st.set_page_config(page_title="CobroYa - Gestión Financiera", layout="wide")

# 2. ESTILO CSS (Apple-Clean / Luxury White)
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    div.stButton > button:first-child {
        background-color: #007AFF; color: white; border-radius: 12px; border: none;
        padding: 0.6rem 2.5rem; font-weight: bold; transition: 0.3s;
    }
    div.stButton > button:first-child:hover { background-color: #0056b3; }
    .metric-card {
        background-color: white; padding: 25px; border-radius: 18px;
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); border: 1px solid #EDEDED;
    }
    h1, h2, h3 { color: #1D1D1F; font-family: 'Helvetica Neue', Helvetica, sans-serif; letter-spacing: -0.5px; }
    .stTable { background-color: white; border-radius: 12px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# 3. CONEXIÓN A SUPABASE
conn = st.connection("supabase", type=SupabaseConnection)

# 4. LÓGICA DE DATOS (Métricas dinámicas)
def get_stats():
    # Sumar balance pendiente de todas las cuentas activas
    res = conn.table("cuentas").select("balance_pendiente").eq("estado", "Activo").execute()
    total_calle = sum([float(c['balance_pendiente']) for c in res.data]) if res.data else 0.0
    
    # Contar clientes únicos
    res_cli = conn.table("clientes").select("id", count="exact").execute()
    total_cli = res_cli.count if res_cli.count else 0
    
    return {
        'Total en Calle': total_calle,
        'Cobros Hoy': total_calle * 0.08, # Simulación de flujo diario
        'Clientes Activos': total_cli,
        'Recuperación': 92
    }

# 5. SIDEBAR (Navegación)
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #007AFF;'>CobroYa</h1>", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("MENÚ PRINCIPAL", ["Panel de Control", "Clientes", "Nueva Cuenta", "Reportes"])
    st.markdown("---")
    st.caption("Lixander García | Business Intelligence")
    st.caption("Versión 1.0.0 Pro")

# --- MÓDULO 1: PANEL DE CONTROL ---
if menu == "Panel de Control":
    st.header("Resumen Ejecutivo")
    stats = get_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='metric-card'>💰<br><small>TOTAL EN CALLE</small><br><h2>RD$ {stats['Total en Calle']:,.2f}</h2></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'>📅<br><small>PROYECCIÓN HOY</small><br><h2 style='color: #007AFF;'>RD$ {stats['Cobros Hoy']:,.2f}</h2></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'>👥<br><small>CARTERA CLIENTES</small><br><h2>{stats['Clientes Activos']}</h2></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='metric-card'>📈<br><small>% RECUPERACIÓN</small><br><h2 style='color: #34C759;'>{stats['Recuperación']}%</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.subheader("Rendimiento Semanal")
        df_ventas = pd.DataFrame({
            'Día': ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom'],
            'Recaudado': [12000, 15000, 8000, 22000, 19000, 30000, 5000]
        })
        fig_line = px.line(df_ventas, x='Día', y='Recaudado', template="plotly_white", color_discrete_sequence=['#007AFF'])
        fig_line.update_traces(line_width=4, mode='lines+markers', marker=dict(size=10))
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        st.subheader("Estado de Cartera")
        fig_pie = px.pie(names=['Al día', 'Atrasado', 'Vencido'], values=[75, 15, 10], hole=.6,
                         color_discrete_sequence=['#34C759', '#FF9500', '#FF3B30'])
        fig_pie.update_layout(showlegend=False, margin=dict(t=0, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

# --- MÓDULO 2: CLIENTES ---
elif menu == "Clientes":
    st.header("Directorio de Clientes")
    
    with st.expander("➕ REGISTRAR NUEVO CLIENTE", expanded=False):
        with st.form("nuevo_cliente_form"):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre Completo")
            cedula = c2.text_input("Cédula / ID")
            tel = c1.text_input("WhatsApp (Sin guiones)")
            dir = c2.text_input("Dirección / Sector")
            if st.form_submit_button("Guardar en Base de Datos"):
                if nombre and tel:
                    conn.table("clientes").insert({"nombre": nombre, "cedula": cedula, "telefono": tel, "direccion": dir}).execute()
                    st.success(f"Cliente {nombre} registrado exitosamente.")
                    st.rerun()

    res_c = conn.table("clientes").select("*").order("nombre").execute()
    if res_c.data:
        df_c = pd.DataFrame(res_c.data)
        st.dataframe(df_c[['nombre', 'cedula', 'telefono', 'direccion']], use_container_width=True)
    else:
        st.info("No hay clientes registrados aún.")

# --- MÓDULO 3: NUEVA CUENTA ---
elif menu == "Nueva Cuenta":
    st.header("Apertura de Crédito / Fiao")
    
    res_cl = conn.table("clientes").select("id, nombre").execute()
    cl_map = {c['nombre']: c['id'] for c in res_cl.data} if res_cl.data else {}

    if not cl_map:
        st.warning("Debe registrar un cliente antes de abrir una cuenta.")
    else:
        with st.form("form_nueva_deuda"):
            cliente_sel = st.selectbox("Seleccione el Cliente", list(cl_map.keys()))
            monto_fiao = st.number_input("Monto a Cobrar (RD$)", min_value=1.0)
            fecha_pago = st.date_input("Fecha de Compromiso / Primer Pago")
            nota_fiao = st.text_area("Concepto (Ej: Venta 4 gomas nuevas)")
            
            if st.form_submit_button("GENERAR CUENTA DE COBRO"):
                nueva_f = {
                    "cliente_id": cl_map[cliente_sel],
                    "monto_inicial": monto_fiao,
                    "balance_pendiente": monto_fiao,
                    "proximo_pago": str(fecha_pago),
                    "notas": nota_fiao
                }
                conn.table("cuentas").insert(nueva_f).execute()
                st.balloons()
                st.success(f"Cuenta creada para {cliente_sel} por RD$ {monto_fiao:,.2f}")

# --- MÓDULO 4: REPORTES ---
elif menu == "Reportes":
    st.header("Centro de Reportes")
    st.markdown("<div class='metric-card'>Próximamente: Exportación de balances en PDF y cierre de caja mensual.</div>", unsafe_allow_html=True)
