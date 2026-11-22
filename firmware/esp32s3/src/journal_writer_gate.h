#pragma once
#include "journal_record.h"

namespace cd { namespace journal {
// The NVS writer is owned by one firmware task. An existing record from a
// previous boot is evidence only. There is intentionally no recovery/resume
// or clear API here. This model never issues hardware operations.
enum class StoredState { Missing, Valid, Error };
class WriterGate {
 public:
  bool permits(StoredState state,const Record& stored,const Record& next){
    if(locked_)return false;
    if(state==StoredState::Error){locked_=true;return false;}
    if(!owned_){
      if(state!=StoredState::Missing){locked_=true;return false;}
      return valid(next)&&next.stage==Stage::Prepared&&next.sequence==0;
    }
    // Detect deletion, stale prefixes or arbitrary replacement while this boot
    // owns a transaction. CRC correctness alone is insufficient.
    if(state!=StoredState::Valid||!same(stored,last_)){
      locked_=true;return false;
    }
    return successor(last_,next);
  }
  void durable(const Record& accepted){
    last_=accepted;owned_=true;
  }
  void uncertain(){locked_=true;}
  bool locked()const{return locked_;}
 private:
  static bool same(const Record& a,const Record& b){
    return valid(a)&&valid(b)&&a.stage==b.stage&&a.sequence==b.sequence&&
      std::memcmp(a.transaction,b.transaction,16)==0&&
      std::memcmp(a.manifestDigest,b.manifestDigest,32)==0;
  }
  bool owned_=false,locked_=false;
  Record last_;
};
} }
