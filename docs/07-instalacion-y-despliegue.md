# 7. Manual de instalación y despliegue

Este manual complementa la sección **Cómo comenzar** del [README](../README.md), que explica en detalle cada comando de `scripts/deploy.sh` en Linux, WSL2 y Windows.

## 7.1 Requisitos

| Equipo | Requisito |
| :--- | :--- |
| Servidor | Docker Engine 24 o superior con Docker Compose v2. En Windows, Docker Desktop con WSL2 |
| Servidor | Puerto 80 libre (producción) o 3000, 8000 y 5432 (desarrollo) |
| Servidor, opcional | GPU NVIDIA con NVIDIA Container Toolkit |
| Equipo del parqueadero | Python 3.12, [`uv`](https://docs.astral.sh/uv/), drivers de las cámaras y del Arduino |
| Equipo del parqueadero | Arduino con el sketch cargado (ver [05-hardware.md](05-hardware.md)) |

En producción, el contenedor `api` solo publica el puerto 8000 en `127.0.0.1`. Hay dos formas de ubicar el worker:

- **En el mismo equipo que el servidor** (configuración de `deploy.sh worker`): `API_URL=http://localhost:8000/api/v1`.
- **En otro equipo de la red:** `API_URL=http://<servidor>/api/v1`, a través de Nginx.

## 7.2 Configuración

```bash
cp .env.example .env
```

Antes del primer arranque en producción cambie obligatoriamente:

| Variable | Valor recomendado |
| :--- | :--- |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |
| `SECRET_KEY` | Cadena aleatoria de al menos 32 caracteres |
| `DEVICE_API_KEY` | Cadena aleatoria de al menos 16 caracteres; la API no arranca sin ella |
| `FIRST_SUPERUSER_PASSWORD` | Contraseña robusta, distinta de la del ejemplo |
| `POSTGRES_PASSWORD` | Contraseña robusta |
| `FRONTEND_URL` | URL pública del sistema, por ejemplo `https://sigap.midominio.co` |
| `ARDUINO_PORT` | Puerto real del Arduino (`COM3`, `/dev/ttyACM0`…) |
| `CAM_ENTRY_INDEX`, `CAM_EXIT_INDEX` | Índices reales de las cámaras |

Para generar las claves:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

El archivo `.env` contiene secretos: no lo suba al repositorio (ya está en `.gitignore`) ni lo envíe por correo.

## 7.3 HTTPS en producción (obligatorio)

Con `ENVIRONMENT=production`, la API marca las cookies de sesión como `Secure` y `SameSite=Strict`. Los navegadores **no envían cookies `Secure` por HTTP**, salvo cuando el sitio se abre en `localhost`. El contenedor `frontend` incluido escucha solo en el puerto 80 sin TLS, así que, si el panel se abre desde otro equipo por `http://`, el inicio de sesión no se mantiene.

Antes de publicar el sistema en la red:

1. Ponga delante un proxy con certificado TLS (por ejemplo Caddy, Traefik o Nginx con Let's Encrypt, o el balanceador del proveedor) que redirija al puerto 80 del contenedor `frontend`.
2. Configure `FRONTEND_URL` con la dirección `https://`.

Para una demostración en un solo equipo basta con abrir `http://localhost`.

## 7.4 Puesta en marcha

### Producción

```bash
bash scripts/deploy.sh prod
```

Al arrancar, el contenedor `api` ejecuta `scripts/prestart.py`, que:

1. Espera hasta 60 s a que PostgreSQL acepte conexiones.
2. Aplica las migraciones de Alembic pendientes.
3. Carga los datos iniciales si faltan: sede principal (50 cupos, 3 s de apertura), los tres roles, el superusuario de `FIRST_SUPERUSER`, las tarifas de ejemplo y los cuatro dispositivos.

Verificación:

```bash
curl http://localhost:8000/health-check
```

Debe responder `{"status":"ok","database":"connected"}`. Luego abra `http://localhost` e inicie sesión con `FIRST_SUPERUSER` / `FIRST_SUPERUSER_PASSWORD`.

### Worker de cámaras

En el equipo del parqueadero, con el Arduino conectado:

```bash
cd backend
uv sync --extra cu130   # con GPU NVIDIA; sin GPU: uv sync --extra cpu
```

```bash
bash scripts/deploy.sh worker
```

En **Dispositivos** las cuatro filas deben pasar a **Conectado** en menos de 10 segundos.

### Primera configuración (Administrador)

1. **Parqueadero:** nombre, dirección, capacidad real y segundos de apertura.
2. **Tarifas:** valores reales de carro y moto. Cada cambio queda en el histórico.
3. **Usuarios:** cree las cuentas de Operador y Soporte. Cada cuenta nueva debe cambiar la contraseña en su primer ingreso.
4. Cambie la contraseña del superusuario desde el menú de perfil.

## 7.5 Actualización

```bash
git pull
bash scripts/deploy.sh prod
```

`docker compose up --build` reconstruye las imágenes y `prestart.py` aplica las migraciones nuevas sin borrar datos. Haga un respaldo antes de cada actualización (ver [03-modelo-de-datos.md](03-modelo-de-datos.md#34-respaldo-y-restauración)).

## 7.6 Operación

| Tarea | Comando |
| :--- | :--- |
| Ver registros de producción | `docker compose -f compose.prod.yml logs -f` (`deploy.sh logs` muestra solo los de desarrollo) |
| Detener | `bash scripts/deploy.sh down` |
| Limpiar contenedores e imágenes sin uso | `bash scripts/deploy.sh clean` |
| Respaldo diario | `pg_dump` (sección 3.4), programado con `cron` o el Programador de tareas |

Los datos de PostgreSQL viven en el volumen `db_data_prod`. Ni `deploy.sh down` ni `deploy.sh clean` lo borran: `clean` solo elimina contenedores detenidos e imágenes sin uso.

## 7.7 Solución de problemas

| Síntoma | Causa probable | Solución |
| :--- | :--- | :--- |
| `could not select device driver "nvidia"` | El equipo no tiene GPU NVIDIA o falta el Container Toolkit | Comente `deploy.resources.reservations.devices` en el archivo compose |
| La API no arranca y menciona `DEVICE_API_KEY` | Falta la clave o tiene menos de 16 caracteres | Defínala en `.env` |
| `/health-check` responde 503 | PostgreSQL no está disponible | Revise `docker compose ps` y los registros del contenedor `db` |
| El login funciona en `localhost` pero no desde otro equipo | Cookies `Secure` sobre HTTP | Configure HTTPS (sección 7.3) |
| Las talanqueras aparecen **Sin comunicación** | Puerto `ARDUINO_PORT` incorrecto, Monitor Serie abierto o sketch sin cargar | Corrija el puerto, cierre el Monitor Serie y verifique `READY` |
| Todos los dispositivos aparecen **Sin comunicación** | El worker está detenido o no alcanza la API | Inicie el worker y revise `API_URL` |
| El worker responde 401 | `DEVICE_API_KEY` distinta entre servidor y worker | Use el mismo `.env` o la misma clave |
| Una cámara aparece con **Error** | Índice incorrecto o cámara ocupada por otro programa | Ajuste `CAM_ENTRY_INDEX` / `CAM_EXIT_INDEX` |
| La cuenta queda bloqueada | 5 intentos fallidos | Espere 15 minutos o desbloquéela desde **Usuarios** |
