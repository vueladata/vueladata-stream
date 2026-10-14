import random
import uuid
from datetime import datetime, timedelta, timezone

# Catálogo de causas válidas simuladas
CAUSAS_VALIDAS = ["TECNICA", "CLIMA", "TRIPULACION", "OPERACIONAL"]

def generar_vuelos_base(cantidad):
    """Genera un listado en memoria de vuelos programados para hoy."""
    vuelos = []
    hora_actual = datetime.now(timezone.utc)
    
    for i in range(1, cantidad + 1):
        vuelos.append({
            "id_vuelo": i,
            "numero_vuelo": f"VU-{1000 + i}",
            
            "salida_programada_utc": hora_actual + timedelta(minutes=random.randint(60, 300))
        })
    return vuelos

def generar_eventos_oooi(vuelo, tasa_defectos=0.1):
    """
    Simula el ciclo OOOI completo para un vuelo y aplica la inyección de defectos 
    exigida por las reglas de calidad (HU-05).
    """
    eventos = []
    es_defectuoso = random.random() < tasa_defectos
    tipo_defecto = random.choice(["FALTA_EVENTO", "CAUSA_INVALIDA", "PARADOJA_TIEMPO"]) if es_defectuoso else None

    t_out = vuelo["salida_programada_utc"] + timedelta(minutes=random.randint(-10, 45))
    t_off = t_out + timedelta(minutes=random.randint(10, 20))
    t_on = t_off + timedelta(minutes=random.randint(40, 180))
    t_in = t_on + timedelta(minutes=random.randint(5, 15))

    retraso_minutos = (t_out - vuelo["salida_programada_utc"]).total_seconds() / 60
    causa_out = random.choice(CAUSAS_VALIDAS) if retraso_minutos > 15 else None

    if tipo_defecto == "CAUSA_INVALIDA" and causa_out is not None:
        causa_out = "ERROR_99" # Causa que no existe en el catálogo

    if tipo_defecto == "PARADOJA_TIEMPO":
        # Restamos 24 horas al evento de llegada para simular un mal cálculo de zona horaria
        t_in = t_in - timedelta(days=1)

    # Formato ISO 8601 
    eventos.append(_crear_mensaje(vuelo, "OUT", t_out, causa_out))
    eventos.append(_crear_mensaje(vuelo, "OFF", t_off))
    
    # Aplicar defecto de falta de evento 
    if tipo_defecto != "FALTA_EVENTO":
        eventos.append(_crear_mensaje(vuelo, "ON", t_on))
        
    eventos.append(_crear_mensaje(vuelo, "IN", t_in))

    return eventos

def _crear_mensaje(vuelo, codigo_evento, fecha_hora, causa=None):
    """Función auxiliar para estructurar el diccionario del mensaje."""
    return {
        "id_externo_evento": str(uuid.uuid4()), # Simulador genera su propio ID único
        "id_vuelo": vuelo["id_vuelo"],
        "numero_vuelo": vuelo["numero_vuelo"],
        "codigo_evento": codigo_evento,
        "fecha_hora_evento_utc": fecha_hora.isoformat(),
        "codigo_causa_original": causa
    }