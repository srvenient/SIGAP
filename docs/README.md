# Documentación de SIGAP

Paquete de documentación de cierre del **Sistema Integral de Gestión y Automatización de Parqueaderos**, construido según la *Documentación proyecto V2.1*.

Para una introducción rápida y los comandos de arranque, vea el [README principal](../README.md).

## Índice

| # | Documento | Para quién | Contenido |
| :--- | :--- | :--- | :--- |
| 1 | [Requisitos y trazabilidad](01-requisitos-y-trazabilidad.md) | Evaluador, cliente | Las 28 historias de usuario con su implementación y sus pruebas |
| 2 | [Arquitectura](02-arquitectura.md) | Desarrolladores | Componentes, módulos, flujos de ingreso, pago y salida, estados y decisiones de diseño |
| 3 | [Modelo de datos](03-modelo-de-datos.md) | Desarrolladores | Diagrama entidad-relación, diccionario de datos, inmutabilidad y respaldos |
| 4 | [API](04-api.md) | Desarrolladores, integradores | Endpoints por módulo, autenticación y códigos de respuesta. Esquema: [openapi.json](api/openapi.json) |
| 5 | [Hardware](05-hardware.md) | Soporte, instaladores | Conexión del Arduino, protocolo serial y fallas |
| 6 | [Modelo de visión](06-modelo-de-vision.md) | Evaluador, desarrolladores | Proceso de lectura de placas, entrenamiento de YOLO y métricas |
| 7 | [Instalación y despliegue](07-instalacion-y-despliegue.md) | Administrador de sistemas | Requisitos, configuración, HTTPS, actualización y solución de problemas |
| 8 | [Pruebas](08-pruebas.md) | Evaluador, desarrolladores | Pruebas automatizadas, evidencias, casos funcionales y prueba de campo |
| 9 | [Seguridad](09-seguridad.md) | Evaluador, administrador de sistemas | Controles, matriz de permisos, datos personales y riesgos |
| 10 | [Acta de entrega](10-acta-de-entrega.md) | Cliente, docente | Datos de la entrega, entregables, limitaciones y pendientes |

### Manuales de usuario

| Manual | Rol |
| :--- | :--- |
| [Administrador](manuales/administrador.md) | Configuración, consultas, cuentas y auditoría |
| [Operador](manuales/operador.md) | Alertas, intervención manual y tickets |
| [Soporte técnico](manuales/soporte.md) | Dispositivos y atención de tickets |
| [Conductor](manuales/conductor.md) | Ingreso, pago y salida |

## Exportar a PDF

Los documentos están en Markdown para que queden versionados junto al código. Para generar un PDF único (portada, contenido, diagramas y numeración de páginas) ejecute desde la raíz del repositorio:

```bash
python scripts/exportar_docs_pdf.py
```

El script solo necesita Python y Microsoft Edge o Google Chrome, y conexión a internet para cargar el renderizador de Markdown y de diagramas. Deja en `entrega/` el PDF, una versión HTML y un ZIP con el PDF y esta carpeta `docs/`. La portada toma los datos completados en la tabla inicial del [acta de entrega](10-acta-de-entrega.md).
