#pragma once
#include "binary_frame.h"
#include <cstring>

// Public discovery ONLY. No authentication, no physical target access.
// The sequence is for correlation, not cryptographic replay protection.
namespace cd {
inline size_t encodeDiscovery(uint8_t opcode, uint16_t seq,
                              const uint8_t* payload, size_t length,
                              uint8_t* out, size_t capacity) {
  if (!out || opcode < 1 || opcode > 3 || length > 4096 ||
      capacity < length + 12 || (length && !payload)) return 0;
  out[0]='C'; out[1]='D'; out[2]=1; out[3]=opcode;
  out[4]=uint8_t(seq); out[5]=uint8_t(seq >> 8);
  out[6]=uint8_t(length); out[7]=uint8_t(length >> 8);
  if (length) std::memcpy(out+8,payload,length);
  const uint32_t crc=crc32(out,length+8);
  for(unsigned i=0;i<4;++i) out[length+8+i]=uint8_t(crc>>(8*i));
  return length+12;
}
class DiscoverySession {
 public:
  // Strict request payload = empty. All replies are nonempty fixed ASCII.
  // Close session after error or the third canonical reply. No downgrade fallback.
  size_t dispatch(const FrameView& request, uint8_t* out, size_t capacity) {
    if (closed_ || request.length != 0 || request.sequence != next_ ||
        request.opcode != next_ + 1)
      return reject();
    const char* reply=nullptr;
    switch(request.opcode) {
      case 1: reply="PONG CamaroDiagConnectors 0.1.0"; break;
      case 2: reply="CAPS hs_can=disabled sw_can=disabled eeprom_read=disabled eeprom_write=disabled ecu_flash=disabled j2534=disabled"; break;
      case 3: reply="STATUS mode=prototype write=disabled"; break;
      default: return reject();
    }
    const size_t n=encodeDiscovery(request.opcode,request.sequence,
       reinterpret_cast<const uint8_t*>(reply),std::strlen(reply),out,capacity);
    if (!n) return reject();
    if(next_==2u) closed_=true;
    else ++next_;
    return n;
  }
  bool closed() const { return closed_; }
  void close() { closed_=true; }
 private:
  size_t reject() { close(); return 0; }
  uint16_t next_=0;
  bool closed_=false;
};
}
