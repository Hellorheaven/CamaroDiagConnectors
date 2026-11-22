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
  auto wrap=p;wrap.sequence=0xffffffffu;
  assert(!successor(wrap,n));
}
