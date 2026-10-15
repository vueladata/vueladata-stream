import os
import json
import time
import pika
from dotenv import load_dotenv
from oooi_generator import generar_vuelos_base, generar_eventos_oooi

# 1. Configuración inicial
load_dotenv()
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "admin123")
QUEUE_NAME = os.getenv("QUEUE_NAME", "eventos_oooi_queue")

def conectar_rabbitmq():
    """Establece la conexión con el broker de RabbitMQ usando credenciales."""
    print(f"[*] Conectando a RabbitMQ en {RABBITMQ_HOST}...")
    try:
        # Configuramos el usuario y contraseña
        credenciales = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
        parametros = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credenciales)
        
        connection = pika.BlockingConnection(parametros)
        channel = connection.channel()
        
        # durable=True asegura que la cola no se borre si RabbitMQ se reinicia
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        return connection, channel
    except Exception as e:
        print(f"[!] Error de conexión: {e}. ¿Está encendido el contenedor de Docker?")
        exit(1)

def iniciar_stream():
    connection, channel = conectar_rabbitmq()
    
    print("[*] Generando agenda de vuelos en memoria...")
    vuelos = generar_vuelos_base(cantidad=100) # Generamos 100 vuelos de prueba
    
    print(f"[*] Transmitiendo eventos OOOI a la cola '{QUEUE_NAME}'...")
    print("-" * 50)
    
    for vuelo in vuelos:
        # Aquí inyectamos el 10% de caos configurado
        eventos = generar_eventos_oooi(vuelo, tasa_defectos=0.1)
        
        for evento in eventos:
            mensaje_json = json.dumps(evento)
            
            # Publicar el mensaje en la cola de RabbitMQ
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=mensaje_json,
                properties=pika.BasicProperties(
                    delivery_mode=2, # Hace que el mensaje sea persistente en disco
                )
            )
            
            print(f"[>] Enviado: Vuelo {evento['numero_vuelo']} | Evento {evento['codigo_evento']} | Causa: {evento.get('codigo_causa_original')}")
            
            # Pausa de 1 segundo para simular un stream en tiempo real
            time.sleep(1)
            
    print("-" * 50)
    print("[*] Transmisión finalizada. Todos los eventos están en la cola.")
    connection.close()

if __name__ == "__main__":
    try:
        iniciar_stream()
    except KeyboardInterrupt:
        print("\n[*] Proceso detenido manualmente. Saliendo limpiamente...")