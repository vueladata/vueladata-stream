---
id: stream-f4-simulator
title: Simulador de Stream F4 (Eventos OOOI)
sidebar_position: 1
---

# Simulador de Eventos OOOI (Stream F4)

Este componente actúa como el **Productor** dentro de la arquitectura orientada a eventos de VuelaData. Su principal responsabilidad es la generación sintética del ciclo de vida de los vuelos comerciales (OOOI) y su transmisión asíncrona hacia un broker de mensajería (RabbitMQ).

El diseño de este módulo está pensado para evaluar la resiliencia de los sistemas consumidores downstream (APIs y pipelines ETL) ante fluctuaciones de tiempo, ráfagas de mensajes y datos operacionalmente corruptos.

---

## 1. Arquitectura del Microservicio

Para aislar el entorno de evaluación y no depender de la base de datos transaccional principal, este módulo opera en memoria utilizando los siguientes componentes:

* **Generador de Datos (`src/oooi_generator.py`):** El motor matemático. Simula una agenda de vuelos en tiempo real (UTC) y calcula las deltas de tiempo lógicas para despegues y aterrizajes.
* **Productor (`src/producer.py`):** El cliente AMQP. Transforma los diccionarios de Python generados en _payloads_ JSON y los publica en la cola persistente `eventos_oooi_queue` de RabbitMQ.
* **Broker de Mensajería:** Contenedor Docker de RabbitMQ (`rabbitmq:3-management-alpine`). Se encarga de desacoplar la emisión de la recepción, garantizando que no se pierdan eventos si el consumidor cae.
* **Consumidor Validador (`tools/dummy_consumer.py`):** Herramienta de auditoría para el evaluador. Se suscribe a la cola e imprime los eventos en consola, confirmando su procesamiento (ACK) para vaciar el broker.

---

## 2. El Ciclo de Vida OOOI

La simulación matemática respeta la secuencia estricta de la aviación comercial, calculando tiempos dependientes de forma progresiva:

1. **OUT (Salida de puerta):** Se calcula a partir de la hora de salida programada, con fluctuaciones aleatorias entre -10 y +45 minutos.
2. **OFF (Despegue):** Se genera sumando entre 10 y 20 minutos al tiempo OUT (simulando el rodaje hacia la pista).
3. **ON (Aterrizaje):** Se genera sumando el tiempo de vuelo al tiempo OFF (entre 40 y 180 minutos).
4. **IN (Llegada a puerta):** Se genera sumando el tiempo de rodaje final al tiempo ON (entre 5 y 15 minutos).

---

## 3. Contrato de Datos (Payload JSON)

Todos los mensajes enviados a RabbitMQ cumplen de forma estricta con este contrato, garantizando que el consumidor sepa exactamente qué tipos de datos esperar:

```json
{
  "id_externo_evento": "a1b2c3d4-e5f6-7890-1234-56789abcdef0",
  "id_vuelo": 1,
  "numero_vuelo": "VU-1001",
  "codigo_evento": "OUT",
  "fecha_hora_evento_utc": "2026-10-14T07:15:00+00:00",
  "codigo_causa_original": "TECNICA"
}
```

### Diccionario de Campos
| Campo | Tipo | Descripción |
|---|---|---|
| `id_externo_evento` | `UUID v4` | Identificador único del mensaje generado por el sensor del avión. |
| `id_vuelo` | `Integer` | Llave foránea que relaciona el evento con el catálogo transaccional. |
| `numero_vuelo` | `String` | Código comercial del vuelo (Ej: VU-1001). |
| `codigo_evento` | `String` | Fase operativa registrada (`OUT`, `OFF`, `ON`, `IN`). |
| `fecha_hora_evento_utc` | `String (ISO 8601)` | Timestamp exacto del evento, estandarizado siempre a zona horaria UTC (+00:00). |
| `codigo_causa_original` | `String` / `Null` | Si el evento `OUT` ocurre con >15 min de retraso, registra la causa original (`TECNICA`, `CLIMA`, etc.). De lo contrario, viaja como `Null`. |

---

## 4. Ingeniería del Caos (Cumplimiento HU-05)

Para validar las reglas de calidad de datos, el script `oooi_generator.py` implementa una función de inyección de defectos que afecta exactamente al **10%** de los vuelos simulados. 

El sistema elige aleatoriamente uno de los siguientes comportamientos anómalos para exigir al máximo los filtros de calidad del consumidor final:

1. **Falta de Evento (`FALTA_EVENTO`):** Simula una pérdida de señal del sensor. El avión registra su despegue (`OFF`) y llegada a puerta (`IN`), pero el evento de aterrizaje (`ON`) jamás es generado ni enviado a la cola.
2. **Causa de Retraso Fuera de Catálogo (`CAUSA_INVALIDA`):** El sistema sobrescribe una causa de retraso legítima (ej. `CLIMA`) con el string `ERROR_99`, forzando a la base de datos receptora a manejar un dato que no existe en su tabla paramétrica.
3. **Paradoja Temporal (`PARADOJA_TIEMPO`):** Simula una mala configuración de zona horaria al cruzar la medianoche. El script toma el evento `IN` y le resta 24 horas, provocando que la base de datos reciba un aterrizaje que cronológicamente ocurre antes que el despegue.