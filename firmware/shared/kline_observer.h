#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace cd {
// Offline ISO 14230-2 frame inspection, addressed physical format only (10xxxxxx).
// Captures must already be separated into individual frames by the caller.
// No initialization, timing, ECU transmission, ISO 9141 or functional addressing.
enum class KlineError:uint8_t { None, Size, Format, Length, Address, Checksum };
struct KlineFrame {
  uint8_t target=0, source=0;
  const uint8_t* payload=nullptr;
  size_t length=0;
};
inline KlineError inspectKwpFrame(const uint8_t* data,size_t size,
    uint8_t expectedTarget,uint8_t expectedSource,KlineFrame& result) {
  result=KlineFrame{};
  if(!data||size<5||size>260)return KlineError::Size;
  if((data[0]&0xc0u)!=0x80u)return KlineError::Format;
  size_t header=3, length=data[0]&0x3fu;
  if(length==0){
    if(size<6)return KlineError::Size;
    header=4;length=data[3];
  }
  if(length==0||size!=header+length+1)return KlineError::Length;
  if(expectedTarget==expectedSource||data[1]!=expectedTarget||data[2]!=expectedSource)
    return KlineError::Address;
  uint8_t checksum=0;
  for(size_t i=0;i<size-1;++i)checksum=uint8_t(checksum+data[i]);
  if(checksum!=data[size-1])return KlineError::Checksum;
  result.target=data[1];result.source=data[2];result.payload=data+header;result.length=length;
  return KlineError::None;
}
}
