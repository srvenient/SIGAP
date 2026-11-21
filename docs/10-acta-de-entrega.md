# 10. Acta de entrega y notas de versión

| Campo | Valor |
| :--- | :--- |
| Proyecto | SIGAP: Sistema Integral de Gestión y Automatización de Parqueaderos |
| Alcance de referencia | Documentación proyecto V2.1 |
| Versión entregada | `v1.0.0` |
| Commit del código | `673634d` |
| Fecha de entrega | 20 de noviembre de 2026 |
| Institución | Fundación Universitaria Monserrate |
| Programa y asignatura | Ingeniería de Sistemas · Optativa III |
| Equipo de desarrollo | Harol Handrey Morales Gil, Yefri Sebastian Rincon Cortes y Nelson Rodriguez Roa |
| Recibe | Claudio Jonathan Zamir Castiblanco Flórez |

## 10.1 Entregables

| # | Entregable | Ubicación |
| ---: | :--- | :--- |
| 1 | Código fuente del backend, frontend y worker | Repositorio: `backend/`, `frontend/` |
| 2 | Sketch del Arduino | `arduino/sigap_talanquera/sigap_talanquera.ino` |
| 3 | Modelo YOLO entrenado y métricas | `backend/models/YOLO/`, `backend/reports/runs/YOLO/` |
| 4 | Configuración de despliegue | `compose.dev.yml`, `compose.prod.yml`, `scripts/deploy.sh`, `.env.example` |
| 5 | Migraciones y datos iniciales | `backend/migrations/`, `backend/src/server/seed.py` |
| 6 | Pruebas automatizadas (137 casos, todos aprobados) | `backend/tests/`, [evidencias/pytest_20261120.txt](evidencias/pytest_20261120.txt) |
| 7 | Requisitos y trazabilidad | [01-requisitos-y-trazabilidad.md](01-requisitos-y-trazabilidad.md) |
| 8 | Arquitectura | [02-arquitectura.md](02-arquitectura.md) |
| 9 | Modelo de datos | [03-modelo-de-datos.md](03-modelo-de-datos.md) |
| 10 | Especificación de la API y esquema OpenAPI | [04-api.md](04-api.md), [api/openapi.json](api/openapi.json) |
| 11 | Hardware | [05-hardware.md](05-hardware.md) |
| 12 | Modelo de visión | [06-modelo-de-vision.md](06-modelo-de-vision.md) |
| 13 | Instalación y despliegue | [07-instalacion-y-despliegue.md](07-instalacion-y-despliegue.md) |
| 14 | Plan de pruebas y evidencias | [08-pruebas.md](08-pruebas.md) |
| 15 | Seguridad | [09-seguridad.md](09-seguridad.md) |
| 16 | Manuales de usuario | [manuales/](manuales/) |

## 10.2 Funcionalidades incluidas

- Ingreso y salida automáticos con lectura de placa (YOLO + EasyOCR), validación de formato, cupos y duplicados.
- Cobro por hora y fracción, tarifa plena después del límite y nuevo período cada 12 horas.
- Módulo de pago público con Tarjeta, PSE y Nequi sobre pasarela simulada, con reintentos y vencimiento.
- Pantallas públicas de carril para ingreso y salida.
- Intervención manual del Operador: alertas con foto, registro y corrección de placa, ingreso manual y apertura de contingencia.
- Monitoreo de dispositivos, eventos técnicos y tickets manuales y automáticos con historial.
- Panel, recaudo, transacciones y auditoría para el Administrador.
- Cuentas por rol, Argon2, JWT rotativos en cookies httpOnly, bloqueo por intentos y límite de peticiones.
- Auditoría e históricos inmutables a nivel de base de datos.

Cumplimiento: 26 de 28 historias de usuario completas y 2 con una limitación documentada (HU-05 y HU-12, cierre de la talanquera por tiempo).

## 10.3 Limitaciones conocidas

| Limitación | Impacto | Alternativa |
| :--- | :--- | :--- |
| Pasarela de pago simulada | No se recauda dinero real | Implementar un adaptador de `PaymentGateway` con webhook firmado y deshabilitar `/simulate` |
| Sin sensor de paso | La talanquera cierra por tiempo, no al detectar que el vehículo pasó (HU-05, HU-12) | Lazo inductivo o barrera infrarroja en el Arduino |
| Sin HTTPS incluido | En producción las cookies `Secure` exigen HTTPS fuera de `localhost` | Proxy con certificado TLS delante del contenedor `frontend` |
| Sin tiempo máximo para salir después de pagar | El valor queda congelado al pagar; no se cobra el tiempo adicional | Definir una ventana de salida y recalcular si se supera |
| Sin pago en efectivo ni cobro asistido | Todo pago pasa por el módulo público | Agregar un medio "efectivo" registrado por el Operador |
| Sin enlace o QR del carril de salida a `/pago` | El conductor debe conocer la dirección del módulo de pago | Kiosco junto a la salida o QR impreso |
| Una sola sede operativa | El modelo de datos ya soporta varias sedes; los servicios usan la sede por defecto | Identificar la sede por usuario y por dispositivo |
| Exactitud del OCR sin medir en campo | Las métricas cubren solo la detección de la placa | Prueba de campo ([08-pruebas.md](08-pruebas.md#85-prueba-de-campo-de-lectura-de-placas)) |

## 10.4 Pendientes

- [x] Ejecutar la suite completa de pruebas con la base `db_test`: 137 aprobados, 0 fallidos el 2026-11-20 ([evidencia](evidencias/pytest_20261120.txt)).
- [ ] Ejecutar los casos funcionales CF-01 a CF-31 y guardar las evidencias en `docs/evidencias/`.
- [ ] Hacer la prueba de campo de lectura de placas.
- [ ] Completar marca y modelo del hardware en [05-hardware.md](05-hardware.md).
- [ ] Documentar el dataset de entrenamiento en [06-modelo-de-vision.md](06-modelo-de-vision.md).
- [ ] Agregar capturas de pantalla a los manuales.
- [ ] Guardar una copia del PDF de la V2.1 en `docs/referencias/`.
- [ ] Retirar del repositorio las fotos de placas de `backend/output/` y agregar esa carpeta a `.gitignore`.
- [ ] Agregar `.idea/` a `.gitignore`.
- [ ] Actualizar `PROJECT_VERSION` y crear la etiqueta de versión en Git.

## 10.5 Trabajo futuro

1. Integración con una pasarela real (por ejemplo, Wompi o PayU) mediante webhook firmado.
2. Sensor de paso para el cierre de la talanquera.
3. Operación de varias sedes desde la misma plataforma.
4. Actualización en tiempo real con WebSockets o Server-Sent Events en lugar de consultas periódicas.
5. Clave de dispositivo por equipo y rotación automática.
6. Política de conservación y borrado de fotos y datos personales.
