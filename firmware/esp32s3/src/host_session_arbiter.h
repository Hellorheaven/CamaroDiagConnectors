#pragma once
#include "host_interface_policy.h"
#include <cstdint>
#include <limits>

namespace cd {
// Single-owner task model. Lease generation is a local stale-callback guard,
// never a credential. No hardware I/O, recovery clearing or programming.
class HostSessionArbiter {
 public:
  struct Lease {
    HostInterface mode=HostInterface::None;
    uint64_t generation=0;
  };
  explicit HostSessionArbiter(bool unresolved=false):recovery_(unresolved){}
  HostSessionArbiter(const HostSessionArbiter&)=delete;
  HostSessionArbiter& operator=(const HostSessionArbiter&)=delete;
  bool acquire(HostInterface mode,const InterfaceEvidence& e,Lease& out){
    out=Lease{};
    if(recovery_||owner_.generation||last_==std::numeric_limits<uint64_t>::max())return false;
    if(interfaceAdmission(mode,HostOperation::DiagnosticRead,false,e)!=InterfaceBlock::None)return false;
    owner_.mode=mode;owner_.generation=++last_;out=owner_;
    return true;
  }
  bool owns(const Lease& lease)const{
    return owner_.generation&&lease.generation==owner_.generation&&lease.mode==owner_.mode;
  }
  bool allowsRead(const Lease& lease,const InterfaceEvidence& e)const{
    return !recovery_&&owns(lease)&&
      interfaceAdmission(lease.mode,HostOperation::DiagnosticRead,false,e)==InterfaceBlock::None;
  }
  bool release(const Lease& lease){
    if(!owns(lease))return false;
    owner_=Lease{};return true;
  }
  void latchRecovery(){recovery_=true;owner_=Lease{};}
  bool recoveryRequired()const{return recovery_;}
 private:
  Lease owner_;
  uint64_t last_=0;
  bool recovery_=false;
};
}
