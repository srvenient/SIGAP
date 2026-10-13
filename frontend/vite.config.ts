import { reactRouter } from "@react-router/dev/vite";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";
import fs from "node:fs";

// Detección de entorno Docker Compose:
// Dentro de Docker Compose, el contenedor del backend se resuelve por su nombre de servicio: "http://api:8000"
// En la máquina host fuera de Docker, se resuelve por "http://localhost:8000"
const isInsideDocker =
  fs.existsSync("/.dockerenv") ||
  fs.existsSync("/run/.containerenv") ||
  process.env.DOCKER === "true" ||
  process.cwd() === "/app";

const backendTarget =
  process.env.BACKEND_URL ||
  (isInsideDocker ? "http://api:8000" : "http://localhost:8000");

console.log(`[Vite Proxy] Configurando destino de /api hacia: ${backendTarget}`);

export default defineConfig({
  plugins: [tailwindcss(), reactRouter()],
  resolve: {
    tsconfigPaths: true,
  },
  server: {
    port: 3000,
    host: "0.0.0.0",
    proxy: {
      "/api": {
        target: backendTarget,
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
