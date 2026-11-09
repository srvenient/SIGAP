/*
 * SIGAP - Control de talanqueras por relé.
 *
 * Protocolo serial (9600 baudios):
 *   PC -> Arduino
 *     E          Abrir talanquera de entrada
 *     S          Abrir talanquera de salida
 *     P          Comprobar comunicación
 *     T<seg>\n   Cambiar el tiempo de apertura (1 a 60 segundos), por ejemplo T5
 *   Arduino -> PC
 *     READY      El Arduino terminó de iniciar
 *     ACK:E      Orden recibida y relé activado (ACK:S para la salida)
 *     CLOSED:E   Relé desactivado, talanquera cerrada (CLOSED:S para la salida)
 *     PONG       Respuesta a P
 *     OK:T=<s>   Tiempo de apertura actualizado
 *     ERR:T      Tiempo fuera de rango
 *
 * Usa millis() en lugar de delay() para que una talanquera abierta no detenga a la otra.
 */

const int PIN_TALANQUERA_ENTRADA = 8;
const int PIN_TALANQUERA_SALIDA = 9;

// Si tu módulo de relés se activa en bajo, intercambia estos dos valores.
const int RELE_ACTIVO = HIGH;
const int RELE_REPOSO = LOW;

const unsigned long TIEMPO_MIN_SEGUNDOS = 1;
const unsigned long TIEMPO_MAX_SEGUNDOS = 60;

struct Talanquera {
  int pin;
  char codigo;
  bool abierta;
  unsigned long abiertaDesde;
};

Talanquera talanqueras[] = {
  { PIN_TALANQUERA_ENTRADA, 'E', false, 0 },
  { PIN_TALANQUERA_SALIDA, 'S', false, 0 },
};
const int TOTAL_TALANQUERAS = sizeof(talanqueras) / sizeof(talanqueras[0]);

unsigned long tiempoAperturaMs = 3000;

bool leyendoTiempo = false;
unsigned long tiempoRecibido = 0;

void setup() {
  Serial.begin(9600);

  for (int i = 0; i < TOTAL_TALANQUERAS; i++) {
    // Primero el nivel y luego el modo, para que el relé no se active al arrancar
    digitalWrite(talanqueras[i].pin, RELE_REPOSO);
    pinMode(talanqueras[i].pin, OUTPUT);
  }

  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0) {
    procesarCaracter((char)Serial.read());
  }
  cerrarTalanquerasVencidas();
}

void procesarCaracter(char caracter) {
  if (leyendoTiempo) {
    if (caracter >= '0' && caracter <= '9') {
      // Se limita para que una entrada larga no desborde el acumulado
      if (tiempoRecibido <= TIEMPO_MAX_SEGUNDOS) {
        tiempoRecibido = tiempoRecibido * 10 + (caracter - '0');
      }
    } else if (caracter == '\n') {
      aplicarTiempo();
      leyendoTiempo = false;
    }
    return;
  }

  switch (caracter) {
    case 'E':
    case 'S':
      abrirTalanquera(caracter);
      break;
    case 'P':
      Serial.println("PONG");
      break;
    case 'T':
      leyendoTiempo = true;
      tiempoRecibido = 0;
      break;
    default:
      break;
  }
}

void aplicarTiempo() {
  if (tiempoRecibido < TIEMPO_MIN_SEGUNDOS || tiempoRecibido > TIEMPO_MAX_SEGUNDOS) {
    Serial.println("ERR:T");
    return;
  }

  tiempoAperturaMs = tiempoRecibido * 1000UL;
  Serial.print("OK:T=");
  Serial.println(tiempoRecibido);
}

void abrirTalanquera(char codigo) {
  for (int i = 0; i < TOTAL_TALANQUERAS; i++) {
    if (talanqueras[i].codigo == codigo) {
      digitalWrite(talanqueras[i].pin, RELE_ACTIVO);
      talanqueras[i].abierta = true;
      // Una orden repetida mientras está abierta reinicia el tiempo
      talanqueras[i].abiertaDesde = millis();

      Serial.print("ACK:");
      Serial.println(codigo);
      return;
    }
  }
}

void cerrarTalanquerasVencidas() {
  for (int i = 0; i < TOTAL_TALANQUERAS; i++) {
    // La resta con unsigned sigue siendo correcta cuando millis() se reinicia a los 49 días
    if (talanqueras[i].abierta && millis() - talanqueras[i].abiertaDesde >= tiempoAperturaMs) {
      digitalWrite(talanqueras[i].pin, RELE_REPOSO);
      talanqueras[i].abierta = false;

      Serial.print("CLOSED:");
      Serial.println(talanqueras[i].codigo);
    }
  }
}
