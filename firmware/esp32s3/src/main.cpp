#include <Arduino.h>

#ifdef CD_BINARY_DISCOVERY
#include "frame_receiver.h"
#include "discovery_session.h"

static cd::FrameReceiver receiver;
static cd::DiscoverySession session;
static uint8_t reply[256]{};

void setup() { Serial.begin(115200); }

void loop() {
  using R=cd::FrameReceiver::Result;
  if (receiver.poll(millis()) == R::Fault) session.close();
  // Development build: after a protocol error, stop responding until reset.
  // No automatic downgrade, no physical commands.
  for(unsigned n=0;n<64 && Serial.available()>0;++n) {
    const int b=Serial.read();
    if(b<0 || session.closed()) continue;
    const auto result=receiver.feed(static_cast<uint8_t>(b),millis());
    if(result==R::Fault) { session.close(); continue; }
    if(result==R::Ready) {
      const auto* frame=receiver.frame();
      if(!frame) { session.close(); continue; }
      const size_t length=session.dispatch(*frame,reply,sizeof(reply));
      if(!length || Serial.write(reply,length)!=length) session.close();
      if(!receiver.consume()) session.close();
    }
  }
}
#else
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

#endif
