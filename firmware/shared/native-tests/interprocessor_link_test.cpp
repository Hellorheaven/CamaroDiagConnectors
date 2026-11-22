#include "../interprocessor_link.h"
#include <cassert>
using namespace cd::link;
int main(){
  uint8_t tx[Size]{},rx[Size]{};
  Packet p,reply;
  DiagnosticSlave slave;
  assert(encode(p,tx,Size));
  assert(slave.transact(tx,Size,rx,Size));
  assert(decode(rx,Size,reply)&&correlate(p,reply));
  p.op=Op::Status;p.seq=1;
  assert(encode(p,tx,Size)&&slave.transact(tx,Size,rx,Size));
  assert(decode(rx,Size,reply)&&correlate(p,reply));
  assert(!slave.transact(tx,Size,rx,Size)&&slave.closed());
  p.seq=0;assert(encode(p,tx,Size));
  DiagnosticSlave corrupt;tx[10]=1;
  assert(!corrupt.transact(tx,Size,rx,Size)&&corrupt.closed());
  DiagnosticSlave shortPacket;assert(!shortPacket.transact(tx,Size-1,rx,Size));
  DiagnosticSlave wrongKind;p.kind=Kind::Response;
  assert(encode(p,tx,Size)&&!wrongKind.transact(tx,Size,rx,Size));
  p.kind=Kind::Request;p.op=static_cast<Op>(3);
  assert(!encode(p,tx,Size));
}
