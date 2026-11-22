#include <Arduino.h>
#include "discovery_parser.h"

static DiscoveryParser parser;

static void respond(DiscoveryParser::Result result) {
  using R = DiscoveryParser::Result;
  switch (result) {
    case R::Ping: Serial.println("PONG CamaroDiagConnectors 0.1.0"); break;
    case R::Caps: Serial.println("CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled"); break;
    case R::Status: Serial.println("STATUS mode=prototype write=disabled"); break;
    case R::Unsupported: Serial.println("ERR UNSUPPORTED"); break;
    case R::Malformed: Serial.println("ERR MALFORMED"); break;
    case R::TooLong: Serial.println("ERR LINE_TOO_LONG"); break;
    case R::Timeout: Serial.println("ERR TIMEOUT"); break;
    case R::None: break;
  }
}

void setup() { Serial.begin(115200); }

void loop() {
  parser.expire(millis());
  // Limit each iteration so sustained USB traffic cannot monopolize the loop.
  for (unsigned n = 0; n < 64 && Serial.available() > 0; ++n) {
    const int byte = Serial.read();
    if (byte >= 0) respond(parser.feed(static_cast<uint8_t>(byte), millis()));
  }
}
