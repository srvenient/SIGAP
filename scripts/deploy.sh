#!/usr/bin/env bash

# Detener el script si hay un error
set -e

# 1. Ir a la raíz del proyecto (asumiendo que el script está en la carpeta /scripts o en la raíz)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"
if [[ "$SCRIPT_DIR" == *"scripts"* ]]; then
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
    PROJECT_ROOT="$SCRIPT_DIR"
fi
cd "$PROJECT_ROOT"

# 2. Cargar variables de entorno del .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
else
    echo "Error: Archivo .env no encontrado en la raíz del proyecto."
    exit 1
fi

# 3. Detección automática de hardware (CPU vs CUDA)
DEVICE_TYPE="cpu"
if command -v nvidia-smi &> /dev/null; then
    DEVICE_TYPE="cu130"
fi
export DEVICE_TYPE

echo "--------------------------------------------------------"
echo "Project:     ${PROJECT_NAME:-"sigap"} v${PROJECT_VERSION:-"0.0.1"}"
echo "Hardware:    ${DEVICE_TYPE^^}"
echo "--------------------------------------------------------"

# 4. Menú de comandos
COMMAND=$1

case "$COMMAND" in
  dev)
    echo "=> Iniciando en modo DESARROLLO..."
    docker compose -f compose.dev.yml up --build
    ;;

  dev-watch)
    echo "=> Iniciando en modo WATCH (Hot-reload activo)..."
    echo "=> Presiona Ctrl+C para detener."
    docker compose -f compose.dev.yml watch
    ;;

  prod)
    echo "=> Desplegando en PRODUCCIÓN (Detached)..."
    docker compose -f compose.prod.yml up -d --build
    echo "--------------------------------------------------------"
    echo "Despliegue completo."
    echo "Sistema enrutado detrás de Nginx en: http://localhost:80"
    echo "--------------------------------------------------------"
    ;;

  down)
    echo "=> Deteniendo todos los contenedores..."
    docker compose -f compose.dev.yml -f compose.prod.yml down
    ;;

  logs)
    docker compose -f compose.dev.yml logs -f
    ;;

  clean)
    docker compose -f compose.dev.yml -f compose.prod.yml down
    docker container prune -f
    docker image prune -f
    ;;

  *)
    echo "Error: Comando '$COMMAND' no reconocido."
    echo "Uso correcto: sh deploy.sh {dev | dev-watch | prod | down | logs | clean}"
    exit 1
    ;;
esac