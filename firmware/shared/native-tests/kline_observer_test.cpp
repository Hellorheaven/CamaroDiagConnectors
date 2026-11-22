#include "../kline_observer.h"
#include <cassert>
using namespace cd;
int main(){
  // Synthetic addressed response, not an ECU command or a validated pinout.
  const uint8_t frame[]={0x82,0xf1,0x12,0x61,0x01,0xe7};
  KlineFrame f;
  assert(inspectKwpFrame(frame,sizeof(frame),0xf1,0x12,f)==KlineError::None);
  assert(f.length==2&&f.payload[0]==0x61&&f.payload[1]==1);
  assert(inspectKwpFrame(frame,sizeof(frame),0x12,0xf1,f)==KlineError::Address);
  assert(f.payload==nullptr&&f.length==0);
  assert(inspectKwpFrame(frame,sizeof(frame)-1,0xf1,0x12,f)==KlineError::Length);
  const uint8_t extended[]={0x80,0xf1,0x12,2,0x61,1,0xe7};
  assert(inspectKwpFrame(extended,sizeof(extended),0xf1,0x12,f)==KlineError::None&&f.length==2);
  uint8_t corrupt[sizeof(frame)];
  std::memcpy(corrupt,frame,sizeof(frame));corrupt[5]^=1;
  assert(inspectKwpFrame(corrupt,sizeof(corrupt),0xf1,0x12,f)==KlineError::Checksum);
  corrupt[0]=0xc2;
  assert(inspectKwpFrame(corrupt,sizeof(corrupt),0xf1,0x12,f)==KlineError::Format);
  assert(inspectKwpFrame(nullptr,0,0xf1,0x12,f)==KlineError::Size);
  uint8_t max[260]={0x80,0xf1,0x12,255};
  for(size_t i=4;i<259;++i)max[i]=uint8_t(i);
  for(size_t i=0;i<259;++i)max[259]=uint8_t(max[259]+max[i]);
  assert(inspectKwpFrame(max,sizeof(max),0xf1,0x12,f)==KlineError::None&&f.length==255);
}
