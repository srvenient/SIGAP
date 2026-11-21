# Manual de Soporte técnico

Soporte técnico supervisa las cámaras y talanqueras y atiende los tickets técnicos.

## Acceso

Ingrese con su usuario y contraseña. Su menú tiene tres opciones: **Panel**, **Dispositivos** y **Tickets técnicos**.

## Panel

Resume el estado de los dispositivos y los tickets abiertos. **Ver todos** lleva a la lista completa de tickets.

## Dispositivos

**Estado actual** muestra los cuatro dispositivos: cámara de ingreso, cámara de salida, talanquera de ingreso y talanquera de salida.

| Estado | Significado |
| :--- | :--- |
| **Conectado** | El dispositivo funciona y el worker lo reportó hace menos de 20 segundos |
| **Sin comunicación** | El worker no reporta (equipo apagado, red caída) o no hay comunicación con el Arduino |
| **Error** | La cámara no entrega imagen o la última apertura de la talanquera falló |

Cada fila muestra la fecha y hora de la última comunicación. La pantalla se actualiza sola.

**Eventos técnicos** lista los fallos registrados, con componente, código de error, descripción, fecha y transacción relacionada. Códigos frecuentes:

| Código | Causa | Revisión sugerida |
| :--- | :--- | :--- |
| `GATE_NO_RESPONSE` | La talanquera no respondió `ACK` a una orden de apertura | Cable USB, alimentación del Arduino, módulo de relés |
| `WORKER_NO_COMMUNICATION` | El worker dejó de enviar su reporte | Equipo del parqueadero encendido, red, proceso `camera_worker.py` |

Para el detalle del hardware y del protocolo serial consulte [05-hardware.md](../05-hardware.md).

## Tickets técnicos

Los tickets llegan de dos formas:

- **Manuales:** los crea un Operador.
- **Automáticos:** los crea el sistema al detectar un fallo, con el evento técnico que lo originó.

### Atender un ticket

1. Abra un ticket **Pendiente** y pulse **Tomar ticket**. Pasa a **En revisión** y queda a su nombre.
2. Registre **Diagnóstico**, **Acciones realizadas** y **Resultado**. Use **Guardar avance** para guardar sin cerrar.
3. Cierre el ticket:
   - **Solucionado:** el problema se resolvió y se verificó. Un ticket solucionado no se puede reabrir.
   - **No solucionado:** el problema persiste o requiere otra intervención. El ticket se puede volver a tomar después.

El historial del ticket guarda cada cambio de estado con usuario, fecha y hora, y no se puede modificar.
