# 5. Documento de hardware

## 5.1 Componentes

| Cantidad | Componente | Función | Especificación usada en el prototipo |
| ---: | :--- | :--- | :--- |
| 1 | Equipo del parqueadero (PC) | Ejecuta el worker de cámaras | Python 3.12, `uv`. GPU NVIDIA opcional para acelerar YOLO y EasyOCR |
| 2 | Cámaras USB o web | Lectura de placas en ingreso y salida | Índices `CAM_ENTRY_INDEX` (1) y `CAM_EXIT_INDEX` (2) en OpenCV |
| 1 | Arduino (UNO o compatible) | Control de las talanqueras | Conexión USB serial a 9600 baudios |
| 1 | Módulo de 2 relés | Acciona cada talanquera | Entrada en el pin 8, salida en el pin 9 |
| 2 | Talanqueras o actuadores | Barrera física | Se activan con el contacto del relé |
| 1 | Cable USB | Arduino ↔ PC | — |

> **Pendiente de completar por el equipo:** marca y modelo exactos de las cámaras, del Arduino, del módulo de relés y de las talanqueras usadas en la demostración, más la fuente de alimentación de los actuadores.

## 5.2 Conexión

```text
                    ┌──────────────────────────┐
   USB ─────────────┤ Arduino                  │
   (PC, 9600)       │                          │
                    │  Pin 8 ──────────► IN1 ──┤ Relé 1 ──► Talanquera de ENTRADA
                    │  Pin 9 ──────────► IN2 ──┤ Relé 2 ──► Talanquera de SALIDA
                    │  5V    ──────────► VCC   │
                    │  GND   ──────────► GND   │
                    └──────────────────────────┘
```

- Los actuadores de las talanqueras se alimentan con su propia fuente a través del contacto del relé (COM/NO), **nunca** desde el pin de 5 V del Arduino.
- Si el módulo de relés se activa en nivel bajo, intercambie `RELE_ACTIVO` y `RELE_REPOSO` en el sketch.
- Al arrancar, el sketch fija primero el nivel de reposo y después configura el pin como salida, para que el relé no se active durante el encendido.

## 5.3 Sketch del Arduino

Archivo: [`arduino/sigap_talanquera/sigap_talanquera.ino`](../arduino/sigap_talanquera/sigap_talanquera.ino).

Carga:

1. Abra el archivo en Arduino IDE.
2. Seleccione la placa y el puerto (por ejemplo `COM3` en Windows o `/dev/ttyACM0` en Linux).
3. Cargue el sketch. En el Monitor Serie (9600 baudios) debe aparecer `READY`.
4. Escriba `P` y confirme que responde `PONG`. Escriba `E` y confirme que el relé 1 se activa, responde `ACK:E` y, al vencer el tiempo, `CLOSED:E`.
5. Cierre el Monitor Serie antes de iniciar el worker: el puerto solo admite un programa a la vez.

El sketch usa `millis()` en lugar de `delay()`, así que una talanquera abierta no bloquea a la otra. La resta de tiempos con `unsigned long` sigue siendo correcta cuando `millis()` se reinicia cada 49 días.

## 5.4 Protocolo serial

Velocidad 9600 baudios, 8N1. Las órdenes son un solo carácter, excepto `T`, que termina en salto de línea.

| Orden (PC → Arduino) | Respuesta (Arduino → PC) | Significado |
| :--- | :--- | :--- |
| — | `READY` | El Arduino terminó de iniciar |
| `E` | `ACK:E` y luego `CLOSED:E` | Abre la talanquera de entrada y la cierra al vencer el tiempo |
| `S` | `ACK:S` y luego `CLOSED:S` | Igual para la salida |
| `P` | `PONG` | Comprobación de comunicación |
| `T<seg>\n` (1 a 60) | `OK:T=<seg>` | Cambia el tiempo de apertura |
| `T<seg>\n` fuera de rango | `ERR:T` | Valor rechazado |

Comportamiento del worker ([`gate_controller.py`](../backend/src/worker/gate_controller.py)):

- Después de enviar `E` o `S` espera `ACK` durante **1,5 s** e ignora las demás líneas (por ejemplo, un `CLOSED` anterior). Sin `ACK`, la orden se considera fallida.
- Al abrir el puerto espera a que el Arduino se reinicie (abrir el puerto serial reinicia la placa).
- Si se pierde la conexión, la descarta y la vuelve a abrir en el siguiente intento. Si el puerto no existe o el Arduino no responde `PONG`, reporta las dos talanqueras como `no_communication` en el heartbeat sin detener el worker.
- En cada heartbeat recibe del backend `gate_open_seconds` y, si cambió, lo envía con `T<seg>`. Así el tiempo de apertura se configura desde la pantalla **Parqueadero** del Administrador.

## 5.5 Qué significa el ACK

`ACK` confirma que el Arduino recibió la orden **y activó el relé**. No confirma que la barrera se haya movido ni que el vehículo haya pasado: el prototipo no tiene sensor de paso y la talanquera se cierra por tiempo (`gate_open_seconds`, 3 s por defecto). La HU-05 y la HU-12 piden que la talanquera cierre "una vez el vehículo haya pasado"; en esta versión se cumple por tiempo. Para cumplirlo con detección real se recomienda un sensor de lazo inductivo o una barrera infrarroja conectada a una entrada digital del Arduino, que envíe `CLOSED` solo cuando el vehículo haya cruzado.

## 5.6 Fallas y su tratamiento

| Situación | Qué hace el sistema |
| :--- | :--- |
| El Arduino no responde `ACK` | Evento `GATE_NO_RESPONSE`, ticket automático para Soporte, pantalla del carril en error. En la salida, la transacción sigue `PAID` |
| El Arduino está desconectado o no responde `PONG` | Las dos talanqueras aparecen como `no_communication` en **Dispositivos** |
| La última apertura de una talanquera falló | Esa talanquera aparece como `error` hasta la siguiente apertura correcta |
| Una cámara no entrega imagen | La cámara aparece como `error` en **Dispositivos** |
| El worker deja de enviar heartbeat por más de 20 s | Los cuatro dispositivos pasan a `no_communication` y se abre un único ticket `WORKER_NO_COMMUNICATION` |
