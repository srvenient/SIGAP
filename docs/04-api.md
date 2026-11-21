# 4. Especificación de la API

- **URL base:** `/api/v1` (en producción, Nginx la publica como `/api/v1` en el puerto 80 y la redirige al contenedor `api`).
- **Esquema completo:** [`api/openapi.json`](api/openapi.json), exportado de la versión entregada (OpenAPI 3.1, 54 rutas). Se puede abrir en <https://editor.swagger.io> o importar en Postman.
- **Documentación interactiva** con el backend en ejecución: `http://localhost:8000/api/v1/docs` (Swagger UI) y `http://localhost:8000/api/v1/redoc`.
- **Estado del servicio:** `GET /health-check` responde `{"status":"ok","database":"connected"}` o 503 si la base no responde.

Para regenerar el esquema después de un cambio:

```bash
cd backend && uv run python -c "import json; from src.server.main import app; json.dump(app.openapi(), open('../docs/api/openapi.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)"
```

## 4.1 Autenticación

La API reconoce tres tipos de cliente:

| Cliente | Mecanismo | Uso |
| :--- | :--- | :--- |
| Personal (Administrador, Operador, Soporte) | Cookies httpOnly con un JWT de acceso (15 min) y un refresh token rotativo (7 días, máximo 15 días por sesión) | Panel `/dashboard` |
| Worker de cámaras | Encabezado `X-Device-Key` con el valor de `DEVICE_API_KEY` | Ingreso, salida, heartbeat, eventos, alertas |
| Conductor | Ninguno; límite de peticiones por IP | Rutas `/public/*` |

El frontend renueva la sesión con `POST /auth/refresh` cuando el access token vence. Si un refresh token ya usado se presenta de nuevo pasados 30 s de gracia, se revoca toda la familia de tokens de esa sesión.

## 4.2 Endpoints

Convenciones de la columna **Acceso**: `Admin`, `Operador`, `Soporte` = rol requerido; `Sesión` = cualquier usuario autenticado; `Dispositivo` = `X-Device-Key`; `Público` = sin autenticación.

### Autenticación y cuentas (`auth`)

| Método | Ruta | Acceso | Descripción |
| :--- | :--- | :--- | :--- |
| POST | `/auth/login` | Público (10/min) | Inicia sesión con usuario o correo y contraseña |
| POST | `/auth/refresh` | Cookie de refresh (30/min) | Rota el refresh token y emite un access token nuevo |
| POST | `/auth/logout` | Sesión | Cierra la sesión actual |
| POST | `/auth/logout-all` | Sesión | Cierra todas las sesiones del usuario |
| GET | `/auth/me` | Sesión | Datos del usuario autenticado |
| PATCH | `/auth/profile` | Sesión | Cambia nombre o correo propio |
| POST | `/auth/change-password` | Sesión | Cambia la contraseña propia (permitido aunque deba cambiarla) |
| GET | `/users/roles` | Admin | Roles disponibles |
| GET | `/users` | Admin | Lista de cuentas |
| POST | `/users` | Admin | Crea una cuenta (HU-15) |
| GET | `/users/{user_id}` | Admin | Detalle de una cuenta |
| PATCH | `/users/{user_id}` | Admin | Cambia rol, datos o estado activo (HU-16) |
| POST | `/users/{user_id}/reset-password` | Admin | Genera una contraseña temporal |
| POST | `/users/{user_id}/unlock` | Admin | Quita el bloqueo por intentos fallidos |

### Parqueadero y tarifas

| Método | Ruta | Acceso | Descripción |
| :--- | :--- | :--- | :--- |
| GET | `/parking` | Sesión | Datos de la sede (nombre, capacidad, tiempo de apertura) |
| PATCH | `/parking` | Admin | Modifica la sede |
| GET | `/parking/occupancy` | Sesión | Cupos ocupados y disponibles |
| GET | `/tariffs` | Admin | Tarifas vigentes |
| PUT | `/tariffs/{vehicle_type}` | Admin | Modifica la tarifa de `car` o `motorcycle` (HU-13) |
| GET | `/tariffs/history` | Admin | Histórico; filtros `vehicle_type`, `date_from`, `date_to` (HU-14) |

### Transacciones

| Método | Ruta | Acceso | Descripción |
| :--- | :--- | :--- | :--- |
| POST | `/transactions/entry` | Dispositivo | Registra un ingreso. 201 si es nuevo, 200 si es un reintento sin apertura |
| POST | `/transactions/{id}/entry-gate-opened` | Dispositivo | Confirma que la talanquera de entrada abrió |
| POST | `/transactions/exit/{plate}/authorize` | Dispositivo | Autoriza la salida: 200 si está `PAID`, 402 si falta el pago, 404 sin transacción |
| POST | `/transactions/{id}/exit-confirm` | Dispositivo | Finaliza la transacción tras el `ACK` de salida |
| GET | `/transactions/inside` | Admin, Operador | Vehículos dentro; filtro `plate` (HU-18) |
| GET | `/transactions` | Admin | Historial; filtros `plate`, `vehicle_type`, `status`, `date_from`, `date_to` (HU-20) |
| GET | `/transactions/{id}` | Admin | Detalle con intentos de pago e intervenciones |

### Pago público y pantallas de carril (`public`)

