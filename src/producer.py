import os
import json
import time
import sys
import pika
from dotenv import load_dotenv

# Importación robusta del generador (soporta ejecución directa o como módulo)
try:
    from oooi_generator import generar_vuelos_base, generar_eventos_oooi
except ImportError:
    from src.oooi_generator import generar_vuelos_base, generar_eventos_oooi

# 1. Configuración inicial
load_dotenv()
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")
QUEUE_NAME = os.getenv("QUEUE_NAME", "eventos_oooi_queue")
STREAM_DELAY_SECONDS = float(os.getenv("STREAM_DELAY_SECONDS", "1"))
TOTAL_VUELOS = int(os.getenv("TOTAL_VUELOS", "100"))

def conectar_rabbitmq(max_intentos=10, espera_segundos=3):
    """Establece la conexión con RabbitMQ con mecanismo de reintentos para evitar caídas en arranque."""
    credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parametros = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credenciales,
        heartbeat=600,
        blocked_connection_timeout=300
    )

    for intento in range(1, max_intentos + 1):
        print(f"[*] Conectando a RabbitMQ en {RABBITMQ_HOST}:{RABBITMQ_PORT} (Intento {intento}/{max_intentos})...", flush=True)
        try:
            connection = pika.BlockingConnection(parametros)
            channel = connection.channel()

            # durable=True asegura que la cola no se borre si RabbitMQ se reinicia
            channel.queue_declare(queue=QUEUE_NAME, durable=True)
            print(f"[+] Conectado exitosamente. Cola '{QUEUE_NAME}' lista.", flush=True)
            return connection, channel
        except (pika.exceptions.AMQPConnectionError, Exception) as e:
            print(f"[!] Intento {intento} fallido: {e}", flush=True)
            if intento < max_intentos:
                print(f"[*] Reintentando en {espera_segundos} segundos...", flush=True)
                time.sleep(espera_segundos)
            else:
                print(f"[!] Error crítico: No fue posible conectar a RabbitMQ tras {max_intentos} intentos. ¿Está levantado el servicio?", flush=True)
                sys.exit(1)

def iniciar_stream():
    connection, channel = conectar_rabbitmq()

    print(f"[*] Generando agenda de {TOTAL_VUELOS} vuelos en memoria...", flush=True)
    vuelos = generar_vuelos_base(cantidad=TOTAL_VUELOS)

    print(f"[*] Transmitiendo eventos OOOI a la cola '{QUEUE_NAME}'...", flush=True)
    print("-" * 50, flush=True)

    total_eventos_enviados = 0

    try:
        for vuelo in vuelos:
            # Inyección de caos (10% defectos según HU-05)
            eventos = generar_eventos_oooi(vuelo, tasa_defectos=0.1)

            for evento in eventos:
                mensaje_json = json.dumps(evento)

                # Publicar el mensaje en la cola de RabbitMQ con persistencia
                channel.basic_publish(
                    exchange='',
                    routing_key=QUEUE_NAME,
                    body=mensaje_json,
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Mensaje persistente en disco (durabilidad HU-21)
                        content_type="application/json"
                    )
                )
                total_eventos_enviados += 1
                causa_info = evento.get('codigo_causa_original')
                causa_txt = f" | Causa: {causa_info}" if causa_info else ""
                print(f"[>] Enviado [{total_eventos_enviados}]: Vuelo {evento['numero_vuelo']} | Evento {evento['codigo_evento']}{causa_txt}", flush=True)

                if STREAM_DELAY_SECONDS > 0:
                    time.sleep(STREAM_DELAY_SECONDS)

    finally:
        print("-" * 50, flush=True)
        print(f"[*] Transmisión finalizada. Se publicaron {total_eventos_enviados} eventos en la cola.", flush=True)
        if connection and connection.is_open:
            connection.close()

if __name__ == "__main__":
    try:
        iniciar_stream()
    except KeyboardInterrupt:
        print("\n[*] Proceso detenido manualmente por el usuario. Saliendo limpiamente...", flush=True)
