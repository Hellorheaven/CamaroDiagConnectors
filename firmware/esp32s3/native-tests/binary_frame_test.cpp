#include "../src/binary_frame.h"
#include <cassert>
#include <vector>
using namespace cd;
static void seal(std::vector<uint8_t>& f) {
  const uint32_t crc = crc32(f.data(), f.size()-4);
  for (unsigned i=0; i<4; ++i) f[f.size()-4+i] = uint8_t(crc >> (8*i));
}
int main() {
  const uint8_t check[] = {'1','2','3','4','5','6','7','8','9'};
  assert(crc32(check, sizeof(check)) == 0xcbf43926u);
  std::vector<uint8_t> f = {'C','D',1,1,0x34,0x12,2,0,0xaa,0xbb,0,0,0,0};
  seal(f);
  FrameView v;
  assert(decode(f.data(),f.size(),v) == FrameError::None);
  assert(v.opcode == 1 && v.sequence == 0x1234 && v.length == 2 && v.payload[1] == 0xbb);
  assert(decode(f.data(),f.size()-1,v) == FrameError::Length);
  assert(v.payload == nullptr);
  f[9] ^= 1; assert(decode(f.data(),f.size(),v) == FrameError::Crc);
  f[9] ^= 1; f[3]=4; seal(f); assert(decode(f.data(),f.size(),v) == FrameError::Opcode);
  f[3]=1; f[2]=2; seal(f); assert(decode(f.data(),f.size(),v) == FrameError::Header);
  assert(decode(nullptr,12,v) == FrameError::Size);
  std::vector<uint8_t> large(4108,0);
  large[0]='C'; large[1]='D'; large[2]=1; large[3]=3; large[7]=16; seal(large);
  assert(decode(large.data(),large.size(),v) == FrameError::None && v.length == 4096);
  large.push_back(0);
  assert(decode(large.data(),large.size(),v) == FrameError::Size);
}
