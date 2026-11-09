# SIGAP

**Sistema Integral de Gestión y Automatización de Parqueaderos**

Plataforma integral diseñada para la automatización, control de acceso vehicular, monitoreo operativo y administración centralizada de parqueaderos. El sistema combina visión por computadora para el procesamiento y detección vehicular, un backend de alto rendimiento desarrollado en FastAPI y un frontend interactivo y responsivo construido con React, Vite y Tailwind CSS.

---

## Objetivos principales

- **Control de Acceso y Detección Vehicular:** Procesamiento y reconocimiento de vehículos y placas (ANPR/LPR) para la automatización de accesos.
- **Gestión Operativa de Patio:** Registro automatizado de ingresos y salidas, control de talanqueras, cálculo de tiempos de permanencia y validación de estados de pago.
- **Control de Acceso Basado en Roles (RBAC):** Interfaces y permisos especializados para Administradores, Operadores y Soporte Técnico.
- **API Robusta y Segura:** Endpoints RESTful documentados con OpenAPI, autenticación segura basada en tokens JWT rotativos, rate limiting y protección contra ataques de fuerza bruta.
- **Arquitectura Lista para Contenedores:** Entornos reproducibles y aislados mediante Docker Compose con soporte automático para aceleración por hardware (NVIDIA GPU / CUDA) o CPU.

---

## Índice

