# ==============================
# STAGE 1: Base image
# ==============================
FROM node:24-alpine AS base

ENV PNPM_HOME="/pnpm" \
    PATH="/pnpm:/usr/local/bin:$PATH"

RUN corepack enable && corepack prepare pnpm@latest --activate

WORKDIR /app

COPY package.json pnpm-lock.yaml ./

# ==============================
# STAGE 2: Local environment
# ==============================
FROM base AS local

RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile

COPY . .

EXPOSE 3000

CMD ["pnpm", "dev", "--host", "0.0.0.0", "--port", "3000"]

# ==============================
# STAGE 3: Build (SPA)
# ==============================
FROM base AS build-env

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile

COPY . .

RUN pnpm run build

# ==============================================================================
# STAGE 4: Production Deployable Image
# ==============================================================================
FROM nginx:alpine-slim AS production

RUN sed -i 's/server_tokens on;/server_tokens off;/g' /etc/nginx/nginx.conf && \
    rm -rf /usr/share/nginx/html/*

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-env /app/build/client /usr/share/nginx/html

# OPTIMIZACIÓN: Healthcheck para que Docker sepa si la web está viva
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]