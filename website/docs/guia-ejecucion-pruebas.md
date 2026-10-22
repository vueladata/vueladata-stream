---
id: guia-ejecucion-pruebas
title: Guía de Clonación, Ejecución y Validación
sidebar_position: 2
---

# Guía de Clonación, Ejecución y Pruebas del Simulador F4

Este documento proporciona el instructivo detallado paso a paso para clonar, configurar, desplegar y auditar el microservicio **Stream-VuelaData (Módulo F4)** desde cero, asegurando el cumplimiento de las Historias de Usuario **HU-06**, **HU-20**, **HU-21** y los Criterios Transversales **CT-01** y **CT-02**.

---

## 1. Requisitos Previos

Antes de comenzar, asegúrate de tener instaladas y operativas las siguientes herramientas en tu máquina anfitriona:

| Herramienta | Versión Mínima | Propósito | Comando de Verificación |
| :--- | :--- | :--- | :--- |
| **Git** | 2.30+ | Clonación y control de versiones | `git --version` |
| **Docker Engine** | 24.0+ | Creación y ejecución de contenedores | `docker --version` |
| **Docker Compose** | v2.20+ | Orquestación multi-contenedor | `docker compose version` |
| **Python** *(Opcional)* | 3.12+ | Pruebas nativas sin Docker | `python --version` |

:::warning Verificación de Puertos
Asegúrate de que los puertos **5672** (protocolo AMQP de RabbitMQ) y **15672** (consola web de administración) no estén siendo utilizados por otras instancias locales antes de iniciar.
:::

---

## 2. Clonación del Repositorio

Abre tu terminal favorita (PowerShell, Bash, Zsh) y ejecuta:

```bash
# 1. Clonar el repositorio oficial
git clone https://github.com/vueladata/Stream-VuelaData.git

# 2. Ingresar al directorio del proyecto
cd Stream-VuelaData
```

### Estructura del Proyecto
Al clonar, el árbol de directorios contendrá los siguientes elementos clave:

```text
Stream-VuelaData/
├── src/
│   ├── oooi_generator.py     # Motor matemático OOOI con 10% de inyección de defectos
│   └── producer.py           # Productor AMQP con reintentos y persistencia (delivery_mode=2)
├── tools/
│   └── dummy_consumer.py     # Consumidor de validación y confirmación ACK
├── website/                  # Portal de documentación técnica (Docusaurus)
├── .dockerignore             # Exclusión estricta de archivos innecesarios
├── .env.example              # Plantilla segura de variables de entorno (CT-02)
├── .gitignore                # Blindaje de secretos y artefactos locales
├── Dockerfile                # Imagen optimizada python:3.12-slim y usuario no-root appuser
├── docker-compose.yml        # Orquestación con healthchecks, volumen y red dedicada
├── README.md                 # Resumen ejecutivo y tabla de optimización HU-20
└── requirements.txt          # Dependencias codificadas en UTF-8 puro
```

---

## 3. Configuración de Variables de Entorno (CT-02)

Para cumplir con el **Criterio Transversal CT-02** (cero secretos en el repositorio), las credenciales no se encuentran quemadas en el código fuente. Debes inicializar tu archivo `.env` a partir de la plantilla:

### En Linux / macOS / PowerShell (Bash):
```bash
cp .env.example .env
```

### En Windows (cmd):
```cmd
copy .env.example .env
```

### Detalle de Parámetros Configurables en `.env`

```ini
# Conexión al Broker RabbitMQ
RABBITMQ_HOST=rabbitmq          # En Docker usa el nombre de servicio 'rabbitmq'; en pruebas locales usa 'localhost'
RABBITMQ_PORT=5672              # Puerto estándar AMQP
RABBITMQ_USER=vuela_user        # Usuario para autenticación
RABBITMQ_PASS=changeme_in_local # Contraseña local
QUEUE_NAME=eventos_oooi_queue   # Nombre de la cola durable

# Control de la Simulación
STREAM_DELAY_SECONDS=1          # Intervalo en segundos entre cada mensaje (1 = tiempo real, 0 = ráfaga rápida)
TOTAL_VUELOS=100                # Cantidad total de vuelos comerciales a generar en agenda
```

---

## 4. Método 1: Despliegue Automatizado con Docker Compose (Recomendado)

Este método valida los criterios de aceptación de **HU-20** (imágenes seguras/optimizadas), **HU-21** (entorno multi-contenedor orquestado) y **CT-01** (arranque en menos de 30 minutos con un solo comando).

