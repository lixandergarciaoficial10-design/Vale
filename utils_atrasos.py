# ============================================
# MÓDULO: utils_atrasos.py
# Cálculo Correcto de Atrasos y Filtros de Cobros
# COMPACTO Y OPTIMIZADO
# ============================================

import pandas as pd
from datetime import datetime, date, timedelta
import pytz

TIMEZONE_RD = pytz.timezone('America/Santo_Domingo')

def obtener_fecha_hoy():
    """Obtiene HOY en zona horaria República Dominicana."""
    return datetime.now(TIMEZONE_RD).date()

# ===== FUNCIÓN 1: Normalizar estado de cuota =====
def normalizar_estado_cuota(estado: str) -> str:
    """Convierte cualquier variante de estado a: 'pagada', 'incompleta' o 'pendiente'."""
    e = str(estado or '').lower().strip()
    if e in ['completa', 'completada', 'pagada']:
        return 'pagada'
    elif e in ['incompleta', 'parcial', 'partial']:
        return 'incompleta'
    else:
        return 'pendiente'

# ===== FUNCIÓN 2: Analizar cuotas de una cuenta =====
def analizar_cuotas_cuenta(conn, cuenta_id: str, hoy: date = None) -> dict:
    """
    Analiza TODAS las cuotas de una cuenta y retorna estado consolidado.
    
    Retorna dict con:
    - todas_pagadas: bool
    - cuotas_vencidas: list de dates
    - proxima_cuota_sin_vencer: date o None
    - cuota_hoy: date o None
    - cuotas_proximo_7_dias: list de dates
    - dias_atraso: int o None
    - estado_cobranza: 'al_dia', 'atrasado', 'urgente'
    """
    
    if hoy is None:
        hoy = obtener_fecha_hoy()
    
    try:
        res = conn.table("plan_cuotas").select("fecha_esperada, estado")\
            .eq("cuenta_id", cuenta_id).order("numero_cuota").execute()
        cuotas = res.data if res.data else []
    except:
        return {
            'todas_pagadas': True,
            'cuotas_vencidas': [],
            'proxima_cuota_sin_vencer': None,
            'cuota_hoy': None,
            'cuotas_proximo_7_dias': [],
            'dias_atraso': None,
            'estado_cobranza': 'al_dia',
            'proxima_fecha': None
        }
    
    todas_pagadas = True
    cuotas_vencidas = []
    proxima_cuota_sin_vencer = None
    cuota_hoy = None
    cuotas_proximo_7_dias = []
    
    for cuota in cuotas:
        fecha = pd.to_datetime(cuota['fecha_esperada']).date()
        estado = normalizar_estado_cuota(cuota.get('estado', ''))
        
        # ⚠️ LÓGICA CLAVE: Solo procesar si NO está pagada
        if estado == 'pagada':
            continue
        
        todas_pagadas = False
        
        # ✅ ATRASO REAL: fecha pasada + cuota sin pagar
        if fecha < hoy:
            cuotas_vencidas.append(fecha)
        
        # ✅ HOY: cuota para hoy
        elif fecha == hoy:
            cuota_hoy = fecha
            if proxima_cuota_sin_vencer is None:
                proxima_cuota_sin_vencer = fecha
        
        # ✅ PRÓXIMOS 7 DÍAS
        elif hoy < fecha <= (hoy + timedelta(days=7)):
            cuotas_proximo_7_dias.append(fecha)
            if proxima_cuota_sin_vencer is None:
                proxima_cuota_sin_vencer = fecha
        
        # ✅ FUTURA: más allá de 7 días
        else:
            if proxima_cuota_sin_vencer is None:
                proxima_cuota_sin_vencer = fecha
    
    # Determinar estado de cobranza
    dias_atraso = None
    estado_cobranza = 'al_dia'
    
    if cuotas_vencidas:
        dias_atraso = (hoy - min(cuotas_vencidas)).days
        estado_cobranza = 'urgente' if dias_atraso >= 15 else 'atrasado'
    
    return {
        'todas_pagadas': todas_pagadas,
        'cuotas_vencidas': cuotas_vencidas,
        'proxima_cuota_sin_vencer': proxima_cuota_sin_vencer,
        'cuota_hoy': cuota_hoy,
        'cuotas_proximo_7_dias': cuotas_proximo_7_dias,
        'dias_atraso': dias_atraso,
        'estado_cobranza': estado_cobranza,
        'proxima_fecha': proxima_cuota_sin_vencer
    }

