# SIGAP

**Sistema Integral de Gestión y Automatización de Parqueaderos**

Plataforma integral diseñada para la automatización, control de acceso vehicular, monitoreo operativo y administración centralizada de parqueaderos. El sistema combina visión por computadora para el procesamiento y detección vehicular, un backend de alto rendimiento desarrollado en FastAPI y un frontend interactivo y responsivo construido con React, Vite y Tailwind CSS.

---

## Objetivos principales

- **Control de Acceso y Detección Vehicular:** Procesamiento y reconocimiento de vehículos y placas (ANPR/LPR) para la automatización de accesos.
- **Gestión Operativa de Patio:** Registro automatizado de ingresos y salidas, control de talanqueras, cálculo de tiempos de permanencia y validación de estados de pago.
- **Control de Acceso Basado en Roles (RBAC):** Interfaces y permisos especializados para Administradores, Operadores de Patio y Soporte Técnico.
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

- **Visión por Computadora Integrada:** Canalización modular de procesamiento de imágenes y video para detección y clasificación vehicular.
- **Gestión Integral de Usuarios:** Administración de cuentas, asignación de roles jerárquicos (`admin`, `operator`, `support`), auditoría de accesos y perfiles de usuario.
- **Consola Operativa y de Monitoreo:** Vistas especializadas para intervención manual de placas, seguimiento de cupos disponibles y reporte de incidencias en patio.
- **Seguridad Avanzada:** Almacenamiento seguro de contraseñas con Argon2 (`pwdlib`), tokens de acceso y refresco (`pyjwt`), políticas de bloqueo temporal por intentos fallidos y limitación de tasa de solicitudes (`SlowAPI`).
- **Despliegue Automatizado:** Script de automatización (`scripts/deploy.sh`) que detecta automáticamente las capacidades de hardware para optimizar las dependencias de IA (CPU vs CUDA).

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

##### Estrategia de Pruebas: Insumo de Imágenes vs Stream de Video
En esta fase del proyecto y con el fin de facilitar las **pruebas manuales, de integración y testing local** sin depender de cámaras físicas de transmisión continua de video en vivo (como streams RTSP o webcams conectadas físicamente a los carriles), el procesamiento se realiza mediante la inspección periódica de archivos de imagen dentro del directorio `backend/input/`.

La carpeta `backend/input/` cuenta con **3 subcarpetas clave**:

1. **`backend/input/entrada/` (Carril de Ingreso):**
   - Carpeta monitoreada para simular la llegada de vehículos al acceso del parqueadero.
   - Al depositar una imagen (`.jpg`, `.jpeg`, `.png`), el worker la lee con OpenCV, aplica la detección del vehículo con YOLO (`SIGAP_model_small_v1.pt`) y extrae la matrícula mediante el lector OCR (`PlateReader`).
   - Si la matrícula es reconocida, el worker envía automáticamente la petición `POST /api/v1/transactions/entry` con el payload `{"plate": "<placa>", "vehicle_type": "<tipo>"}`.
   - Si el backend autoriza el ingreso (código HTTP 200 o 201), se confirma la entrada en el sistema (y se activa la talanquera física si hay un Arduino conectado).

2. **`backend/input/salida/` (Carril de Salida):**
   - Carpeta monitoreada para simular el egreso o retiro de vehículos del parqueadero.
   - Al colocar una imagen en esta carpeta, el worker identifica la placa y realiza la petición `POST /api/v1/transactions/exit/{plate}` para verificar el estado de pago, liquidar el valor según el tiempo de permanencia y registrar la salida.

3. **`backend/input/procesadas/` (Histórico de Procesamiento):**
   - Carpeta de archivo y despacho automático. Inmediatamente después de analizar cada imagen depositada en `entrada/` o `salida/`, el worker la traslada a `procesadas/`.
   - **Propósito:** Previene que el ciclo de monitoreo continuo vuelva a procesar la misma imagen indefinidamente. En caso de que un archivo no pueda ser interpretado como imagen válida, se renombra como `error_{archivo}` y se traslada aquí para fines de auditoría.

> [!TIP]
> **Imágenes de salida con detecciones:**
> Adicionalmente a las subcarpetas de `input/`, el worker genera en `backend/output/` una copia de cada captura procesada con los recuadros delimitadores (*bounding boxes*) de la detección visual dibujados sobre la imagen original (`detected_{archivo}`).

##### Ejecución automática con `deploy.sh`

- **En Linux / WSL2:**
  ```bash
  ./scripts/deploy.sh worker
  ```

- **En Windows (Git Bash):**
  ```bash
  sh scripts/deploy.sh worker
  ```

*Este comando realiza automáticamente:*
1. La asignación de la variable de entorno `API_URL="http://localhost:8000/api/v1"`.
2. El cambio al directorio `backend/`.
3. La creación automática de las carpetas de trabajo (`backend/input/entrada`, `backend/input/salida` y `backend/input/procesadas`).
4. La ejecución del script en el entorno virtual mediante `uv run python scripts/camera_worker.py`.

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
├── backend/                       # Servicio backend y modelos de IA
│   ├── core/                      # Configuración general, base de datos, seguridad y rate limiting
│   ├── input/                     # Insumos de prueba para detección (reemplazo de stream de video)
│   │   ├── entrada/               # Carril de ingreso (imágenes simuladas para registro de entrada)
│   │   ├── salida/                # Carril de salida (imágenes simuladas para registro de salida)
│   │   └── procesadas/            # Histórico de imágenes procesadas automáticamente
│   ├── models/                    # Pesos y artefactos de modelos de visión
│   ├── output/                    # Capturas resultantes con bounding boxes de detección
│   ├── scripts/                   # Scripts auxiliares y workers (camera_worker.py)
│   ├── src/
│   │   ├── server/                # Aplicación FastAPI, routers (auth, usuarios) y ciclo de vida
│   │   ├── processing/            # Pipelines y utilidades de procesamiento de video e imagen
│   │   ├── inference/             # Rutinas de inferencia y detección vehicular/placas
│   │   └── training/              # Scripts auxiliares de entrenamiento
│   ├── tests/                     # Suite de pruebas automatizadas con pytest
│   ├── Dockerfile                 # Contenedor multi-etapa para backend
│   └── pyproject.toml             # Configuración de dependencias con uv
├── frontend/                      # Aplicación cliente web
│   ├── app/
│   │   ├── routes/                # Rutas del aplicativo (Login, Dashboard, Usuarios, etc.)
│   │   ├── components/            # Componentes reutilizables de UI, navegación y modales
│   │   ├── context/               # Proveedores de estado (AuthContext, ToastContext)
│   │   ├── services/              # Clientes HTTP para consumo de endpoints
│   │   └── app.css                # Estilos globales y tokens del tema
│   ├── public/                    # Recursos estáticos y tipografías
│   ├── Dockerfile                 # Contenedor para desarrollo y producción
│   └── nginx.conf                 # Configuración de servidor web para producción
├── scripts/
│   └── deploy.sh                  # Script de automatización para gestión de contenedores
├── compose.dev.yml                # Definición de servicios para desarrollo
├── compose.prod.yml               # Definición de servicios para producción
└── .env.example                   # Plantilla de variables de entorno
```

---

## Pruebas

Para ejecutar las pruebas unitarias y de integración del backend:

```bash
cd backend
pytest
```