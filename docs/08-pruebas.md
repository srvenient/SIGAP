# 8. Plan de pruebas y evidencias

## 8.1 Estrategia

| Nivel | Herramienta | Alcance |
| :--- | :--- | :--- |
| Unitarias | pytest | Cálculo del cobro (funciones puras) y protocolo del worker con un Arduino y un backend simulados |
| Integración | pytest + httpx + PostgreSQL real | Cada endpoint con la base de pruebas, incluidos los triggers de inmutabilidad y la concurrencia |
| Funcionales (manuales) | Navegador + hardware | Recorrido completo por rol con cámaras y Arduino reales (sección 8.4) |
| Campo | Registro manual | Exactitud de la lectura de placas en el parqueadero (sección 8.5) |

Las pruebas de integración usan su propia base PostgreSQL (`db_test`, puerto 5433) y nunca tocan la de desarrollo.

## 8.2 Cómo ejecutarlas

```bash
docker compose -f compose.dev.yml --profile test up -d db_test
```

```bash
cd backend && uv run --no-sync pytest -v
```

Para ejecutar solo las que no necesitan base de datos:

```bash
cd backend && uv run --no-sync pytest tests/test_charge.py tests/test_worker.py -v
```

## 8.3 Inventario de pruebas automatizadas

**137 casos** en total (algunas funciones están parametrizadas y generan varios casos).

| Archivo | Funciones | Casos | Necesita base de datos |
| :--- | ---: | ---: | :--- |
| `tests/test_charge.py` | 3 | 19 | No |
| `tests/test_worker.py` | 14 | 19 | No |
| `tests/test_app.py` | 2 | 2 | Sí |
| `tests/test_operations.py` | 61 | 97 | Sí |

### Evidencia de ejecución

| Fecha | Alcance | Resultado |
| :--- | :--- | :--- |
| 2026-11-20 | `test_charge.py` + `test_worker.py` (38 casos) | **38 aprobados, 0 fallidos** (3,3 s) |
| 2026-11-20 | Suite completa con PostgreSQL 16 (`db_test`), commit `673634d` | **137 aprobados, 0 fallidos** (12,9 s). Salida completa: [evidencias/pytest_20261120.txt](evidencias/pytest_20261120.txt) |

> Para repetir la ejecución: `docker compose -f compose.dev.yml --profile test up -d db_test` y, dentro de `backend/`, `uv run --no-sync pytest -v`.

### Qué verifica cada grupo

**Cobro (`test_charge.py`)**
- `test_calculate_charge`: hora y fracción, límite de 5 h, tarifa plena y nuevo período a las 12 h.
- `test_limit_is_configurable`: el límite de tarifa plena se puede cambiar.
- `test_elapsed_minutes`: los minutos se redondean hacia arriba, con mínimo 1.

**Worker (`test_worker.py`)**
- Protocolo serial: espera de `ACK`, falla sin `ACK`, `PONG`, cambio de tiempo, reconexión, puerto inexistente.
- Flujo de carril: la entrada solo abre después de crear la transacción; un ingreso rechazado o sin servidor nunca abre; la salida solo finaliza después del `ACK`; una salida no autorizada nunca abre; las órdenes manuales reportan su resultado.

**Ingreso**
- `test_entry_requires_device_key`, `test_entry_creates_transaction_with_system_values`, `test_entry_ignores_client_supplied_status_and_amount`
- `test_entry_rejects_plate_that_does_not_match_type`, `test_entry_rejects_vehicle_already_inside`
- `test_entry_retry_returns_same_transaction_when_gate_never_opened`
- `test_entry_rejected_when_parking_is_full`, `test_paid_vehicle_still_occupies_a_space`, `test_concurrent_entries_cannot_exceed_capacity`

**Pago**
- `test_quote_applies_current_tariff`, `test_quote_applies_full_rate_and_new_period`, `test_quote_for_unknown_plate_returns_404`
- `test_pending_payment_keeps_transaction_entered`, `test_approved_payment_marks_paid_and_records_method`
- `test_rejected_payment_can_be_retried_and_is_audited`, `test_payment_timeout_expires_attempt_and_is_audited`
- `test_late_approval_after_timeout_does_not_mark_paid`, `test_approval_is_idempotent`, `test_invalid_payment_method_is_rejected`

