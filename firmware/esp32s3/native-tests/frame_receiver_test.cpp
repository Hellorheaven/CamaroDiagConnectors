#include "../src/frame_receiver.h"
#include <cassert>
#include <vector>
using namespace cd;
static std::vector<uint8_t> sample() {
  std::vector<uint8_t> v={'C','D',1,1,0x34,0x12,0,0,0,0,0,0};
  const uint32_t crc=crc32(v.data(),8);
  for(unsigned i=0;i<4;++i)v[8+i]=uint8_t(crc>>(8*i));
  return v;
}
int main(){
  FrameReceiver r;
  using R=FrameReceiver::Result;
  const auto v=sample();
  assert(r.poll(0)==R::Pending);
  assert(!r.consume());
  for(size_t i=0;i<v.size();++i)
    assert(r.feed(v[i],uint32_t(i))==(i+1==v.size()?R::Ready:R::Pending));
  assert(r.frame() && r.frame()->sequence==0x1234);
  assert(r.consume() && !r.frame());
  assert(r.feed('C',100)==R::Pending);
  assert(r.poll(2100)==R::Fault);
  assert(r.feed('C',2101)==R::Fault && !r.consume());
  r.resetSession();
  assert(r.feed('X',0)==R::Fault);
  r.resetSession();
  auto bad=v; bad.back()^=1;
  for(size_t i=0;i<bad.size();++i)
    assert(r.feed(bad[i],0)==(i+1==bad.size()?R::Fault:R::Pending));
  r.resetSession();
  for(auto b:v)r.feed(b,0);
  assert(r.feed('C',1)==R::Fault && !r.frame());
  r.resetSession();
  assert(r.feed('C',0xfffffff0u)==R::Pending);
  assert(r.poll(0x000007c0u)==R::Fault);
}
