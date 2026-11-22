#include "../src/journal_record.h"
#include <cassert>
using namespace cd::journal;
int main(){
  Record p;
  uint8_t bytes[RecordSize]{};
  assert(!encode(p,bytes,sizeof(bytes)));
  p.transaction[0]=1;p.manifestDigest[0]=2;
  assert(encode(p,bytes,sizeof(bytes)));
  Record decoded;
  assert(decode(bytes,sizeof(bytes),decoded));
  assert(classify(decoded)==BootDisposition::SafeButBlocked);
  Record n=p;n.stage=Stage::EraseIntent;n.sequence=1;
  assert(successor(p,n));
  assert(classify(n)==BootDisposition::RecoveryRequired);
  assert(!successor(n,p));
  Record wrong=n;wrong.sequence++;wrong.stage=Stage::ProgramIntent;wrong.manifestDigest[0]^=1;
  assert(!successor(n,wrong));
  wrong=n;wrong.sequence++;wrong.stage=Stage::Completed;
  assert(!successor(n,wrong));
  auto recovery=n;recovery.sequence++;recovery.stage=Stage::RecoveryRequired;
  assert(successor(n,recovery)&&classify(recovery)==BootDisposition::RecoveryRequired);
  auto retry=recovery;retry.sequence++;retry.stage=Stage::EraseIntent;
  assert(!successor(recovery,retry));
  bytes[40]^=1;assert(!decode(bytes,sizeof(bytes),decoded));
  assert(classify(decoded)==BootDisposition::Corrupt);
  assert(!decode(bytes,sizeof(bytes)-1,decoded));
  auto abort=p;abort.sequence++;abort.stage=Stage::Aborted;
  assert(successor(p,abort));
  for(uint8_t stage=1;stage<=10;++stage){
    for(uint32_t seq=0;seq<=9;++seq){
      Record candidate=p;candidate.stage=static_cast<Stage>(stage);candidate.sequence=seq;
      const bool expected=stage==9?seq==1:stage==10?(seq>=2&&seq<=7):seq==uint32_t(stage-1);
      assert(valid(candidate)==expected);
      assert(encode(candidate,bytes,sizeof(bytes))==expected);
      if(expected)assert(decode(bytes,sizeof(bytes),decoded));
    }
  }
  // Well-formed CRC cannot turn an unreachable checkpoint into a valid one.
  assert(encode(p,bytes,sizeof(bytes)));
  bytes[8]=1;
  const uint32_t checksum=cd::crc32(bytes,60);
  for(unsigned i=0;i<4;++i)bytes[60+i]=uint8_t(checksum>>(8*i));
  assert(!decode(bytes,sizeof(bytes),decoded));
  // Shared independent wire fixture pinned in CamaroDiag #70.
  const uint8_t golden[RecordSize]={0x43,0x44,0x4a,0x01,0x02,0x00,0x00,0x00,0x01,0x00,0x00,0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f,0x10,0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,0x2e,0x2f,0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x37,0x38,0x39,0x3a,0x3b,0x3c,0x3d,0x3e,0x3f,0xa7,0x5e,0x21,0xb6};
  Record vector;
  assert(decode(golden,sizeof(golden),vector));
  assert(vector.stage==Stage::EraseIntent&&vector.sequence==1);
  for(unsigned i=0;i<16;++i)assert(vector.transaction[i]==i+1);
  for(unsigned i=0;i<32;++i)assert(vector.manifestDigest[i]==i+32);
  assert(encode(vector,bytes,sizeof(bytes)));
  assert(std::memcmp(bytes,golden,sizeof(bytes))==0);
  auto wrap=p;wrap.sequence=0xffffffffu;
  assert(!successor(wrap,n));
}
