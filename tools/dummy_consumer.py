import os
import json
import time
import sys
import pika
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")
QUEUE_NAME = os.getenv("QUEUE_NAME", "eventos_oooi_queue")

def callback(ch, method, properties, body):
    """Esta función se ejecuta automáticamente cada vez que llega un mensaje."""
    mensaje = json.loads(body)
    causa = mensaje.get('codigo_causa_original')
    causa_str = f" | Causa: {causa}" if causa else ""
    print(f"[x] Recibido: Vuelo {mensaje.get('numero_vuelo')} | Evento {mensaje.get('codigo_evento')} | Fecha: {mensaje.get('fecha_hora_evento_utc')}{causa_str}", flush=True)

    # Confirmar a RabbitMQ que el mensaje fue procesado para que lo borre de la cola
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_consumidor(max_intentos=10, espera_segundos=3):
    print(f"[*] Conectando a RabbitMQ en {RABBITMQ_HOST}:{RABBITMQ_PORT} para escuchar '{QUEUE_NAME}'...", flush=True)
    credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parametros = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=credenciales,
        heartbeat=600,
        blocked_connection_timeout=300
    )

    for intento in range(1, max_intentos + 1):
        try:
            connection = pika.BlockingConnection(parametros)
            channel = connection.channel()

            # Nos aseguramos de que la cola exista antes de leer
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            # Le decimos a RabbitMQ que use la función 'callback' cuando lleguen mensajes
            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

            print("[*] Esperando mensajes. Presiona CTRL+C para salir.", flush=True)
            channel.start_consuming()
            return
        except (pika.exceptions.AMQPConnectionError, Exception) as e:
            print(f"[!] Intento {intento}/{max_intentos} fallido: {e}", flush=True)
            if intento < max_intentos:
                print(f"[*] Reintentando en {espera_segundos} segundos...", flush=True)
                time.sleep(espera_segundos)
            else:
                print(f"[!] Error: No se pudo conectar al broker tras {max_intentos} intentos.", flush=True)
                sys.exit(1)

if __name__ == "__main__":
    try:
        iniciar_consumidor()
    except KeyboardInterrupt:
        print("\n[*] Proceso detenido manualmente por el usuario. Saliendo limpiamente...", flush=True)
