#include "../isotp_observer.h"
#include <cassert>
#include <cstring>
using R=cd::IsoTpObserver::Result;
int main(){
  cd::IsoTpObserver single(0x7e8,false);
  uint8_t sf[]={3,0x62,0xf1,0x90,0};
  assert(single.feed(0x7e9,false,sf,sizeof(sf),0)==R::Ignored);
  assert(single.feed(0x7e8,false,sf,sizeof(sf),0)==R::Complete);
  assert(single.size()==3&&single.message()[2]==0x90);
  assert(single.consume()&&!single.message());
  uint8_t ff[]={0x10,10,1,2,3,4,5,6};
  uint8_t cf[]={0x21,7,8,9,10};
  cd::IsoTpObserver multi(0x7e8,false);
  assert(multi.feed(0x7e8,false,ff,8,10)==R::Pending);
  assert(multi.feed(0x7e8,false,cf,5,20)==R::Complete);
  for(unsigned i=0;i<10;++i)assert(multi.message()[i]==i+1);
  cd::IsoTpObserver time(0x7e8,false);
  assert(time.feed(0x7e8,false,ff,8,0)==R::Pending);
  assert(time.poll(1000)==R::Fault&&!time.message());
  cd::IsoTpObserver seq(0x7e8,false);cf[0]=0x22;
  seq.feed(0x7e8,false,ff,8,0);
  assert(seq.feed(0x7e8,false,cf,5,1)==R::Fault);
  cd::IsoTpObserver invalid(0x800,false);
  assert(invalid.feed(0x800,false,sf,5,0)==R::Fault);
  cd::IsoTpObserver extended(0x18daf110,true);
  assert(extended.feed(0x18daf110,true,sf,5,0)==R::Complete);
  cd::IsoTpObserver bad(0x7e8,false);sf[0]=7;
  assert(bad.feed(0x7e8,false,sf,5,0)==R::Fault);
}
