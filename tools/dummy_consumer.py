import os
import json
import pika
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")
QUEUE_NAME = os.getenv("QUEUE_NAME", "eventos_oooi_queue")

def callback(ch, method, properties, body):
    """Esta función se ejecuta automáticamente cada vez que llega un mensaje."""
    mensaje = json.loads(body)
    print(f"[x] Recibido: Vuelo {mensaje['numero_vuelo']} | Evento {mensaje['codigo_evento']} | Fecha: {mensaje['fecha_hora_evento_utc']}")
    
    # Confirmar a RabbitMQ que el mensaje fue procesado para que lo borre de la cola
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_consumidor():
    print(f"[*] Conectando a RabbitMQ en {RABBITMQ_HOST} para leer la cola '{QUEUE_NAME}'...")
    try:
        credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parametros = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credenciales)
        
        connection = pika.BlockingConnection(parametros)
        channel = connection.channel()
        
        # Nos aseguramos de que la cola exista antes de leer
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        # Le decimos a RabbitMQ que use la función 'callback' cuando lleguen mensajes
        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
        
        print("[*] Esperando mensajes. Presiona CTRL+C para salir.")
        channel.start_consuming()
        
    except Exception as e:
        print(f"[!] Error: {e}")
        exit(1)

if __name__ == "__main__":
    try:
        iniciar_consumidor()
    except KeyboardInterrupt:
        print("\n[*] Proceso detenido manualmente. Saliendo limpiamente...")