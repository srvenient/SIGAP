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

Otorga permisos de ejecución al script:
```bash
chmod +x ./scripts/deploy.sh
```

Utiliza los siguientes comandos según el modo requerido:

- **Modo Desarrollo:** Levanta la base de datos (puerto 5432), el backend de FastAPI (puerto 8000) y el frontend con Vite (puerto 3000):
  ```bash
  ./scripts/deploy.sh dev
  ```

- **Modo Desarrollo con Hot-Reload (Watch):** Sincroniza cambios de código en tiempo real sin reiniciar contenedores:
  ```bash
  ./scripts/deploy.sh dev-watch
  ```

- **Modo Producción:** Despliegue optimizado en segundo plano (*detached*), con el frontend servido por Nginx en el puerto 80 enrutando solicitudes hacia la API:
  ```bash
  ./scripts/deploy.sh prod
  ```

- **Comandos de Mantenimiento:**
  - `./scripts/deploy.sh down`: Detiene y remueve los contenedores activos.
  - `./scripts/deploy.sh logs`: Muestra el registro en tiempo real de los contenedores.
  - `./scripts/deploy.sh clean`: Detiene el entorno y realiza una limpieza del sistema Docker.

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
│   ├── models/                    # Pesos y artefactos de modelos de visión
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