# Simulador de Stream F4 (Eventos OOOI)

Este repositorio contiene el Productor de eventos asíncronos para el proyecto VuelaData, simulando la generación del ciclo de vida de vuelos comerciales y su envío a través de RabbitMQ.

## Requisitos Previos
- Docker y Docker Desktop en ejecución.
- Python 3.10 o superior.

## Ejecución del Entorno de Prueba
Para evaluar el envío y recepción de mensajes de forma aislada, ejecute los siguientes pasos en terminales separadas:

1. **Levantar el Broker de Mensajería:** 
   ```bash
   docker-compose up -d
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Iniciar el Consumidor (Terminal 1 - Escucha activa):**
   ```bash
   python tools/dummy_consumer.py
   ```

4. **Ejecutar el Simulador (Terminal 2 - Inyección de datos):**
   ```bash
   python src/producer.py
   ```

## Documentación Técnica
La documentación detallada de este módulo está construida con Docusaurus. Para visualizarla localmente:

1. Navegue a la carpeta de la web: `cd website`
2. Instale los paquetes (solo la primera vez): `npm install`
3. Levante el servidor: `npm run start`