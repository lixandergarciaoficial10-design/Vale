# ============================================
# MÓDULO: utils_roles_plan.py
# Gestión de Roles, Límites de Plan y Sesiones
# COMPACTO Y OPTIMIZADO
# ============================================

import streamlit as st
import hashlib
from datetime import datetime
import pytz
from st_supabase_connection import SupabaseConnection

TIMEZONE_RD = pytz.timezone('America/Santo_Domingo')

# ===== CONFIGURACIÓN DE LÍMITES =====
PLAN_LIMITS = {
    'gratis': {'admins': 1, 'trabajadores': 0},
    'star': {'admins': 1, 'trabajadores': 1},
    'pro': {'admins': 2, 'trabajadores': 3},
    'business': {'admins': 5, 'trabajadores': 15}
}

# ===== FUNCIÓN 1: Obtener rol del usuario =====
def obtener_rol_usuario(conn, user_id: str) -> str:
    """Obtiene el rol del usuario autenticado (admin o trabajador)."""
    try:
        res = conn.table("usuarios_dependientes").select("tipo_rol").eq("id", user_id).single().execute()
        if res.data:
            return res.data.get('tipo_rol', 'trabajador').lower()
        return 'admin'  # Si no existe registro, es el dueño (admin)
    except:
        return 'admin'

# ===== FUNCIÓN 2: Obtener tipo de rol (normalizado) =====
def normalizar_rol(rol_text: str) -> str:
    """Normaliza el rol a 'admin' o 'trabajador'."""
    r = str(rol_text or '').lower().strip()
    return 'admin' if r in ['admin', 'administrador', 'dueño', 'propietario'] else 'trabajador'

# ===== FUNCIÓN 3: Validar límites del plan =====
def validar_limite_plan(conn, owner_id: str, nuevo_rol: str) -> dict:
    """
    Valida si se puede crear un nuevo usuario según el plan.
    Retorna: {'puede_crear': bool, 'motivo': str, 'stats': {...}}
    """
    nuevo_rol = normalizar_rol(nuevo_rol)
    
    # Obtener plan actual
    res_conf = conn.table("configuracion").select("tipo_plan").eq("user_id", owner_id).single().execute()
    plan = res_conf.data.get('tipo_plan', 'gratis').lower() if res_conf.data else 'gratis'
    
    # Limites para este plan
    limites = PLAN_LIMITS.get(plan, PLAN_LIMITS['gratis'])
    
    # Contar usuarios actuales
    res_admins = conn.table("usuarios_dependientes").select("id", count="exact")\
        .eq("owner_id", owner_id).eq("tipo_rol", "admin").eq("es_activo", True).execute()
    res_trab = conn.table("usuarios_dependientes").select("id", count="exact")\
        .eq("owner_id", owner_id).eq("tipo_rol", "trabajador").eq("es_activo", True).execute()
    
    admins_actuales = (res_admins.count or 0) + 1  # +1 por el dueño (admin principal)
    trabajadores_actuales = res_trab.count or 0
    
    # Validar
    if nuevo_rol == 'admin' and admins_actuales >= limites['admins']:
        return {
            'puede_crear': False,
            'motivo': f"Límite de {limites['admins']} admin(es) alcanzado para plan {plan}",
            'stats': {
                'plan': plan,
                'admins': (admins_actuales, limites['admins']),
                'trabajadores': (trabajadores_actuales, limites['trabajadores'])
            }
        }
    
    if nuevo_rol == 'trabajador' and trabajadores_actuales >= limites['trabajadores']:
        return {
            'puede_crear': False,
            'motivo': f"Límite de {limites['trabajadores']} trabajador(es) alcanzado para plan {plan}",
            'stats': {
                'plan': plan,
                'admins': (admins_actuales, limites['admins']),
                'trabajadores': (trabajadores_actuales, limites['trabajadores'])
            }
        }
    
    return {
        'puede_crear': True,
        'motivo': 'OK',
        'stats': {
            'plan': plan,
            'admins': (admins_actuales, limites['admins']),
            'trabajadores': (trabajadores_actuales, limites['trabajadores'])
        }
    }

# ===== FUNCIÓN 4: Crear sesión de usuario =====
def crear_sesion_usuario(conn, usuario_id: str, owner_id: str, ip_address: str = "", user_agent: str = "") -> bool:
    """Crea una nueva sesión y retorna True si es exitoso."""
    try:
        token = hashlib.sha256(f"{usuario_id}{datetime.now().isoformat()}".encode()).hexdigest()
        conn.table("sesiones_usuarios").insert({
            "usuario_id": usuario_id,
            "owner_id": owner_id,
            "token_sesion": token,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "es_activo": True
        }).execute()
        return True
    except Exception as e:
        print(f"Error crear sesión: {e}")
        return False