# ===== FUNCIÓN 3: Categorizar cliente según filtro =====
def categorizar_cliente(analisis: dict, hoy: date = None) -> str:
    """
    Basado en el análisis, retorna la categoría del cliente para filtros.
    Opciones: '🟢 Al Día', '🔥 Urgentes', '🚨 Atrasados', '📅 Cobrarles Hoy', '⏳ Próx. 7 Días'
    """
    if analisis['estado_cobranza'] == 'al_dia' and not analisis['cuota_hoy']:
        return '🟢 Al Día'
    elif analisis['estado_cobranza'] == 'urgente':
        return '🔥 Urgentes'
    elif analisis['estado_cobranza'] == 'atrasado':
        return '🚨 Atrasados'
    elif analisis['cuota_hoy']:
        return '📅 Cobrarles Hoy'
    elif analisis['cuotas_proximo_7_dias']:
        return '⏳ Próx. 7 Días'
    else:
        return '📋 Todos'

# ===== FUNCIÓN 4: Verificar si pasa filtro =====
def pasa_filtro(categoria: str, filtro_seleccionado: str) -> bool:
    """Verifica si la categoría del cliente cumple con el filtro seleccionado."""
    if filtro_seleccionado == '📋 Todos':
        return True
    return categoria == filtro_seleccionado

# ===== FUNCIÓN 5: Calcular prioridad para ordenamiento =====
def calcular_prioridad(analisis: dict, balance: float = 0, hoy: date = None) -> int:
    """Calcula score de prioridad para ordenar clientes (mayor = más urgente)."""
    if hoy is None:
        hoy = obtener_fecha_hoy()
    
    dias = analisis['dias_atraso'] or 0
    estado = analisis['estado_cobranza']
    
    if estado == 'urgente':
        return 1000 + dias  # Urgentes primero
    elif estado == 'atrasado':
        return 900 + dias   # Atrasados segundo
    elif analisis['cuota_hoy']:
        return 500          # Hoy tercero
    elif analisis['cuotas_proximo_7_dias']:
        dias_prox = (min(analisis['cuotas_proximo_7_dias']) - hoy).days
        return 400 - dias_prox
    else:
        return 0

# ===== FUNCIÓN 6: Formatear texto de atraso =====
def formatear_atraso(dias: int = None) -> str:
    """Convierte días en texto amigable."""
    if dias is None or dias <= 0:
        return "Al día"
    
    if dias < 30:
        return f"{dias} día{'s' if dias != 1 else ''}"
    elif dias < 365:
        meses = dias // 30
        dias_rest = dias % 30
        return f"{meses} mes{'es' if meses != 1 else ''} y {dias_rest} día{'s' if dias_rest != 1 else ''}"
    else:
        años = dias // 365
        meses = (dias % 365) // 30
        return f"{años} año{'s' if años != 1 else ''} y {meses} mes{'es' if meses != 1 else ''}"

# ===== FUNCIÓN 7: Procesar lista de clientes para UI =====
def procesar_clientes_filtrados(conn, res_cuentas: list, filtro: str = "📋 Todos", busqueda: str = "", hoy: date = None) -> list:
    """
    Procesa todas las cuentas, las analiza, las filtra y ordena.
    Retorna lista lista de dicts con datos aumentados para la UI.
    """
    if hoy is None:
        hoy = obtener_fecha_hoy()
    
    datos_procesados = []
    
    for cuenta in res_cuentas:
        nombre = cuenta.get('clientes', {}).get('nombre', 'Cliente')
        cedula = cuenta.get('clientes', {}).get('cedula', '')
        telefono = cuenta.get('clientes', {}).get('telefono', '')
        
        # Búsqueda
        if busqueda:
            if busqueda not in nombre.lower() and \
               busqueda not in str(cedula).lower() and \
               busqueda not in str(telefono).lower():
                continue
        
        # Analizar cuotas
        analisis = analizar_cuotas_cuenta(conn, cuenta['id'], hoy)
        categoria = categorizar_cliente(analisis, hoy)
        
        # Filtro
        if not pasa_filtro(categoria, filtro):
            continue
        
        # Aumentar datos
        cuenta['_aux_nombre'] = nombre
        cuenta['_aux_categoria'] = categoria
        cuenta['_aux_dias_atraso'] = analisis['dias_atraso'] or 0
        cuenta['_aux_txt_atraso'] = formatear_atraso(analisis['dias_atraso'])
        cuenta['_aux_proxima_fecha'] = analisis['proxima_fecha']
        cuenta['_aux_proxima_dias'] = (analisis['proxima_fecha'] - hoy).days if analisis['proxima_fecha'] else 999
        cuenta['_aux_prioridad'] = calcular_prioridad(analisis, cuenta.get('balance_pendiente', 0), hoy)
        cuenta['_aux_analisis'] = analisis
        
        datos_procesados.append(cuenta)
    
    # Ordenar por prioridad (descendente)
    datos_procesados = sorted(datos_procesados, key=lambda x: x['_aux_prioridad'], reverse=True)
    
    return datos_procesados

print("✅ Módulo utils_atrasos.py cargado correctamente")
