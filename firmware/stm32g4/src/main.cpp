#include <Arduino.h>

// Isolated Nucleo bring-up only. Do not wire a target, transceiver or ESP32.
// Keep candidate signal pins high impedance; the board's external interlocks
// are required for actual safety. No CAN, SPI or target power is enabled.
static const uint32_t targetPins[] = {PA5, PA7, PA6, PB6, PA11, PA12, PA8};
void setup() {
  for (auto pin : targetPins) pinMode(pin, INPUT);
  Serial.begin(115200);
  Serial.println("CamaroDiagConnectors STM32G474 prototype");
  Serial.println("STATUS route=none tx=disabled power=disabled");
}
void loop() {
  // ST-LINK virtual COM diagnostic only, no input command interpreter.
  static uint32_t last=0;
  const uint32_t now=millis();
  if(uint32_t(now-last)>=1000u) {
    last=now;
    Serial.println("STATUS route=none tx=disabled power=disabled");
  }
}