### Paso 4.1: Construir y Levantar los Servicios

Ejecuta el siguiente comando en la raíz del proyecto:

```bash
docker compose up -d --build
```

#### ¿Qué sucede internamente?
1. **Compilación de la Imagen:** Docker construye la imagen del productor a partir de `python:3.12-slim`, instalando dependencias desde `requirements.txt` y configurando el usuario seguro `appuser`.
2. **Red Aislada:** Se inicializa la red tipo puente `vueladata_net`.
3. **Persistencia:** Se crea el volumen local `rabbitmq_data` mapeado a `/var/lib/rabbitmq`.
4. **Healthcheck Activo:** RabbitMQ inicia y el sistema ejecuta revisiones periódicas mediante `rabbitmq-diagnostics -q ping`.
5. **Arranque Condicionado:** El servicio `stream_f4` aguarda hasta que RabbitMQ reporte estado `healthy` para comenzar a enviar mensajes, evitando errores de conexión prematura.

---

### Paso 4.2: Verificar el Estado de los Contenedores

Verifica que ambos contenedores se encuentren en estado saludable y operativo:

```bash
docker compose ps
```

*Salida esperada:*
```text
NAME                 IMAGE                        COMMAND                  SERVICE      STATUS                    PORTS
f4-rabbitmq          rabbitmq:3-management-alpine "docker-entrypoint.s…"   rabbitmq     Up (healthy)              0.0.0.0:5672->5672/tcp, 0.0.0.0:15672->15672/tcp
stream-f4-producer   stream-vueladata-stream_f4   "python src/producer…"   stream_f4    Up                        
```

---

### Paso 4.3: Monitorear la Transmisión de Eventos OOOI

Observa la emisión de eventos en tiempo real:

```bash
docker compose logs -f stream_f4
```

*Salida esperada en consola:*
```text
[*] Conectando a RabbitMQ en rabbitmq:5672 (Intento 1/10)...
[+] Conectado exitosamente. Cola 'eventos_oooi_queue' lista.
[*] Generando agenda de 100 vuelos en memoria...
[*] Transmitiendo eventos OOOI a la cola 'eventos_oooi_queue'...
--------------------------------------------------
[>] Enviado [1]: Vuelo VU-1001 | Evento OUT
[>] Enviado [2]: Vuelo VU-1001 | Evento OFF
[>] Enviado [3]: Vuelo VU-1001 | Evento ON
[>] Enviado [4]: Vuelo VU-1001 | Evento IN
[>] Enviado [5]: Vuelo VU-1002 | Evento OUT | Causa: TECNICA
...
```

---

### Paso 4.4: Auditoría en el Panel de RabbitMQ Management