**Salida**
- `test_exit_with_pending_payment_is_refused_and_alerts_operator`, `test_exit_without_transaction_is_refused_and_alerts_operator`, `test_repeated_exit_attempts_do_not_duplicate_alert`
- `test_authorize_does_not_change_state_until_gate_confirms`, `test_confirm_exit_completes_transaction`, `test_confirm_exit_refused_when_not_paid`
- `test_gate_failure_raises_ticket_and_keeps_transaction_paid`, `test_repeated_failure_does_not_duplicate_open_ticket`

**Tarifas**
- `test_tariff_update_keeps_history_and_does_not_touch_settled`, `test_new_tariff_applies_to_next_quote`, `test_invalid_tariff_is_rejected`

**Intervención manual**
- `test_operator_resolves_unreadable_plate`, `test_invalid_manual_plate_keeps_alert_pending`, `test_operator_corrects_plate_of_vehicle_inside`
- `test_manual_open_flows_through_worker_and_is_audited`, `test_manual_exit_after_payment_completes_when_gate_opens`, `test_manual_exit_refused_when_unpaid`

**Dispositivos y tickets**
- `test_device_status_follows_heartbeat`, `test_device_error_opens_automatic_ticket`, `test_silent_worker_is_detected_once`
- `test_ticket_lifecycle_preserves_history`, `test_not_solved_ticket_can_be_taken_again`, `test_solved_ticket_cannot_be_reopened`, `test_operator_only_sees_own_tickets`
- `test_only_support_manages_tickets`, `test_support_cannot_create_tickets`

**Consultas**
- `test_inside_list_and_search`, `test_revenue_counts_only_collected_by_type_and_method`, `test_dashboard_summarizes_the_day`, `test_transaction_filters_and_detail`

**Auditoría e integridad**
- `test_login_and_logout_are_audited`, `test_failed_login_is_audited_without_revealing_cause`, `test_queries_do_not_generate_audit_records`, `test_audit_filters`, `test_audit_api_has_no_write_operations`
- `test_database_rejects_changes_to_audit_logs`, `test_database_rejects_changes_to_tariff_history`, `test_database_rejects_changes_to_ticket_history`

**Cuentas y permisos**
- `test_weak_password_is_rejected`, `test_account_changes_are_audited`, `test_inactive_account_gets_specific_message`, `test_permission_matrix`

**Aplicación**
- `test_health_check_returns_ok_status`, `test_openapi_spec_is_served`

## 8.4 Casos de prueba funcionales

Ejecútelos con el sistema desplegado, las cámaras y el Arduino conectados. Registre en **Resultado** `Aprobado` o `Fallido` y en **Evidencia** el nombre de la captura o del video guardado en `docs/evidencias/`.

