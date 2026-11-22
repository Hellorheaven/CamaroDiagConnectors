#include "../src/journal_writer_gate.h"
#include <cassert>
using namespace cd::journal;
int main(){
  Record prepared;
  prepared.transaction[0]=1;prepared.manifestDigest[0]=2;
  Record erase=prepared;erase.stage=Stage::EraseIntent;erase.sequence=1;
  Record program=erase;program.stage=Stage::ProgramIntent;program.sequence=2;
  WriterGate fresh;
  assert(!fresh.permits(StoredState::Missing,Record{},erase));
  assert(fresh.permits(StoredState::Missing,Record{},prepared));
  fresh.durable(prepared);
  assert(fresh.permits(StoredState::Valid,prepared,erase));
  fresh.durable(erase);
  assert(fresh.permits(StoredState::Valid,erase,program));
  assert(!fresh.permits(StoredState::Valid,prepared,erase)&&fresh.locked());
  assert(!fresh.permits(StoredState::Valid,erase,program));
  WriterGate reboot;
  assert(!reboot.permits(StoredState::Valid,erase,program)&&reboot.locked());
  WriterGate missing;
  missing.durable(prepared);
  assert(!missing.permits(StoredState::Missing,Record{},prepared)&&missing.locked());
  WriterGate corrupt;
  assert(!corrupt.permits(StoredState::Error,Record{},prepared)&&corrupt.locked());
  WriterGate uncertain;
  assert(uncertain.permits(StoredState::Missing,Record{},prepared));
  uncertain.uncertain();
  assert(!uncertain.permits(StoredState::Missing,Record{},prepared)&&uncertain.locked());
  WriterGate foreign;
  foreign.durable(prepared);
  Record replacement=prepared;replacement.manifestDigest[2]=3;
  assert(!foreign.permits(StoredState::Valid,replacement,erase)&&foreign.locked());
}