| Método | Ruta | Acceso | Descripción |
| :--- | :--- | :--- | :--- |
| GET | `/public/quote/{plate}` | Público (30/min) | Minutos de permanencia y valor a pagar (HU-07) |
| GET | `/public/payment-methods` | Público | Medios disponibles: `card` (Tarjeta), `pse` (PSE), `nequi` (Nequi) |
| POST | `/public/payments` | Público (30/min) | Inicia un intento de pago y devuelve la referencia `SGP-…` (HU-08) |
| GET | `/public/payments/{reference}` | Público (120/min) | Estado del intento |
| POST | `/public/payments/{reference}/cancel` | Público (120/min) | Cancela el intento (HU-09) |
| POST | `/public/payments/{reference}/simulate` | Público (120/min) | Solo con la pasarela simulada: aprueba o rechaza el intento |
| GET | `/public/gates/{gate}/display` | Público (120/min) | Mensaje actual de la pantalla de carril `entry` o `exit` |

### Dispositivos

| Método | Ruta | Acceso | Descripción |
| :--- | :--- | :--- | :--- |
| POST | `/devices/heartbeat` | Dispositivo | Reporta el estado de cámaras y talanqueras; devuelve el tiempo de apertura y las órdenes manuales pendientes |
| POST | `/devices/events` | Dispositivo | Reporta un evento técnico; los errores abren un ticket automático (HU-24) |
| POST | `/devices/commands/{command_id}/result` | Dispositivo | Resultado de una orden de apertura manual |
| PUT | `/devices/display/{gate}` | Dispositivo | Actualiza el mensaje de la pantalla de carril |
| GET | `/devices` | Admin, Soporte | Estado de los cuatro dispositivos (HU-22) |
| GET | `/devices/events` | Admin, Soporte | Registro de eventos técnicos |

### Intervención manual

| Método | Ruta | Acceso | Descripción |
| :--- | :--- | :--- | :--- |
| POST | `/interventions/alerts` | Dispositivo | El worker crea una alerta (placa ilegible) con foto opcional |
| GET | `/interventions/alerts` | Admin, Operador | Alertas; filtro por estado |
| GET | `/interventions/alerts/{alert_id}/snapshot` | Admin, Operador | Foto JPEG de la alerta |
| POST | `/interventions/alerts/{alert_id}/resolve` | Admin, Operador | Registra la placa correcta y ordena la apertura (HU-06) |
| POST | `/interventions/alerts/{alert_id}/dismiss` | Admin, Operador | Descarta la alerta con motivo |
| POST | `/interventions/manual-entry` | Admin, Operador | Ingreso manual con placa y motivo |
| PATCH | `/interventions/transactions/{id}/plate` | Admin, Operador | Corrige la placa de un vehículo dentro |
| POST | `/interventions/gates/{gate}/open` | Admin, Operador | Apertura de contingencia con motivo obligatorio |
| GET | `/interventions/commands` | Admin, Operador | Órdenes de apertura recientes |

### Tickets técnicos

| Método | Ruta | Acceso | Descripción |
| :--- | :--- | :--- | :--- |
| POST | `/tickets` | Operador | Crea un ticket manual (HU-23) |
| GET | `/tickets` | Operador, Soporte | Lista; el Operador solo ve los suyos |
| GET | `/tickets/{ticket_id}` | Operador, Soporte | Detalle con historial |
| POST | `/tickets/{ticket_id}/take` | Soporte | Toma el ticket y lo pasa a `in_review` (HU-25) |
| PATCH | `/tickets/{ticket_id}/notes` | Soporte | Guarda diagnóstico, acciones y resultado |
| POST | `/tickets/{ticket_id}/close` | Soporte | Cierra como `solved` o `not_solved` |

### Reportes y auditoría

| Método | Ruta | Acceso | Descripción |
| :--- | :--- | :--- | :--- |
| GET | `/reports/dashboard` | Admin | Ocupación, recaudo, ingresos y salidas del día, estado de dispositivos (HU-21) |
| GET | `/reports/revenue` | Admin | Recaudo por rango de fechas, tipo de vehículo y medio de pago (HU-19) |
| GET | `/audit/actions` | Admin | Tipos de acción auditables |
| GET | `/audit` | Admin | Registros; filtros `action`, `username`, `date_from`, `date_to` (HU-27) |

La API de auditoría no expone ninguna operación de escritura, modificación ni borrado (HU-28). La prueba `test_audit_api_has_no_write_operations` lo verifica sobre el esquema OpenAPI.

## 4.3 Códigos de respuesta

| Código | Significado en SIGAP |
| :--- | :--- |
| 200 / 201 / 202 / 204 | Correcto. 202 indica que la orden de apertura quedó en cola para el worker |
| 400 | Regla de negocio incumplida: placa con transacción activa, desactivar al último administrador |
| 401 | Sin sesión, sesión vencida o credenciales incorrectas. El mensaje no dice si falló el usuario o la contraseña |
| 402 | Salida sin pago |
| 403 | Rol sin permiso o cuenta inactiva (`Usuario inactivo`) |
| 404 | Recurso inexistente o salida sin transacción activa |
| 409 | Conflicto de estado: parqueadero lleno, transacción ya pagada, alerta ya atendida, cambio de estado de ticket no permitido |
| 422 | Datos con formato inválido: placa que no corresponde al tipo, medio de pago inexistente, contraseña débil, tarifa inválida |
| 429 | Límite de peticiones superado o cuenta bloqueada temporalmente |
| 503 | Base de datos no disponible (`/health-check`) |

Todas las respuestas de error tienen la forma `{"detail": "<mensaje en español>"}`.
