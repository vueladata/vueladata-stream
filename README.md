# Simulador de Stream F4 (Eventos OOOI) — VuelaData

Este repositorio contiene el **Productor de eventos asíncronos (F4)** para el proyecto VuelaData, responsable de simular el ciclo de vida operacional de vuelos comerciales (fases **OOOI**: *Out of gate*, *Off ground*, *On ground*, *Into gate*) y transmitirlos de manera persistente a través de un broker RabbitMQ.

Incluye inyección de anomalías controladas (**10% de caos**) para someter a prueba la resiliencia y filtros de calidad de los consumidores downstream (APIs y pipelines ETL).

---

## 📋 Requisitos Previos

- **Docker** y **Docker Compose v2** (o Docker Desktop).
- *(Opcional para ejecución local sin Docker)*: Python 3.12+ y `pip`.

---

## 🚀 Puesta en Marcha con Docker (HU-20 y HU-21)

El entorno multi-contenedor orquesta el broker de RabbitMQ junto con el servicio productor (`stream_f4`) sobre una red aislada (`vueladata_net`).

### 1. Variables de Entorno
Copia la plantilla `.env.example` para inicializar tus variables locales (CT-02):
```bash
cp .env.example .env
```

### 2. Construcción y Arranque Completo
Inicia el broker y el productor con un solo comando:
```bash
docker compose up -d --build
```

El servicio `stream_f4` espera a que RabbitMQ supere su healthcheck (`condition: service_healthy`) antes de iniciar la transmisión de eventos persistentes (`delivery_mode=2`).

### 3. Visualizar la Transmisión
Para seguir los logs del productor en tiempo real:
```bash
docker compose logs -f stream_f4
```

### 4. Panel de Control RabbitMQ
Accede a la interfaz web de gestión:
- **URL:** [http://localhost:15672](http://localhost:15672)
- **Usuario:** `admin` (o el configurado en `.env`)
- **Contraseña:** `admin123` (o la configurada en `.env`)
- **Cola activa:** `eventos_oooi_queue`

---

## 🛠️ Ejecución Local para Desarrollo / Auditoría

Si deseas correr el productor y el consumidor en consolas separadas:

1. **Levantar únicamente el broker RabbitMQ:**
   ```bash
   docker compose up -d rabbitmq
   ```

2. **Instalar dependencias de Python (codificación UTF-8 pura):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Iniciar Consumidor Validador (Terminal 1 - Escucha activa con ACK):**
   ```bash
   python tools/dummy_consumer.py
   ```

4. **Ejecutar el Simulador Productor (Terminal 2 - Inyección OOOI):**
   ```bash
   python src/producer.py
   ```

---

## 📦 Evidencia de Optimización Docker (HU-20)

Para cumplir con la rúbrica de la **Historia de Usuario HU-20**, la imagen Docker del microservicio fue optimizada utilizando `python:3.12-slim`, exclusión estricta mediante `.dockerignore` (evitando transferir dependencias de Node.js / Docusaurus) y ejecución bajo el usuario sin privilegios `appuser` (UID 1000).

| Métrica / Parámetro | Configuración Estándar (Antes) | Configuración Optimizada (Ahora) | Beneficio |
| :--- | :--- | :--- | :--- |
| **Imagen Base** | `python:3.12` (~1.02 GB) | `python:3.12-slim` (~140 MB) | Reducción de ~85% en tamaño base |
| **Contexto de Build** | Sin `.dockerignore` (Copia `website/`, `node_modules`, cache) | Con `.dockerignore` estricto | Build context reducido de >150 MB a <1 MB |
| **Tamaño Final de Imagen** | ~1.15 GB | **~165 MB** | Menor tiempo de pull/push en CI/CD |
| **Usuario de Ejecución** | `root` (vulnerabilidad de seguridad) | `appuser` (UID 1000, no-root) | Principio de menor privilegio (Seguridad HU-20) |
| **Cache de Capas** | `COPY . .` antes de dependencias | `COPY requirements.txt` aislado | Builds incrementales en milisegundos |

---

## ⚙️ Contrato de Datos y Defectos OOOI (HU-06)

Cada mensaje publicado en RabbitMQ tiene la siguiente estructura JSON con persistencia (`delivery_mode=2`):

```json
{
  "id_externo_evento": "6afabb29-e37a-4bdd-83d9-6c3318edad7b",
  "id_vuelo": 1,
  "numero_vuelo": "VU-1001",
  "codigo_evento": "OUT",
  "fecha_hora_evento_utc": "2026-10-22T06:24:27.505964+00:00",
  "codigo_causa_original": "TECNICA"
}
```

### Inyección de Caos (10% de los vuelos):
1. **`FALTA_EVENTO`:** Simula pérdida de sensor omitiendo el evento de aterrizaje `ON`.
2. **`CAUSA_INVALIDA`:** Inyecta `ERROR_99` (código fuera del catálogo) para probar la validación de tablas paramétricas.
3. **`PARADOJA_TIEMPO`:** Resta 24h al evento `IN`, provocando un aterrizaje previo al despegue para validar reglas temporales.


---

## 📚 Documentación Técnica (Docusaurus)

Para consultar la documentación extendida con explicaciones de arquitectura y la guía detallada de clonación y auditoría:

- [Simulador de Stream F4 (Eventos OOOI)](website/docs/stream-f4-simlator.md)
- [Guía de Clonación, Ejecución y Validación](website/docs/guia-ejecucion-pruebas.md)

Para iniciar el servidor local de Docusaurus:
```bash
cd website
npm install
npm run start
```
