# Manual del Operador

El Operador atiende las situaciones que el sistema no resuelve solo: placas ilegibles, vehículos sin pago en la salida y aperturas de contingencia.

## Acceso

Ingrese a la dirección del sistema con su usuario y contraseña. En el primer ingreso el sistema le pedirá cambiar la contraseña: debe tener entre 8 y 40 caracteres, con mayúscula, minúscula y número.

Su menú tiene cuatro opciones: **Panel**, **Vehículos dentro**, **Alertas e intervención** y **Tickets técnicos**.

Para cambiar su nombre o contraseña, o para cerrar sesión, abra su perfil desde la barra superior.

## Panel

Muestra la ocupación del parqueadero y las **Alertas por atender**. El botón **Atender alertas** lleva directamente a la pantalla de alertas. La información se actualiza sola cada 5 segundos.

## Alertas e intervención

Las alertas llegan solas desde las cámaras:

| Tipo | Cuándo aparece | Cómo atenderla |
| :--- | :--- | :--- |
| Placa no reconocida | La cámara ve una placa pero no puede leerla durante 4 segundos | Revise la foto y pulse **Registrar placa** |
| Pago pendiente | Un vehículo llegó a la salida sin pagar | Indique al conductor que pague en el módulo de pago, o **Descartar** con motivo si ya se resolvió |
| Sin transacción activa | Un vehículo llegó a la salida sin ingreso registrado | Verifique la situación; corrija la placa en **Vehículos dentro** si se registró mal |

### Registrar una placa (placa no reconocida)

1. En la alerta, revise la foto y pulse **Registrar placa**.
2. Escriba la **Placa** correcta y el **Motivo** de la intervención.
3. Pulse **Registrar placa**. Si la placa es válida, se crea el ingreso y se abre la talanquera.

Si la placa no tiene un formato válido (`ABC123` para carro, `ABC12D` para moto), el sistema la rechaza, no crea el ingreso y la alerta sigue pendiente. Corrija la placa e intente de nuevo.

### Ingreso manual

Para registrar un vehículo sin alerta previa (por ejemplo, con la cámara dañada), pulse **Registrar ingreso manual**, escriba placa y motivo, y confirme.

### Apertura de contingencia

1. Pulse **Abrir talanquera**.
2. Elija la **Talanquera** (ingreso o salida) y escriba el **Motivo**. El motivo es obligatorio.
3. Pulse **Abrir**.

La apertura de salida **solo se permite si el vehículo ya pagó**: usted puede saltarse la cámara, no el cobro. En **Órdenes de apertura recientes** puede ver si la talanquera confirmó la apertura.

Todas las intervenciones quedan registradas en la auditoría con su usuario, la fecha, la placa y el motivo.

## Vehículos dentro

Lista de los vehículos con transacción **Ingresado** o **Pagado**, con placa, tipo y hora de ingreso. Se actualiza sola.

- **Buscar por placa:** filtra la lista.
- **Corregir placa:** si la cámara registró mal una placa, escriba la **Placa correcta** y el **Motivo**, y pulse **Guardar**.

## Tickets técnicos

Use los tickets para reportar a Soporte un problema que detecte durante la operación.

1. Pulse **Crear ticket**.
2. Complete **Componente o proceso afectado** y **Descripción del problema**.
3. Si el problema tiene que ver con un vehículo, indique la **Transacción relacionada (opcional)**.
4. Pulse **Crear**.

El ticket queda **Pendiente** y asignado a Soporte técnico. En esta pantalla verá solo los tickets que usted creó, con su estado actual: **Pendiente**, **En revisión**, **Solucionado** o **No solucionado**.
