# 9. Documento de seguridad

## 9.1 Controles implementados

### Autenticación (HU-17)

| Control | Implementación | Configuración |
| :--- | :--- | :--- |
| Hash de contraseñas | Argon2 mediante `pwdlib` ([`core/security.py`](../backend/core/security.py)); nunca se guarda texto plano | — |
| Política de contraseñas (HU-15) | De 8 a 40 caracteres, con al menos una mayúscula, una minúscula y un número | `require_strong_password` en `user.py` |
| Mensaje de error genérico | `Usuario o correo y contraseña incorrectos`, sin indicar qué campo falló | — |
| Protección contra enumeración de usuarios | Si el usuario no existe se verifica igual contra un hash ficticio, para que el tiempo de respuesta no lo delate | `DUMMY_HASHED_PASSWORD` |
| Bloqueo por intentos fallidos | 5 intentos fallidos bloquean la cuenta 15 minutos (respuesta 429) | `FAILED_LOGIN_ATTEMPTS`, `LOCKOUT_DURATION_MINUTES` |
| Cuenta desactivada | Responde 403 `Usuario inactivo` solo si la contraseña era correcta | — |
| Cambio obligatorio de contraseña | Cuentas nuevas y contraseñas restablecidas deben cambiarse en el primer ingreso | `must_change_password` |

### Sesión

| Control | Implementación |
| :--- | :--- |
| Tokens | JWT HS256 de acceso (15 min) con `aud`, `jti`, `iat`, `nbf` y `exp` obligatorios |
| Renovación | Refresh token rotativo de 7 días, con vencimiento absoluto de la sesión a los 15 días |
| Detección de robo de token | Si un refresh token ya rotado se reutiliza después de 30 s de gracia, se revoca toda la familia de la sesión |
| Almacenamiento del refresh token | Solo su hash SHA-256 en la tabla `refresh_tokens` |
| Cookies | `httpOnly` siempre; en producción también `Secure` y `SameSite=Strict` |
| Invalidación al cambiar contraseña | Los access tokens emitidos antes de `password_changed_at` se rechazan |
| Cierre de sesión | `logout` (sesión actual) y `logout-all` (todas las sesiones) |

### Autorización (HU-17)

Cada endpoint valida el rol en el backend con `require_roles(...)` ([`auth/api/deps.py`](../backend/src/server/auth/api/deps.py)). El menú del frontend solo oculta opciones ([`lib/access.ts`](../frontend/app/lib/access.ts)); aunque alguien escriba la URL a mano, la API responde 403. La prueba `test_permission_matrix` recorre los endpoints con cada rol.

Matriz de permisos:

| Funcionalidad | Administrador | Operador | Soporte | Conductor |
| :--- | :---: | :---: | :---: | :---: |
| Panel (dashboard) | Completo | Operativo | Técnico | — |
| Vehículos dentro | Sí | Sí | — | — |
| Alertas e intervención manual | Sí | Sí | — | — |
| Transacciones y recaudo | Sí | — | — | — |
| Tarifas e histórico | Sí | — | — | — |
| Usuarios | Sí | — | — | — |
| Parqueadero | Sí | — | — | — |
| Auditoría | Sí | — | — | — |
| Dispositivos y eventos técnicos | Sí | — | Sí | — |
| Crear tickets | — | Sí (ve solo los suyos) | — | — |
| Atender tickets | — | — | Sí | — |
| Consultar valor y pagar (`/pago`) | — | — | — | Sí |
| Pantallas de carril (`/punto/*`) | — | — | — | Sí |

### Dispositivos

- El worker se autentica con el encabezado `X-Device-Key`. La clave es obligatoria y debe tener al menos 16 caracteres; sin ella la API no arranca.
- El worker no decide aperturas: el backend autoriza cada ingreso y salida, y las aperturas manuales viajan como órdenes que vencen a los 60 s.
- El backend ignora el estado y el valor que envíe el cliente al registrar un ingreso (`test_entry_ignores_client_supplied_status_and_amount`).

