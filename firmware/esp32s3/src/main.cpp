#include <Arduino.h>
#include <cstring>

// Prototype découverte série, AUCUNE opération sur véhicule ni puce.
static constexpr size_t MAX_LINE = 96;
static char line[MAX_LINE + 1];
static size_t count = 0;
static bool discarding = false;

static void respond(const char *cmd) {
  if (strcmp(cmd, "PING") == 0) {
    Serial.println("PONG CamaroDiagConnectors 0.1.0");
  } else if (strcmp(cmd, "CAPS") == 0) {
    Serial.println("CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled");
  } else if (strcmp(cmd, "STATUS") == 0) {
    Serial.println("STATUS mode=prototype write=disabled");
  } else {
    Serial.println("ERR UNSUPPORTED");
  }
}

void setup() {
  Serial.begin(115200);
}

void loop() {
  while (Serial.available() > 0) {
    char c = static_cast<char>(Serial.read());
    if (c == '\n') {
      if (discarding) {
        Serial.println("ERR LINE_TOO_LONG");
      } else {
        if (count != 0 && line[count - 1] == '\r') --count;
        line[count] = '\0';
        respond(line);
      }
      count = 0;
      discarding = false;
    } else if (!discarding) {
      if (count < MAX_LINE) {
        line[count++] = c;
      } else {
        discarding = true;
      }
    }
  }
}