1. Abre tu navegador e ingresa a: **[http://localhost:15672](http://localhost:15672)**.
2. Inicia sesión con las credenciales definidas en tu `.env` (por defecto: usuario `vuela_user` y contraseña `changeme_in_local`).
3. Ve a la pestaña **Queues and Streams**.
4. Haz clic sobre **`eventos_oooi_queue`**:
   - Observa la tasa de entrada de mensajes (*Incoming rate*).
   - Verifica que el estado de los mensajes sea **Durable** y estén en disco.
   - En la sección **Get messages**, puedes obtener 1 mensaje de muestra para inspeccionar el JSON del contrato de datos.

---

### Paso 4.5: Prueba de Persistencia ante Fallos (Resiliencia HU-21)

Para comprobar que los mensajes no se pierden si el broker sufre un reinicio:

```bash
# 1. Reiniciar forzosamente el contenedor de RabbitMQ
docker compose restart rabbitmq

# 2. Comprobar que el productor reconecta automáticamente
docker compose logs --tail=20 stream_f4

# 3. Verificar en el panel web (http://localhost:15672) que la cola conserva los mensajes acumulados.
```

---

## 5. Método 2: Ejecución y Validación Local en Consola (Consumidor vs. Productor)

Si deseas auditar paso a paso la recepción de mensajes con confirmación ACK en tiempo real mediante consolas separadas:

### Paso 5.1: Levantar Únicamente el Broker RabbitMQ
```bash
docker compose up -d rabbitmq
```

### Paso 5.2: Preparar el Entorno Virtual de Python

En una terminal en la raíz de `Stream-VuelaData`:

```bash
# Crear entorno virtual
python -m venv venv

# Activar en Windows PowerShell:
.\venv\Scripts\Activate.ps1

# O en Linux / macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 5.3: Configurar `.env` para Conexión Local
Asegúrate de que en tu archivo `.env` local tengas configurado:
```ini
RABBITMQ_HOST=localhost
```

### Paso 5.4: Iniciar Consumidor Validador (Terminal 1)
En la primera terminal, inicia la herramienta de consumo de prueba:

```bash
python tools/dummy_consumer.py
```

*Salida:*
```text
[*] Conectando a RabbitMQ en localhost:5672 para escuchar 'eventos_oooi_queue'...
[*] Esperando mensajes. Presiona CTRL+C para salir.
```

### Paso 5.5: Iniciar Productor Simulador (Terminal 2)
Abre una segunda terminal, activa el entorno virtual y ejecuta:

```bash
python src/producer.py
```

### Paso 5.6: Confirmación del Flujo Bidireccional
Observarás en la **Terminal 1** cómo el consumidor procesa cada mensaje y envía el `ack` correspondiente a RabbitMQ para liberar la cola:

```text
[x] Recibido: Vuelo VU-1001 | Evento OUT | Fecha: 2026-10-22T08:15:00+00:00
[x] Recibido: Vuelo VU-1001 | Evento OFF | Fecha: 2026-10-22T08:29:00+00:00
[x] Recibido: Vuelo VU-1001 | Evento ON  | Fecha: 2026-10-22T10:04:00+00:00
[x] Recibido: Vuelo VU-1001 | Evento IN  | Fecha: 2026-10-22T10:14:00+00:00
```

---

## 6. Validación de Reglas de Calidad y Defectos OOOI (HU-06)

El simulador inyecta un **10% de caos** estocástico. Durante la ejecución podrás identificar los siguientes tres defectos de calidad para evaluar los filtros del consumidor final:

1. **`CAUSA_INVALIDA`:**
   - **Qué buscar:** En la consola verás mensajes con `Causa: ERROR_99`.
   - **Propósito:** Evalúa si el receptor rechaza causas que no existen en el catálogo paramétrico de la base de datos (`TECNICA`, `CLIMA`, `TRIPULACION`, `OPERACIONAL`).
2. **`FALTA_EVENTO`:**
   - **Qué buscar:** Para un vuelo específico, se emitirán los eventos `OUT`, `OFF` e `IN`, omitiendo por completo el evento de aterrizaje `ON`.
   - **Propósito:** Evalúa si el consumidor detecta pérdidas de señal de telemetría y bloquea el cálculo de tiempo de vuelo en el pipeline analítico.
3. **`PARADOJA_TIEMPO`:**
   - **Qué buscar:** La fecha del evento `IN` contiene un desfase de -24 horas respecto al despegue `OFF`.
   - **Propósito:** Evalúa si el receptor valida cronológicamente que un avión no puede aterrizar antes de despegar.

---

## 7. Detención y Limpieza del Entorno

Cuando finalices tus pruebas, puedes detener o limpiar los recursos según tu necesidad:

```bash
# 1. Detener los contenedores sin borrar los datos de RabbitMQ:
docker compose stop

# 2. Detener y remover los contenedores y la red:
docker compose down

# 3. Limpieza completa (remueve también el volumen de RabbitMQ):
docker compose down -v
```

---

## 8. Solución de Problemas Frecuentes (Troubleshooting)

| Síntoma | Causa Posible | Solución |
| :--- | :--- | :--- |
| `Bind for 0.0.0.0:5672 failed: port is already allocated` | Ya tienes un servicio local de RabbitMQ activo en tu máquina. | Detén el servicio local con `Stop-Service RabbitMQ` (Windows) o cambia el puerto en `docker-compose.yml` (ej. `5673:5672`). |
| `failed to connect to the docker API` | El motor de Docker (Docker Desktop) no está iniciado. | Inicia la aplicación **Docker Desktop** y espera a que el ícono esté en verde. |
| `Error de autenticación (ACCESS_REFUSED)` | Las credenciales en `.env` no coinciden con las creadas en el volumen persistente de RabbitMQ. | Si cambiaste de usuario/clave en `.env`, debes eliminar el volumen anterior ejecutando `docker compose down -v` y volver a levantar. |
| `ModuleNotFoundError: No module named 'pika'` en local | No activaste el entorno virtual antes de ejecutar el script. | Ejecuta `.\venv\Scripts\activate` (o `source venv/bin/activate`) e instala dependencias con `pip install -r requirements.txt`. |
