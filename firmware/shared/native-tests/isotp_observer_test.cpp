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
  cd::IsoTpObserver shortFinal(0x7e8,false);cf[0]=0x21;
  assert(shortFinal.feed(0x7e8,false,ff,8,0)==R::Pending);
  assert(shortFinal.feed(0x7e8,false,cf,4,1)==R::Fault);
  cd::IsoTpObserver invalid(0x800,false);
  assert(invalid.feed(0x800,false,sf,5,0)==R::Fault);
  cd::IsoTpObserver extended(0x18daf110,true);
  assert(extended.feed(0x18daf110,true,sf,5,0)==R::Complete);
  cd::IsoTpObserver bad(0x7e8,false);sf[0]=7;
  assert(bad.feed(0x7e8,false,sf,5,0)==R::Fault);
  // Synthetic FD frames: 12-byte escaped SF, 64-byte FF and shorter final CF.
  uint8_t fdSingle[12]={0,10,1,2,3,4,5,6,7,8,9,10};
  cd::IsoTpObserver fd(0x7e8,false,true);
  assert(fd.feed(0x7e8,false,fdSingle,12,0)==R::Ignored);
  assert(fd.feed(0x7e8,false,fdSingle,12,1,true)==R::Complete);
  assert(fd.size()==10&&fd.message()[9]==10&&fd.consume());
  uint8_t fdFirst[64]={0x10,70};
  for(unsigned i=2;i<64;++i)fdFirst[i]=uint8_t(i-2);
  uint8_t fdLast[12]={0x21,62,63,64,65,66,67,68,69};
  assert(fd.feed(0x7e8,false,fdFirst,64,2,true)==R::Pending);
  assert(fd.feed(0x7e8,false,fdLast,12,3,true)==R::Complete);
  assert(fd.size()==70);
  for(unsigned i=0;i<70;++i)assert(fd.message()[i]==i);
  cd::IsoTpObserver badFd(0x7e8,false,true);
  assert(badFd.feed(0x7e8,false,fdSingle,10,0,true)==R::Fault);
  cd::IsoTpObserver badEscape(0x7e8,false,true);
  fdSingle[0]=1;
  assert(badEscape.feed(0x7e8,false,fdSingle,12,0,true)==R::Fault);
  cd::IsoTpObserver shortFd(0x7e8,false,true);
  assert(shortFd.feed(0x7e8,false,fdFirst,64,0,true)==R::Pending);
  assert(shortFd.feed(0x7e8,false,fdLast,8,1,true)==R::Fault);
  cd::IsoTpObserver longCf(0x7e8,false,true);
  uint8_t ff12[12]={0x10,30};
  assert(longCf.feed(0x7e8,false,ff12,12,0,true)==R::Pending);
  assert(longCf.feed(0x7e8,false,fdFirst,64,1,true)==R::Fault);
  cd::IsoTpObserver classic(0x7e8,false);
  assert(classic.feed(0x7e8,false,fdSingle,12,0,true)==R::Ignored);
  assert(classic.feed(0x7e8,false,fdSingle,12,0)==R::Fault);
}
