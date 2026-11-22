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
  auto wrap=p;wrap.sequence=0xffffffffu;
  assert(!successor(wrap,n));
}
