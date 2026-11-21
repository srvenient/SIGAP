# Manual del Administrador

El Administrador configura el negocio (tarifas, parqueadero, cuentas) y consulta la operación, el recaudo y la auditoría.

## Acceso

Ingrese con su usuario y contraseña. Después de iniciar sesión verá el **Panel**, que es su vista inicial.

Menú: **Panel**, **Vehículos dentro**, **Alertas e intervención**, **Transacciones**, **Recaudo**, **Dispositivos**, **Tarifas**, **Usuarios**, **Parqueadero** y **Auditoría**.

Las pantallas **Vehículos dentro** y **Alertas e intervención** funcionan igual que para el Operador (ver [operador.md](operador.md)). **Dispositivos** funciona igual que para Soporte (ver [soporte.md](soporte.md)).

## Panel

Muestra datos actualizados cada 5 segundos:

- Ocupación: cupos ocupados y disponibles.
- **Recaudo de hoy** y **Pagos aprobados**.
- **Ingresos de hoy** y **Salidas de hoy**.
- Estado general de los dispositivos.

## Transacciones

Historial de todos los ingresos. Filtre por **Placa**, **Tipo de vehículo**, **Estado** y rango de fechas (**Desde**, **Hasta**). Cada fila muestra placa, tipo, horas de ingreso y salida, valor liquidado y estado. La etiqueta **Manual** indica que hubo intervención manual.

Abra una transacción para ver el detalle completo: medio de pago, referencia, **Intentos de pago** (aprobados y fallidos, con el motivo) y el motivo de la intervención manual, si la hubo.

## Recaudo

Elija el periodo con **Desde** y **Hasta**. Verá el **Recaudo del periodo**, el desglose **Por tipo de vehículo** y **Por medio de pago**, y la lista de **Pagos registrados**. Solo cuentan las transacciones **Pagado** o **Finalizado**.

## Tarifas

Hay una tarifa para carro y otra para moto. Cada una tiene:

| Campo | Ejemplo | Significado |
| :--- | ---: | :--- |
| Valor por hora (COP) | 4.000 | Se cobra por cada hora completa |
| Valor por fracción (COP) | 2.000 | Se cobra por cada fracción iniciada después de las horas completas |
| Duración de la fracción (min) | 30 | Tamaño de cada fracción |
| Tarifa plena (COP) | 20.000 | Se cobra al superar el límite, una vez por cada período de 12 horas |
| Tarifa plena desde (min) | 300 | Límite de permanencia a partir del cual se cobra la tarifa plena |

Para modificar una tarifa, cambie los valores y pulse **Guardar**. El sistema rechaza valores inválidos: los montos deben ser mayores que cero, la fracción debe durar entre 1 y 59 minutos y el límite de tarifa plena debe estar entre 1 y 720 minutos.

El cambio aplica solo a los pagos que se hagan desde ese momento. Los vehículos que ya pagaron conservan su valor.

**Histórico de cambios** muestra cada modificación con la configuración anterior y la nueva, el usuario y la fecha. Filtre por **Tipo de vehículo** y por fechas. Los registros del histórico no se pueden modificar ni borrar.

### Ejemplos de cobro con la tarifa de carro anterior

| Permanencia | Cálculo | Valor |
| :--- | :--- | ---: |
| 20 min | 1 fracción | $2.000 |
| 1 h 10 min | 1 hora + 1 fracción | $6.000 |
| 4 h 45 min | 4 horas + 2 fracciones | $20.000 |
| 6 h | Supera 5 h: 1 tarifa plena | $20.000 |
| 13 h | Supera 12 h: 2 tarifas plenas | $40.000 |

## Usuarios

### Crear una cuenta

1. Pulse **Crear cuenta**.
2. Complete **Nombre de usuario** (único), nombre completo, correo y rol (**Administrador**, **Operador** o **Soporte técnico**).
3. Escriba una **Contraseña inicial** o pulse **Generar contraseña**. Debe tener entre 8 y 40 caracteres, con mayúscula, minúscula y número.
4. Revise los datos y pulse **Confirmar y crear**.
5. Entregue la contraseña a la persona por un medio seguro. Deberá cambiarla en su primer ingreso.

### Modificar una cuenta

Desde la fila de la cuenta puede:

- **Cambiar rol.**
- **Restablecer contraseña:** genera una contraseña temporal que debe entregar a la persona. Su sesión activa se cierra.
- **Desactivar cuenta:** la persona ya no podrá iniciar sesión, pero la cuenta y su historial se conservan. Use **Reactivar cuenta** para habilitarla de nuevo.
- **Desbloquear cuenta:** quita el bloqueo de 15 minutos que se aplica tras 5 intentos fallidos.

Restricciones:

- No se puede desactivar ni quitar el rol a la última cuenta de Administrador activa.
- La cuenta superusuario definida en el `.env` está protegida y no se puede modificar desde aquí.
- No puede modificar su propia cuenta desde **Usuarios**; use su perfil.

Todas las creaciones y modificaciones quedan en la auditoría.

## Parqueadero

Configure **Nombre del parqueadero**, **Dirección**, **Capacidad (cupos)** y **Apertura de talanquera (s)**. El tiempo de apertura se envía al Arduino en el siguiente reporte del worker (unos 5 segundos).

## Auditoría

Registro de todas las acciones relevantes: transacciones, pagos, aperturas de talanquera, tarifas, cuentas, inicios y cierres de sesión, alertas y tickets.

Filtre por **Acción**, **Usuario** y fechas (**Desde**, **Hasta**), y elija el **Orden**. Cada registro muestra usuario (o `sistema` si la acción fue automática), acción, fecha y hora, elemento afectado, resultado y detalle.

Los registros de auditoría no se pueden modificar ni borrar desde la plataforma ni desde la base de datos.