### Rutas públicas

| Ruta | Límite por IP |
| :--- | :--- |
| `/auth/login` | 10 por minuto |
| `/auth/refresh`, `/auth/profile`, `/auth/change-password` | 30 por minuto |
| `/public/quote/{plate}`, `POST /public/payments` | 30 por minuto |
| Demás rutas `/public/*` | 120 por minuto |

La referencia de pago `SGP-…` tiene 24 caracteres aleatorios (`secrets.token_urlsafe(18)`), así que no se puede adivinar para consultar o cancelar el pago de otra persona.

### Auditoría e integridad (HU-26 a HU-28)

- Las acciones relevantes se registran en `audit_logs` con usuario (o `sistema`), fecha, elemento afectado, resultado y detalle.
- Las consultas no generan registros (`test_queries_do_not_generate_audit_records`).
- `audit_logs`, `tariff_history` y `ticket_history` están protegidas por triggers de PostgreSQL que rechazan `UPDATE`, `DELETE` y `TRUNCATE` ([03-modelo-de-datos.md](03-modelo-de-datos.md#33-inmutabilidad)).
- La API de auditoría solo tiene operaciones de lectura.

### Infraestructura

- En producción, la API solo publica el puerto 8000 en `127.0.0.1`; desde la red solo es accesible a través de Nginx.
- PostgreSQL no publica puertos en producción.
- Los montos se manejan como `Decimal` y `Numeric(12,2)`.
- Todas las consultas pasan por SQLAlchemy con parámetros, sin SQL armado con texto del usuario.

## 9.2 Tratamiento de datos personales

Según la Ley 1581 de 2012 (Colombia), la placa asociada a fechas y horas de ingreso y salida, y las fotos de los vehículos, son datos personales.

| Dato | Dónde se guarda | Recomendación |
| :--- | :--- | :--- |
| Placa, horas de ingreso y salida | `transactions` | Definir un tiempo de conservación y publicar una política de tratamiento en el parqueadero |
| Fotos de alertas | `alert_snapshots` | Solo se guardan cuando la placa no se pudo leer; definir su tiempo de conservación |
| Fotos de detecciones del worker | Carpeta `backend/output/` del equipo del parqueadero | Programar su borrado periódico. **Hoy hay imágenes de placas en el repositorio que deben retirarse** |
| Datos del personal | `users` | Acceso solo para el Administrador |

## 9.3 Riesgos conocidos y recomendaciones

| Riesgo | Severidad | Recomendación |
| :--- | :--- | :--- |
| El contenedor `frontend` no tiene TLS y, sin HTTPS, las cookies `Secure` no funcionan fuera de `localhost` | Alta para un despliegue real | Poner un proxy con certificado delante (ver [07-instalacion-y-despliegue.md](07-instalacion-y-despliegue.md#73-https-en-producción-obligatorio)) |
| `POST /public/payments/{reference}/simulate` permite a cualquiera aprobar un pago | Alta si se usa en producción | Solo existe con la pasarela simulada. Al conectar una pasarela real, el resultado debe llegar por un webhook firmado y este endpoint debe quedar deshabilitado |
| Clave de dispositivo única y compartida | Media | Rotarla periódicamente; a futuro, una clave por equipo o certificado de cliente |
| El límite de peticiones se guarda en memoria | Baja | Con varias réplicas de la API, usar Redis en `RATE_LIMIT_STORAGE_URI` |
| Credenciales iniciales en `.env.example` | Media | Cambiar `FIRST_SUPERUSER_PASSWORD`, `SECRET_KEY` y `POSTGRES_PASSWORD` antes del primer arranque |
| Imágenes de placas y archivos `.pt` en el historial de Git | Media | Retirar `backend/output/` del repositorio; el historial de Git conserva las versiones anteriores, así que para eliminarlas por completo hay que reescribirlo |
