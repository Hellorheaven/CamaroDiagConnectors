#include "../src/discovery_session.h"
#include <cassert>
#include <cstring>
using namespace cd;
int main(){
  DiscoverySession s;
  FrameView v;
  v.opcode=1;
  uint8_t out[256]{};
  auto n=s.dispatch(v,out,sizeof(out));
  FrameView reply;
  assert(n && decode(out,n,reply)==FrameError::None);
  assert(reply.sequence==0 && reply.opcode==1);
  assert(reply.length==std::strlen("PONG CamaroDiagConnectors 0.1.0"));
  assert(!std::memcmp(reply.payload,"PONG CamaroDiagConnectors 0.1.0",reply.length));
  v.sequence=1; v.opcode=2;
  n=s.dispatch(v,out,sizeof(out));
  assert(n && decode(out,n,reply)==FrameError::None);
  assert(reply.opcode==2 && reply.sequence==1);
  v.sequence=2; v.opcode=3;
  n=s.dispatch(v,out,sizeof(out));
  assert(n && decode(out,n,reply)==FrameError::None);
  assert(reply.length==std::strlen("STATUS mode=prototype write=disabled"));
  assert(!std::memcmp(reply.payload,"STATUS mode=prototype write=disabled",reply.length));
  assert(!s.dispatch(v,out,sizeof(out)) && s.closed());
  v.sequence=3;
  assert(!s.dispatch(v,out,sizeof(out)));
  DiscoverySession skip; v.sequence=1;
  assert(!skip.dispatch(v,out,sizeof(out)) && skip.closed());
  DiscoverySession payload; v.sequence=0; v.length=1;
  assert(!payload.dispatch(v,out,sizeof(out)) && payload.closed());
  DiscoverySession unknown; v.length=0; v.opcode=4;
  assert(!unknown.dispatch(v,out,sizeof(out)) && unknown.closed());
  DiscoverySession shortOutput; v.opcode=1;
  assert(!shortOutput.dispatch(v,out,12) && shortOutput.closed());
  DiscoverySession wrongOrder; v.sequence=0; v.opcode=2;
  assert(!wrongOrder.dispatch(v,out,sizeof(out)) && wrongOrder.closed());
  DiscoverySession repeated; v.opcode=1;
  assert(repeated.dispatch(v,out,sizeof(out)));
  v.sequence=1;
  assert(!repeated.dispatch(v,out,sizeof(out)) && repeated.closed());
  DiscoverySession complete;
  for(unsigned i=0;i<3;++i) {
    v.sequence=uint16_t(i); v.opcode=uint8_t(i+1);
    assert(complete.dispatch(v,out,sizeof(out)));
  }
  assert(complete.closed());
  v.sequence=3; v.opcode=1;
  assert(!complete.dispatch(v,out,sizeof(out)));
  assert(!encodeDiscovery(1,0,nullptr,1,out,sizeof(out)));
  assert(!encodeDiscovery(1,0,nullptr,4097,out,sizeof(out)));
}