- [Características](#características)
- [Stack tecnológico](#stack-tecnológico)
- [Cómo comenzar](#cómo-comenzar)
  - [Requisitos](#requisitos)
  - [Inicio rápido (Docker)](#inicio-rápido-docker)
  - [Worker de Cámaras (camera_worker.py)](#4-ejecución-del-worker-de-cámaras-camera_workerpy)
- [Configuración del Sistema (.env)](#configuración-del-sistema-env)
- [Documentación de la API](#documentación-de-la-api)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Pruebas](#pruebas)

---

## Características

- **Ingreso y salida automáticos:** lectura de placa con YOLO y EasyOCR, validación de formato, cupos y duplicados, y apertura de talanquera solo con autorización del backend y confirmación del Arduino.
- **Tarifas configurables:** valor por hora y fracción, tarifa plena después del límite de permanencia, nuevo período cada 12 horas e histórico inmutable de cambios.
- **Módulo de pago público:** el conductor consulta el valor por placa y paga mediante una pasarela intercambiable (hoy simulada, sin dinero real), con reintentos y vencimiento.
- **Intervención manual:** alertas con foto para el Operador, corrección de placa, ingreso manual y apertura de contingencia con motivo obligatorio.
- **Soporte técnico:** estado de cámaras y talanqueras en tiempo real, eventos técnicos y tickets manuales o automáticos con historial.
- **Auditoría inmutable:** cada acción relevante queda registrada y un trigger de PostgreSQL rechaza cualquier modificación.
- **Seguridad:** contraseñas con Argon2, JWT rotativos en cookies httpOnly, bloqueo por intentos fallidos, rate limiting y clave de dispositivo para el worker.

---

## Stack tecnológico

- **Backend:**
  - Python 3.12+
  - FastAPI (Framework web asíncrono y OpenAPI)
  - SQLModel & SQLAlchemy Async (ORM y modelado de datos)
  - Psycopg 3 (Driver asíncrono de PostgreSQL)
  - PyTorch & Torchvision (Inferencia de modelos de visión)
  - Loguru (Sistema estructurado de logging)
  - SlowAPI (Control y limitación de peticiones)
- **Frontend:**
  - React 19 & TypeScript
  - React Router
  - Vite (Empaquetador y entorno de desarrollo)
  - Tailwind CSS v4 (Sistema de diseño y modo oscuro)
  - Lucide React (Librería de iconografía)
- **Base de Datos:**
  - PostgreSQL 16 Alpine
- **Infraestructura & DevOps:**
  - Docker & Docker Compose
  - Nginx (Servidor web y proxy inverso en producción)
  - uv (Gestión de paquetes y dependencias en backend)

---

## Cómo comenzar

### Requisitos

- **Docker y Docker Compose** (**Obligatorio**).
- **Git**.
- **uv** (Recomendado para la ejecución en el Host del worker de cámaras con Python 3.12+).
- *(Opcional)* **GPU NVIDIA** con controladores y **NVIDIA Container Toolkit** configurado para aceleración CUDA en inferencia.

---

### Inicio rápido (Docker)

> [!IMPORTANT]
> Debido a las dependencias de red, enlaces entre servicios (frontend, backend, base de datos) y configuraciones de entorno, el proyecto está **diseñado exclusivamente para ejecutarse mediante Docker** (tanto en modo desarrollo como en producción).

El proyecto incluye un script auxiliar (`scripts/deploy.sh`) que facilita la administración del ciclo de vida de los contenedores y la selección automática del entorno de ejecución (CPU o GPU/CUDA).

#### 1. Configurar variables de entorno
Copia la plantilla de configuración y define tus credenciales:
```bash
cp .env.example .env
```

#### 2. Configuración de Hardware (CUDA / GPU)
El script `scripts/deploy.sh` detecta automáticamente si el host cuenta con una GPU NVIDIA accesible vía `nvidia-smi` para configurar la variante correcta (`cpu` o `cu130`).

> [!TIP]
> **Soporte de GPU en Docker:**
> Los archivos `compose.dev.yml` y `compose.prod.yml` tienen reservado el dispositivo GPU por defecto:
> - **En Linux:** Verifica tener instalado el [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).
> - **En Windows:** Ejecuta el proyecto desde **WSL2** con Docker Desktop y la integración WSL habilitada.
>
> **Si tu equipo no cuenta con GPU NVIDIA:**
> Comenta o remueve la sección `deploy.resources.reservations.devices` en `compose.dev.yml` y `compose.prod.yml` para evitar el error de controlador de Docker (`could not select device driver`).

#### 3. Ejecución del proyecto

El proyecto centraliza sus operaciones de despliegue y administración a través del script de automatización [`scripts/deploy.sh`](file:///home/srvenient/eternal-dev/fullstack/SIGAP/scripts/deploy.sh). A continuación se detalla cómo ejecutarlo en los diferentes sistemas operativos:

##### A. En Linux / WSL2
1. Otorga permisos de ejecución al script (solo la primera vez):
   ```bash
   chmod +x ./scripts/deploy.sh
   ```
2. Ejecuta el comando deseado directamente con `./scripts/deploy.sh <comando>` o explícitamente mediante `bash scripts/deploy.sh <comando>`.

##### B. En Windows (Git Bash / WSL)
Dado que los scripts de automatización del proyecto están escritos en sintaxis Bash con comandos estándar de Unix/POSIX, para ejecutarlos en Windows se cuenta con las siguientes opciones:

- **Opción recomendada: Git Bash** (incluido al instalar [Git for Windows](https://gitforwindows.org/)):
  Abre la terminal de **Git Bash** en la raíz del proyecto y ejecuta:
  ```bash
  sh scripts/deploy.sh <comando>
  # O alternativamente:
  bash scripts/deploy.sh <comando>
  ```
  *(Nota: En Git Bash no es indispensable el comando `chmod +x` ya que la invocación directa con `sh` o `bash` delega la interpretación al ejecutable de Bash en Windows).*

- **Opción WSL2 (Windows Subsystem for Linux):**
  Abre tu terminal de distribución Linux (Ubuntu, Debian, etc.), navega a la ruta del proyecto y utiliza `./scripts/deploy.sh <comando>`.

- **Opción PowerShell / CMD:**
  Si tienes Git instalado y configurado en la variable de entorno `PATH` del sistema, puedes invocar Bash directamente:
  ```powershell
  bash scripts/deploy.sh <comando>
  ```

##### Comandos disponibles en `deploy.sh`

| Modo / Comando | Sintaxis (Linux / WSL) | Sintaxis (Windows - Git Bash) | Descripción |
| :--- | :--- | :--- | :--- |
| **Desarrollo** | `./scripts/deploy.sh dev` | `sh scripts/deploy.sh dev` | Levanta la base de datos (puerto 5432), backend FastAPI (puerto 8000) y frontend Vite (puerto 3000). |
| **Hot-Reload (Watch)** | `./scripts/deploy.sh dev-watch` | `sh scripts/deploy.sh dev-watch` | Sincroniza cambios de código en caliente sin reiniciar contenedores. |
| **Producción** | `./scripts/deploy.sh prod` | `sh scripts/deploy.sh prod` | Despliegue optimizado en segundo plano (*detached*) servido por Nginx (puerto 80). |
| **Worker de Cámaras** | `./scripts/deploy.sh worker` | `sh scripts/deploy.sh worker` | Ejecuta el worker perimetral de visión artificial (LPR/ANPR) en el Host. |
| **Detener entorno** | `./scripts/deploy.sh down` | `sh scripts/deploy.sh down` | Detiene y remueve los contenedores activos. |
| **Ver registros** | `./scripts/deploy.sh logs` | `sh scripts/deploy.sh logs` | Muestra el registro en tiempo real de los contenedores Docker. |
| **Limpieza Docker** | `./scripts/deploy.sh clean` | `sh scripts/deploy.sh clean` | Detiene los contenedores y ejecuta limpieza del sistema Docker. |

#### 4. Ejecución del Worker de Cámaras (camera_worker.py)

El script [`backend/scripts/camera_worker.py`](file:///home/srvenient/eternal-dev/fullstack/SIGAP/backend/scripts/camera_worker.py) opera como el agente perimetral de visión por computadora (LPR/ANPR). Se encarga de procesar las capturas vehiculares, detectar vehículos y placas mediante YOLO y OCR, y enviar automáticamente las transacciones al backend para la apertura de talanqueras o control de acceso vehicular.

Debido a su interacción con hardware local (cámaras USB/RTSP o microcontroladores como Arduino), el script está diseñado para ejecutarse nativamente en el Host utilizando `uv`.

> [!IMPORTANT]
> Antes de iniciar el worker, asegúrate de tener el backend en ejecución (mediante `./scripts/deploy.sh dev` o `./scripts/deploy.sh prod`) para que los endpoints de la API estén disponibles en `http://localhost:8000/api/v1`.

##### Cómo funciona
El worker lee las cámaras de entrada y salida (`CAM_ENTRY_INDEX`, `CAM_EXIT_INDEX`), confirma cada placa con tres lecturas iguales y consulta al backend. Se autentica con `DEVICE_API_KEY` y reporta el estado de los dispositivos cada 5 segundos.

La talanquera se controla por serial con el sketch [`arduino/sigap_talanquera/sigap_talanquera.ino`](arduino/sigap_talanquera/sigap_talanquera.ino), que **debe cargarse en el Arduino**: el worker espera su confirmación `ACK` y trata como fallo cualquier orden sin respuesta. El `ACK` confirma que el Arduino activó el relé, no que la barrera se haya movido; sin sensor de paso, el cierre es por tiempo y se configura en **Parqueadero**.

| Pantalla | Ruta | Acceso |
| :--- | :--- | :--- |
| Módulo de pago | `/pago` | Público |
| Pantalla del carril de ingreso | `/punto/ingreso` | Público |
| Pantalla del carril de salida | `/punto/salida` | Público |
| Panel de administración | `/` | Usuario y contraseña |

##### Ejecución automática con `deploy.sh`

- **En Linux / WSL2:**
  ```bash
  ./scripts/deploy.sh worker
  ```

- **En Windows (Git Bash):**
  ```bash
  sh scripts/deploy.sh worker
  ```

*Este comando asigna `API_URL="http://localhost:8000/api/v1"`, carga el `.env` y ejecuta `uv run --no-sync python scripts/camera_worker.py` desde `backend/`.*

##### Ejecución manual alternativa en el Host

Si prefieres ejecutar el worker de forma directa en tu terminal sin usar `deploy.sh`:

- **En Linux / WSL2 / Git Bash (Windows):**
  ```bash
  cd backend
  export API_URL="http://localhost:8000/api/v1"
  uv run python scripts/camera_worker.py
  ```

- **En Windows (PowerShell):**
  ```powershell
  cd backend
  $env:API_URL="http://localhost:8000/api/v1"
  uv run python scripts/camera_worker.py
  ```

- **En Windows (CMD):**
  ```cmd
  cd backend
  set API_URL=http://localhost:8000/api/v1
  uv run python scripts/camera_worker.py
  ```

---

## Configuración del Sistema (.env)

Todos los valores de configuración del proyecto se gestionan mediante el archivo `.env` en la raíz del proyecto, tomando como referencia [.env.example](file:///home/srvenient/eternal-dev/fullstack/SIGAP/.env.example).

### 1. Configuración General del Entorno
| Variable | Descripción | Valor por Defecto / Opciones |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Entorno de ejecución de la aplicación. | `local` (o `production`) |
| `DEVICE_TYPE` | Tipo de dispositivo para procesamiento e inferencia de IA. Configurado automáticamente por `scripts/deploy.sh`. | `cpu` (o `cu130`) |
| `DEBUG` | Habilita o deshabilita el modo de depuración (`true` o `false`). | `true` |
| `LOG_LEVEL` | Nivel de detalle de los registros (*logs*). | `info` (`debug`, `warn`, `error`) |

### 2. Información del Proyecto
| Variable | Descripción | Valor por Defecto / Opciones |
| :--- | :--- | :--- |
| `PROJECT_NAME` | Nombre identificador del proyecto. | `sigap` |
| `PROJECT_VERSION` | Versión actual de la aplicación. | `0.0.1` |

### 3. Configuración de la API
| Variable | Descripción | Valor por Defecto / Opciones |
| :--- | :--- | :--- |
| `SECRET_KEY` | Clave secreta criptográfica para la firma y validación de tokens JWT. *(Cambiar por una cadena segura en local/producción)*. | `tu_clave_secreta_aqui` |
| `FRONTEND_URL` | URL base del frontend para permitir solicitudes CORS y redirecciones. | `http://localhost:3000` |
| `FIRST_SUPERUSER` | Nombre de usuario inicial para la cuenta del primer superadministrador. | `admin` |
| `FIRST_SUPERUSER_PASSWORD` | Contraseña asignada a la cuenta del primer superadministrador. | `admin123` |
| `DEVICE_API_KEY` | Clave con la que el worker se autentica ante la API. **Obligatoria**, mínimo 16 caracteres. | *(sin valor por defecto)* |
| `PAYMENT_GATEWAY` | Pasarela de pago. Solo existe la simulada, que no cobra dinero real. | `simulated` |
| `PAYMENT_TIMEOUT_SECONDS` | Segundos que espera la confirmación de un pago. | `180` |

### 4. Configuración de la Base de Datos (PostgreSQL)
| Variable | Descripción | Valor por Defecto / Opciones |
| :--- | :--- | :--- |
| `POSTGRES_USER` | Nombre de usuario para la conexión a PostgreSQL. | `postgres` |
| `POSTGRES_PASSWORD` | Contraseña del usuario de PostgreSQL. | `tu_contraseña_aqui` |
| `POSTGRES_SERVER` | Dirección del host del servidor de base de datos en Docker. | `db` |
| `POSTGRES_PORT` | Puerto de conexión a PostgreSQL. | `5432` |
| `POSTGRES_DB` | Nombre de la base de datos a utilizar para el proyecto. | `sigap_db` |

---

## Documentación de la API

Con el backend en ejecución, puedes acceder a la documentación interactiva autogenerada y validación de endpoints:

- **Swagger UI:** [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)
- **ReDoc:** [http://localhost:8000/api/v1/redoc](http://localhost:8000/api/v1/redoc)
- **Esquema OpenAPI (JSON):** [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/api/v1/openapi.json)
- **Verificación de Estado (Health Check):** [http://localhost:8000/health-check](http://localhost:8000/health-check)

---

## Estructura del Proyecto

```text
SIGAP/
├── arduino/sigap_talanquera/      # Sketch del Arduino que controla los relés
├── backend/
│   ├── core/                      # Configuración, base de datos, seguridad y rate limiting
│   ├── migrations/                # Migraciones de Alembic
│   ├── models/                    # Pesos del modelo YOLO
│   ├── scripts/                   # camera_worker.py y prestart.py
│   ├── src/
│   │   ├── server/                # API FastAPI, un módulo por dominio:
│   │   │                          # auth, parking, tariff, transaction, payment, device,
│   │   │                          # intervention, ticket, audit y reporting
│   │   ├── worker/                # Control del Arduino y flujo de cada carril
│   │   ├── inference/             # Detección y lectura de placas
│   │   └── processing/            # Procesamiento de imagen y texto
│   └── tests/                     # Pruebas con pytest
├── frontend/
│   ├── app/routes/                # Pantallas por rol y pantallas públicas
│   ├── app/components/            # Componentes de interfaz
│   ├── app/services/              # Clientes HTTP
│   ├── app/app.css                # Identidad visual y tokens
│   └── nginx.conf                 # Servidor web de producción
├── scripts/deploy.sh              # Gestión de contenedores
├── compose.dev.yml
├── compose.prod.yml
└── .env.example
```

---

## Pruebas

Las pruebas usan una base PostgreSQL propia en el puerto 5433 y nunca tocan la de desarrollo:

```bash
docker compose -f compose.dev.yml --profile test up -d db_test
cd backend
uv run --no-sync pytest
```
