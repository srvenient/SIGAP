# 1. Requisitos y matriz de trazabilidad

**Documento de referencia:** *Documentación proyecto V2.1* (Sistema de Gestión de Parqueaderos Públicos). Es la versión vigente del alcance: tres roles (Administrador, Operador y Soporte técnico), tickets técnicos y la regla de cobro de 12 horas. Guarde una copia del PDF en `docs/referencias/` junto con esta entrega.

**Convenciones**

- **Estado:** *Cumple*, o *Con limitación* cuando se cumple con una limitación documentada.
- **Pruebas:** nombres de funciones de `backend/tests/`. **CF-xx** son los casos funcionales de [08-pruebas.md](08-pruebas.md#84-casos-de-prueba-funcionales).
- Las rutas de código son relativas a `backend/src/` salvo que se indique otra cosa.

## 1.1 Resumen

| Épica | Historias | Cumple | Con limitación |
| :--- | :--- | :---: | :---: |
| 1. Ingreso de vehículos | HU-01 a HU-06 | 5 | 1 |
| 2. Pago | HU-07 a HU-09 | 3 | 0 |
| 3. Salida | HU-10 a HU-12 | 2 | 1 |
| 4. Tarifas | HU-13, HU-14 | 2 | 0 |
| 5. Cuentas de acceso | HU-15 a HU-17 | 3 | 0 |
| 6. Monitoreo | HU-18 a HU-21 | 4 | 0 |
| 7. Soporte técnico | HU-22 a HU-25 | 4 | 0 |
| 8. Auditoría | HU-26 a HU-28 | 3 | 0 |
| **Total** | **28** | **26** | **2** |

Las dos limitaciones vienen de la misma causa: el prototipo no tiene sensor de paso y la talanquera se cierra por tiempo (ver [05-hardware.md](05-hardware.md#55-qué-significa-el-ack)).

## 1.2 Requisitos generales

| Requisito V2.1 | Estado | Cómo se cumple |
| :--- | :---: | :--- |
| Control automatizado del ingreso a la salida | Cumple | Worker de cámaras + backend + Arduino ([02-arquitectura.md](02-arquitectura.md)) |
| Tarifas por tipo de vehículo (carro y moto) con histórico | Cumple | Módulo `tariff`; HU-13 y HU-14 |
| Transacción trazable desde el ingreso hasta el final | Cumple | Estados `ENTERED → PAID → COMPLETED`, intentos de pago y auditoría |
| Estado general: recaudo, dispositivos, ocupación | Cumple | Dashboard y recaudo (HU-19, HU-21) |
| Arquitectura que permita escalar a varias sedes | Cumple | `parking_lot_id` obligatorio en las tablas operativas ([02-arquitectura.md](02-arquitectura.md#26-preparación-para-varias-sedes)) |
| Autenticación con usuario y contraseña | Cumple | HU-17 |
| Contraseñas sin texto plano | Cumple | Argon2 ([09-seguridad.md](09-seguridad.md)) |
| Acceso según el rol | Cumple | `require_roles` en cada endpoint; `test_permission_matrix` |
| Operaciones relevantes auditadas | Cumple | HU-26 a HU-28 |
| Interfaz administrativa con autenticación | Cumple | `/dashboard/*` |
| Interfaz operativa pública: ingreso, pago y salida | Cumple | `/punto/ingreso`, `/pago`, `/punto/salida` |
| Pago vía pasarela electrónica | Cumple | Puerto `PaymentGateway` con adaptador simulado; una pasarela real se conecta sin cambiar los casos de uso |
| Configuración de "tipos de vehículo" | Cumple | Los tipos son los dos que fija la V2.1 (carro y moto); cada uno con su tarifa configurable |

## 1.3 Matriz por historia de usuario

### Épica 1: Gestión de ingreso de vehículos

| HU | Criterio de aceptación | Estado | Implementación | Pruebas |
| :--- | :--- | :---: | :--- | :--- |
| HU-01 | Capturar imagen y reconocer la placa al detectar un vehículo | Cumple | `scripts/camera_worker.py`, `inference/detection.py`, `inference/plate_reader.py` | CF-01 |
| HU-01 | Extraer el texto y determinar carro o moto por el formato | Cumple | `server/transaction/domain/plate.py` (`ABC123` carro, `ABC12D` moto) | `test_entry_creates_transaction_with_system_values`, CF-02 |
| HU-01 | Placa no reconocida genera alerta para resolución manual | Cumple | Alerta `plate_unreadable` con foto tras 4 s | `test_operator_resolves_unreadable_plate`, CF-05 |
| HU-02 | Comparar capacidad con vehículos dentro | Cumple | `TransactionService.register_entry`; cuenta `ENTERED` y `PAID` | `test_paid_vehicle_still_occupies_a_space`, `test_concurrent_entries_cannot_exceed_capacity` |
| HU-02 | Con cupo, el ingreso continúa | Cumple | Ídem | `test_entry_creates_transaction_with_system_values` |
| HU-02 | Sin cupo: no crear transacción, no abrir e informar al conductor | Cumple | Error 409; pantalla del carril "Parqueadero lleno" | `test_entry_rejected_when_parking_is_full`, `test_rejected_entry_never_opens`, CF-03 |
| HU-03 | Formato válido según el tipo de vehículo | Cumple | `identify_vehicle_type`; error 422 | `test_entry_rejects_plate_that_does_not_match_type` |
| HU-03 | Sin otra transacción activa con la misma placa | Cumple | Validación + índice único parcial `uq_transactions_active_plate` | `test_entry_rejects_vehicle_already_inside`, CF-04 |
| HU-04 | Transacción con id, placa, tipo, fecha y hora, parqueadero y estado "Ingresado" | Cumple | Tabla `transactions` | `test_entry_creates_transaction_with_system_values` |
| HU-04 | Fecha y hora automáticas, sin modificación manual | Cumple | El backend ignora los valores enviados por el cliente | `test_entry_ignores_client_supplied_status_and_amount` |
| HU-05 | Abrir solo después de crear la transacción | Cumple | `worker/gate_flow.py` | `test_entry_opens_only_after_transaction_is_created` |
| HU-05 | Talanquera sin respuesta genera alerta técnica para Soporte | Cumple | Evento `GATE_NO_RESPONSE` y ticket automático | `test_entry_gate_failure_reports_and_does_not_confirm`, `test_gate_failure_raises_ticket_and_keeps_transaction_paid`, CF-15 |
| HU-05 | Cerrar automáticamente cuando el vehículo haya pasado | Con limitación | Cierre por tiempo configurable (`gate_open_seconds`); sin sensor de paso | `test_ping_and_open_seconds` |
| HU-06 | Intervenir en placas no reconocidas, parciales o distintas | Cumple | `intervention`: registrar placa, ingreso manual, corregir placa | `test_operator_resolves_unreadable_plate`, `test_operator_corrects_plate_of_vehicle_inside`, CF-06 |
| HU-06 | Auditoría con usuario, fecha, placa y motivo | Cumple | `transaction.created` / `transaction.plate_corrected` / `alert.resolved` con motivo | `test_operator_resolves_unreadable_plate` |
| HU-06 | Placa inválida: no crear e informar | Cumple | Error 422; la alerta sigue pendiente | `test_invalid_manual_plate_keeps_alert_pending`, CF-07 |
| HU-06 | Placa válida: continuar el flujo normal | Cumple | Crea la transacción y ordena la apertura | `test_operator_resolves_unreadable_plate` |

### Épica 2: Gestión de pago

| HU | Criterio de aceptación | Estado | Implementación | Pruebas |
| :--- | :--- | :---: | :--- | :--- |
| HU-07 | Buscar la transacción abierta por placa | Cumple | `GET /public/quote/{plate}` | `test_quote_for_unknown_plate_returns_404` |
| HU-07 | Calcular permanencia y aplicar la tarifa vigente | Cumple | `tariff/domain/charge.py` | `test_quote_applies_current_tariff`, `test_elapsed_minutes` |
| HU-07 | Hasta el límite: hora y fracción | Cumple | `calculate_charge`, modo `hourly` | `test_calculate_charge` |
| HU-07 | Sobre el límite: tarifa plena (y nuevo período cada 12 h) | Cumple | `calculate_charge`, modo `full_rate` | `test_quote_applies_full_rate_and_new_period`, `test_limit_is_configurable` |
| HU-07 | Mostrar tiempo y valor antes de pagar | Cumple | `frontend/app/routes/public/pago.tsx` | CF-08 |
| HU-08 | Mostrar los medios de pago | Cumple | `GET /public/payment-methods`: Tarjeta, PSE, Nequi | CF-09 |
| HU-08 | Generar referencia asociada a la transacción | Cumple | `payment_attempts.reference` (`SGP-…`) | `test_approved_payment_marks_paid_and_records_method` |
| HU-08 | Estado "Procesando pago" mientras se confirma | Cumple | Pantalla con consulta cada 2 s | CF-09 |
| HU-08 | Sin confirmación, la transacción sigue "Ingresado" | Cumple | El estado solo cambia al aprobarse | `test_pending_payment_keeps_transaction_entered` |
| HU-08 | Al confirmar: "Pagado" y "Pago aprobado" | Cumple | `PaymentService` | `test_approved_payment_marks_paid_and_records_method`, `test_approval_is_idempotent` |
| HU-08 | Registrar fecha, hora y medio de pago | Cumple | `paid_at`, `payment_method`, `payment_reference` | `test_approved_payment_marks_paid_and_records_method` |
| HU-09 | Rechazado, cancelado o vencido: sigue "Ingresado" | Cumple | Vencimiento a los 180 s en el barrido de fondo | `test_rejected_payment_can_be_retried_and_is_audited`, `test_payment_timeout_expires_attempt_and_is_audited`, `test_late_approval_after_timeout_does_not_mark_paid` |
| HU-09 | Informar que el pago no se completó | Cumple | Pantalla "El pago no se completó" | CF-10 |
| HU-09 | Permitir un nuevo intento y elegir otra vez el medio | Cumple | Botón **Intentar de nuevo** | `test_rejected_payment_can_be_retried_and_is_audited`, CF-10, CF-11 |
| HU-09 | Auditar cada intento fallido con transacción, medio, referencia, fecha y motivo | Cumple | `payment.failed` con detalle | `test_rejected_payment_can_be_retried_and_is_audited` |

### Épica 3: Salida de vehículos

| HU | Criterio de aceptación | Estado | Implementación | Pruebas |
| :--- | :--- | :---: | :--- | :--- |
| HU-10 | Capturar y reconocer la placa en la salida | Cumple | Cámara de salida del worker | CF-12 |
| HU-10 | Extraer el texto para buscar la transacción | Cumple | `POST /transactions/exit/{plate}/authorize` | `test_authorize_does_not_change_state_until_gate_confirms` |
| HU-11 | Buscar la transacción activa | Cumple | `TransactionService.authorize_exit` | `test_authorize_does_not_change_state_until_gate_confirms` |
| HU-11 | "Ingresado": salida no autorizada, informar y alertar al operador | Cumple | 402 y alerta `payment_pending` | `test_exit_with_pending_payment_is_refused_and_alerts_operator`, `test_repeated_exit_attempts_do_not_duplicate_alert`, CF-13 |
| HU-11 | "Pagado": continuar la salida | Cumple | 200 | `test_exit_completes_only_after_ack` |
| HU-11 | Sin transacción: no autorizada, alerta e intervención del operador | Cumple | 404 y alerta `no_active_transaction` | `test_exit_without_transaction_is_refused_and_alerts_operator`, CF-14 |
| HU-12 | Orden de apertura solo con "Pagado" | Cumple | Automática y manual | `test_unauthorized_exit_never_opens`, `test_manual_exit_refused_when_unpaid` |
| HU-12 | Registrar hora de salida y pasar a "Finalizado" | Cumple | Tras el `ACK` del Arduino | `test_confirm_exit_completes_transaction`, `test_manual_exit_after_payment_completes_when_gate_opens` |
| HU-12 | Sin respuesta: alerta técnica sin alterar el estado | Cumple | La transacción sigue `PAID` | `test_gate_failure_raises_ticket_and_keeps_transaction_paid`, `test_exit_without_ack_does_not_finalize` |
| HU-12 | Cerrar automáticamente después del paso | Con limitación | Cierre por tiempo; sin sensor de paso | `test_ping_and_open_seconds` |

### Épica 4: Administración de tarifas

| HU | Criterio de aceptación | Estado | Implementación | Pruebas |
| :--- | :--- | :---: | :--- | :--- |
| HU-13 | Configurar hora, fracción, duración de la fracción y tarifa plena por tipo | Cumple | `PUT /tariffs/{vehicle_type}`; pantalla **Tarifas** | CF-16 |
| HU-13 | Configurar el límite de tarifa plena | Cumple | `full_rate_after_minutes` | `test_limit_is_configurable` |
| HU-13 | Validar los valores antes de guardar | Cumple | Montos > 0, fracción 1–59 min, límite 1–720 min | `test_invalid_tariff_is_rejected` |
| HU-13 | Modificar cualquier parámetro | Cumple | Ídem | `test_tariff_update_keeps_history_and_does_not_touch_settled` |
| HU-13 | Conservar la anterior en el histórico | Cumple | `tariff_history` | `test_tariff_update_keeps_history_and_does_not_touch_settled` |
| HU-13 | No afectar transacciones liquidadas | Cumple | `tariff_snapshot` y valor congelado al pagar | `test_tariff_update_keeps_history_and_does_not_touch_settled`, CF-17 |
| HU-13 | Aplicar solo desde el cambio | Cumple | La cotización usa la tarifa vigente | `test_new_tariff_applies_to_next_quote` |
| HU-14 | Mostrar configuración anterior y nueva | Cumple | `previous_config`, `new_config` | `test_tariff_update_keeps_history_and_does_not_touch_settled` |
| HU-14 | Tipo de vehículo, usuario, fecha y hora | Cumple | `changed_by_username`, `changed_at` | Ídem |
| HU-14 | Filtrar por tipo y fechas | Cumple | `GET /tariffs/history?vehicle_type&date_from&date_to` | CF-16 |
| HU-14 | No se puede eliminar ni modificar | Cumple | Trigger de inmutabilidad; la API no expone escritura | `test_database_rejects_changes_to_tariff_history` |

### Épica 5: Gestión de cuentas de acceso

| HU | Criterio de aceptación | Estado | Implementación | Pruebas |
| :--- | :--- | :---: | :--- | :--- |
| HU-15 | Crear con usuario, contraseña y rol | Cumple | `POST /users` | `test_account_changes_are_audited` |
| HU-15 | Usuario único | Cumple | Índice único `ix_users_username` | `test_account_changes_are_audited` |
| HU-15 | Política de contraseña (longitud y complejidad) | Cumple | 8–40 caracteres, mayúscula, minúscula y número | `test_weak_password_is_rejected`, CF-18 |
| HU-15 | Hash seguro | Cumple | Argon2 | — |
| HU-15 | Auditar la creación | Cumple | `user.created` | `test_account_changes_are_audited` |
| HU-16 | Modificar rol o contraseña | Cumple | `PATCH /users/{id}`, `reset-password` | `test_account_changes_are_audited` |
| HU-16 | Desactivar sin eliminar | Cumple | `is_active = false`; cierra sus sesiones | `test_inactive_account_gets_specific_message` |
| HU-16 | Auditar con usuario, fecha, hora y cambio | Cumple | `user.updated` con valores anterior y nuevo | `test_account_changes_are_audited` |
| HU-16 | No desactivar al último Administrador activo | Cumple | `LastActiveAdmin` (también al cambiarle el rol) | CF-19 |
| HU-17 | Validar credenciales | Cumple | `AuthService.authenticate` | `test_login_and_logout_are_audited` |
| HU-17 | Error sin indicar si falló el usuario o la contraseña | Cumple | Mensaje único | `test_failed_login_is_audited_without_revealing_cause`, CF-21 |
| HU-17 | Cuenta desactivada: rechazar e informar aunque las credenciales sean correctas | Cumple | 403 `Usuario inactivo` | `test_inactive_account_gets_specific_message`, CF-20 |
| HU-17 | Mostrar solo las funciones del rol | Cumple | Menú por rol + validación en el backend | `test_permission_matrix`, CF-22 |
| HU-17 | Auditar inicio y cierre de sesión | Cumple | `auth.login`, `auth.logout` | `test_login_and_logout_are_audited` |

### Épica 6: Monitoreo y consulta de la operación

| HU | Criterio de aceptación | Estado | Implementación | Pruebas |
| :--- | :--- | :---: | :--- | :--- |
| HU-18 | Listar vehículos dentro con placa, tipo y hora de ingreso | Cumple | `GET /transactions/inside`. Incluye `ENTERED` y `PAID`: ambos siguen ocupando un cupo | `test_inside_list_and_search` |
| HU-18 | Actualización automática | Cumple | Consulta cada 5 s | CF-23 |
| HU-18 | Buscar por placa | Cumple | Filtro `plate` | `test_inside_list_and_search` |
| HU-19 | Filtrar por fechas | Cumple | `GET /reports/revenue` | `test_revenue_counts_only_collected_by_type_and_method` |
| HU-19 | Total y desglose por tipo y medio | Cumple | Ídem | Ídem, CF-24 |
| HU-19 | Solo "Pagado" o "Finalizado" | Cumple | Ídem | Ídem |
| HU-20 | Filtrar por placa, tipo, estado y fechas | Cumple | `GET /transactions` | `test_transaction_filters_and_detail` |
| HU-20 | Mostrar placa, tipo, ingreso, salida, valor y estado | Cumple | Pantalla **Transacciones** | Ídem |
| HU-20 | Detalle con medio de pago e intervención manual | Cumple | `GET /transactions/{id}` | Ídem, CF-25 |
| HU-21 | Ocupación, recaudo, ingresos, salidas y dispositivos | Cumple | `GET /reports/dashboard` | `test_dashboard_summarizes_the_day` |
| HU-21 | Datos actualizados al consultar | Cumple | Cálculo en cada consulta, refresco cada 5 s | Ídem |
| HU-21 | Vista inicial del Administrador | Cumple | `/dashboard` muestra el panel según el rol | CF-26 |

### Épica 7: Soporte técnico

| HU | Criterio de aceptación | Estado | Implementación | Pruebas |
| :--- | :--- | :---: | :--- | :--- |
| HU-22 | Estado de las 2 cámaras y las 2 talanqueras | Cumple | `GET /devices` | `test_device_status_follows_heartbeat` |
| HU-22 | Conectado, sin comunicación o con error | Cumple | `DeviceStatus` | `test_device_status_follows_heartbeat`, `test_silent_worker_is_detected_once` |
| HU-22 | Fecha y hora de la última comunicación | Cumple | `last_seen_at` | `test_device_status_follows_heartbeat` |
| HU-22 | Actualizar al cambiar la comunicación | Cumple | Heartbeat cada 5 s, barrido a los 20 s, pantalla cada 5 s | CF-27 |
| HU-23 | El Operador crea tickets | Cumple | `POST /tickets` | `test_ticket_lifecycle_preserves_history` |
| HU-23 | Componente y descripción obligatorios | Cumple | `TicketCreate` | Ídem |
| HU-23 | Fecha, hora y usuario automáticos | Cumple | `created_at`, `created_by_username` | Ídem |
| HU-23 | Estado "Pendiente", asignado a Soporte | Cumple | `status = pending`, `assigned_role = support` | Ídem, CF-28 |
| HU-23 | Asociar una transacción | Cumple | `transaction_id` opcional | CF-28 |
| HU-23 | El Operador consulta sus tickets | Cumple | Filtro por creador | `test_operator_only_sees_own_tickets` |
| HU-24 | Ticket automático con componente, código, descripción, fecha y transacción | Cumple | `TicketService.open_automatic` desde `technical_events` | `test_device_error_opens_automatic_ticket`, `test_repeated_failure_does_not_duplicate_open_ticket` |
| HU-24 | "Pendiente" y asignado a Soporte | Cumple | Ídem | Ídem |
| HU-25 | Soporte consulta los tickets | Cumple | `GET /tickets` | `test_only_support_manages_tickets` |
| HU-25 | Tomar el ticket: "en revisión" | Cumple | `POST /tickets/{id}/take` | `test_ticket_lifecycle_preserves_history` |
| HU-25 | Registrar diagnóstico, acciones y resultado | Cumple | `PATCH /tickets/{id}/notes` | Ídem |
| HU-25 | Cerrar como "solucionado" | Cumple | `POST /tickets/{id}/close` | Ídem, `test_solved_ticket_cannot_be_reopened` |
| HU-25 | Cerrar como "no solucionado" | Cumple | Ídem; se puede volver a tomar | `test_not_solved_ticket_can_be_taken_again` |
| HU-25 | Historial con estados, usuario, fecha y hora | Cumple | `ticket_history` inmutable | `test_ticket_lifecycle_preserves_history`, `test_database_rejects_changes_to_ticket_history`, CF-29 |

### Épica 8: Auditoría

| HU | Criterio de aceptación | Estado | Implementación | Pruebas |
| :--- | :--- | :---: | :--- | :--- |
| HU-26 | Registrar transacciones, pagos, aperturas, tarifas, cuentas y sesiones | Cumple | `AuditAction` ([03-modelo-de-datos.md](03-modelo-de-datos.md#tickets-y-auditoría)) | `test_login_and_logout_are_audited`, `test_manual_open_flows_through_worker_and_is_audited`, `test_account_changes_are_audited` |
| HU-26 | Usuario o sistema, fecha, hora, elemento y resultado | Cumple | `actor_label`, `created_at`, `entity_*`, `result` | `test_audit_filters` |
| HU-26 | Las consultas no generan registros | Cumple | Solo los casos de uso de escritura registran | `test_queries_do_not_generate_audit_records` |
| HU-27 | Filtrar por acción, usuario y fechas | Cumple | `GET /audit` | `test_audit_filters`, CF-30 |
| HU-27 | Detalle completo de cada registro | Cumple | Pantalla **Auditoría** | CF-30 |
| HU-27 | Orden cronológico | Cumple | Por `created_at`, con selector de orden | `test_audit_filters` |
| HU-28 | Ningún rol puede modificar ni eliminar | Cumple | La API no expone escritura | `test_audit_api_has_no_write_operations` |
| HU-28 | Los registros conservan su información | Cumple | Triggers contra `UPDATE`, `DELETE` y `TRUNCATE` | `test_database_rejects_changes_to_audit_logs`, CF-31 |