| ID | HU | Precondición | Pasos | Resultado esperado | Resultado | Evidencia |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| CF-01 | HU-01, 04, 05 | Hay cupos | Acercar un carro a la cámara de ingreso | Pantalla de ingreso en verde con la placa, talanquera abre y cierra; aparece en **Vehículos dentro** | | |
| CF-02 | HU-01 | — | Acercar una moto (placa `ABC12D`) | Se registra con tipo **Moto** | | |
| CF-03 | HU-02 | Capacidad = vehículos dentro | Acercar otro vehículo | Pantalla indica que no hay cupos; la talanquera no abre | | |
| CF-04 | HU-03 | El vehículo ya está dentro | Volver a pasarlo por el ingreso | Ingreso rechazado; no se crea otra transacción | | |
| CF-05 | HU-01, 06 | — | Tapar parcialmente la placa 4 s | Aparece una alerta con foto en **Alertas e intervención** | | |
| CF-06 | HU-06 | CF-05 | Operador registra la placa correcta | Se crea la transacción, abre la talanquera y queda en auditoría con el motivo | | |
| CF-07 | HU-06 | CF-05 | Operador escribe una placa inválida (`AB12`) | Se rechaza; la alerta sigue pendiente | | |
| CF-08 | HU-07 | Vehículo dentro | Consultar la placa en `/pago` | Muestra tiempo de permanencia y valor | | |
| CF-09 | HU-08 | CF-08 | Elegir Nequi y **Aprobar** | "Procesando pago" y luego "Pago aprobado"; la transacción pasa a **Pagado** | | |
| CF-10 | HU-09 | CF-08 | Elegir Tarjeta y **Rechazar** | "El pago no se completó"; se puede reintentar; queda en auditoría | | |
| CF-11 | HU-09 | CF-08 | Iniciar un pago y esperar 3 minutos | El intento vence; la transacción sigue **Ingresado** | | |
| CF-12 | HU-10, 11, 12 | Vehículo pagado | Pasarlo por la cámara de salida | Talanquera abre; transacción **Finalizado** con hora de salida | | |
| CF-13 | HU-11 | Vehículo sin pagar | Pasarlo por la salida | Talanquera cerrada, pantalla "pago pendiente", alerta para el Operador | | |
| CF-14 | HU-11 | Placa sin ingreso | Pasarla por la salida | Talanquera cerrada, alerta "sin transacción activa" | | |
| CF-15 | HU-05, 24 | Desconectar el relé o el Arduino | Intentar un ingreso | Alerta técnica y ticket automático en **Tickets técnicos** | | |
| CF-16 | HU-13, 14 | Sesión de Administrador | Cambiar la tarifa de carro | El histórico muestra valores anterior y nuevo, usuario y fecha | | |
| CF-17 | HU-13 | CF-16 | Consultar un vehículo ya pagado antes del cambio | Su valor no cambia | | |
| CF-18 | HU-15 | Sesión de Administrador | Crear usuario con contraseña `abc` | Se rechaza por la política de contraseñas | | |
| CF-19 | HU-16 | Un solo Administrador activo | Intentar desactivarlo | Se rechaza | | |
| CF-20 | HU-17 | Cuenta desactivada | Iniciar sesión con la contraseña correcta | Mensaje "Usuario inactivo" | | |
| CF-21 | HU-17 | — | Iniciar sesión con contraseña incorrecta | Mensaje genérico, sin decir qué campo falló | | |
| CF-22 | HU-17 | Sesión de Operador | Revisar el menú | Solo ve Panel, Vehículos dentro, Alertas e intervención y Tickets técnicos | | |
| CF-23 | HU-18 | Sesión de Operador | Buscar una placa en **Vehículos dentro** | La lista se filtra y se actualiza sola al entrar o salir un vehículo | | |
| CF-24 | HU-19 | Pagos con varios medios | Abrir **Recaudo** con un rango de fechas | Total y desglose por tipo de vehículo y medio | | |
| CF-25 | HU-20 | — | Filtrar **Transacciones** por estado y abrir una | Detalle con medio de pago e intervención manual | | |
| CF-26 | HU-21 | — | Iniciar sesión como Administrador | La vista inicial es el panel con ocupación, recaudo, ingresos, salidas y dispositivos | | |
| CF-27 | HU-22 | Worker detenido | Esperar 20 s en **Dispositivos** | Los cuatro dispositivos pasan a **Sin comunicación** con la hora de la última comunicación | | |
| CF-28 | HU-23 | Sesión de Operador | Crear un ticket asociado a una transacción | Queda **Pendiente** y asignado a Soporte | | |
| CF-29 | HU-25 | Sesión de Soporte | Tomar, documentar y cerrar un ticket | Pasa por **En revisión** y **Solucionado**; el historial muestra cada cambio | | |
| CF-30 | HU-26, 27 | — | Filtrar **Auditoría** por acción y usuario | Registros en orden cronológico con usuario, acción, elemento y resultado | | |
| CF-31 | HU-28 | Acceso a la base | Ejecutar `DELETE FROM audit_logs;` | PostgreSQL rechaza la operación | | |

## 8.5 Prueba de campo de lectura de placas

Registre al menos 100 pasos reales, repartidos entre día y noche, carros y motos.

| # | Fecha y hora | Día / noche | Tipo | Placa real | Placa leída | Resultado |
| ---: | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | | | | | | Correcta / Alerta / Incorrecta |

Indicadores a reportar:

- **Lectura correcta** = correctas ÷ total.
- **Lectura incorrecta** = incorrectas ÷ total. Es el indicador más importante: una lectura incorrecta crea una transacción con la placa equivocada.
- **Intervención manual** = alertas ÷ total.