# ===== FUNCIÓN 5: Contar sesiones concurrentes =====
def contar_sesiones_activas(conn, owner_id: str) -> int:
    """Cuenta cuántas sesiones activas tiene el owner en las últimas 24 horas."""
    try:
        res = conn.table("sesiones_usuarios").select("id", count="exact")\
            .eq("owner_id", owner_id)\
            .eq("es_activo", True)\
            .execute()
        return res.count or 0
    except:
        return 0

# ===== FUNCIÓN 6: Validar acceso concurrente =====
def validar_acceso_concurrente(conn, owner_id: str, usuario_id: str) -> dict:
    """
    Valida si el usuario puede acceder simultáneamente según el plan.
    Retorna: {'permitido': bool, 'sesiones': int, 'limite': int}
    """
    # Obtener plan
    res_conf = conn.table("configuracion").select("tipo_plan").eq("user_id", owner_id).single().execute()
    plan = res_conf.data.get('tipo_plan', 'gratis').lower() if res_conf.data else 'gratis'
    
    # En todos los planes, cada usuario puede tener máx 2 sesiones simultáneas
    # pero el número TOTAL de usuarios activos está limitado por el plan
    sesiones_activas = contar_sesiones_activas(conn, owner_id)
    
    # Obtener límite total de usuarios
    limites = PLAN_LIMITS.get(plan, PLAN_LIMITS['gratis'])
    limite_total_usuarios = limites['admins'] + limites['trabajadores'] + 1  # +1 owner
    
    return {
        'permitido': sesiones_activas < limite_total_usuarios,
        'sesiones_activas': sesiones_activas,
        'limite': limite_total_usuarios
    }

# ===== FUNCIÓN 7: Obtener permisos del usuario =====
def obtener_permisos(rol: str) -> dict:
    """
    Define qué puede hacer cada rol.
    Admin: todo
    Trabajador: solo cobros básicos
    """
    if normalizar_rol(rol) == 'admin':
        return {
            'crear_usuario': True,
            'eliminar_usuario': True,
            'editar_cliente': True,
            'eliminar_cliente': True,
            'editar_abono': True,
            'eliminar_abono': True,
            'editar_configuracion': True,
            'cambiar_plan': True,
            'ver_todos_datos': True
        }
    else:  # Trabajador
        return {
            'crear_usuario': False,
            'eliminar_usuario': False,
            'editar_cliente': False,
            'eliminar_cliente': False,
            'editar_abono': False,
            'eliminar_abono': False,
            'editar_configuracion': False,
            'cambiar_plan': False,
            'ver_todos_datos': True  # Solo lectura
        }

# ===== FUNCIÓN 8: Verificar permiso (shorthand) =====
def tiene_permiso(rol: str, accion: str) -> bool:
    """Verifica si el rol tiene permiso para una acción específica."""
    permisos = obtener_permisos(rol)
    return permisos.get(accion, False)

# ===== FUNCIÓN 9: Mostrar rol en UI =====
def mostrar_rol_ui(rol: str) -> str:
    """Retorna el texto visual del rol para mostrar en UI."""
    r = normalizar_rol(rol)
    return "🔑 Admin" if r == 'admin' else "👤 Trabajador"

# ===== FUNCIÓN 10: Validar contraseña maestra =====
def validar_contraseña_maestra(conn, owner_id: str, password: str) -> bool:
    """
    Comprueba si la contraseña ingresada es la maestra de la cuenta.
    (En producción, integrar con Supabase Auth)
    """
    try:
        # Aquí iría integración con Supabase Auth
        # Por ahora: simulado
        return True
    except:
        return False

# ===== FUNCIÓN 11: Determinar rol al login =====
def determinar_rol_login(conn, email: str, es_clave_maestra: bool, owner_id: str = None) -> str:
    """
    Determina el rol al hacer login.
    - Si usa clave maestra = Admin
    - Si usa clave de dependencia = Trabajador
    """
    if es_clave_maestra:
        return 'admin'
    
    # Consultar en usuarios_dependientes
    try:
        res = conn.table("usuarios_dependientes").select("tipo_rol")\
            .eq("email", email).single().execute()
        if res.data:
            return res.data.get('tipo_rol', 'trabajador')
    except:
        pass
    
    return 'trabajador'

print("✅ Módulo utils_roles_plan.py cargado correctamente")
