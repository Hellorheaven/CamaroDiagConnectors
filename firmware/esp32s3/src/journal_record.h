#pragma once
#include <cstdint>
#include <cstddef>
#include <cstring>
#include "binary_frame.h"

namespace cd { namespace journal {
// Single-transaction embedded checkpoint. CRC detects accidental corruption,
// not tampering. A record is not authorization or proof of physical recovery.
enum class Stage:uint8_t { Prepared=1, EraseIntent=2, ProgramIntent=3,
  VerifyIntent=4, Verified=5, RestartIntent=6, PostCheck=7, Completed=8,
  Aborted=9, RecoveryRequired=10 };
enum class BootDisposition { NoRecord, SafeButBlocked, RecoveryRequired, Corrupt };
struct Record {
  Stage stage=Stage::Prepared;
  uint32_t sequence=0;
  uint8_t transaction[16]{};
  uint8_t manifestDigest[32]{};
};
constexpr size_t RecordSize=64;
inline bool nonzero(const uint8_t* p,size_t n){
  for(size_t i=0;i<n;++i)if(p[i])return true;
  return false;
}
inline bool valid(const Record& r){
  const auto stage=uint8_t(r.stage);
  if(stage<1||stage>10||!nonzero(r.transaction,16)||!nonzero(r.manifestDigest,32))
    return false;
  // The NVS writer starts at Prepared(0); no valid successor skips stages.
  if(r.stage==Stage::Aborted)return r.sequence==1;
  if(r.stage==Stage::RecoveryRequired)return r.sequence>=2&&r.sequence<=7;
  return r.sequence==uint32_t(stage-1);
}
inline bool encode(const Record& r,uint8_t* out,size_t n){
  if(!out||n!=RecordSize||!valid(r))return false;
  out[0]='C';out[1]='D';out[2]='J';out[3]=1;
  out[4]=uint8_t(r.stage);out[5]=out[6]=out[7]=0;
  for(unsigned i=0;i<4;++i)out[8+i]=uint8_t(r.sequence>>(8*i));
  std::memcpy(out+12,r.transaction,16);std::memcpy(out+28,r.manifestDigest,32);
  const uint32_t c=crc32(out,60);
  for(unsigned i=0;i<4;++i)out[60+i]=uint8_t(c>>(8*i));
  return true;
}
inline bool decode(const uint8_t* in,size_t n,Record& out){
  out=Record{};
  if(!in||n!=RecordSize||in[0]!='C'||in[1]!='D'||in[2]!='J'||in[3]!=1||
     in[5]||in[6]||in[7]||crc32(in,60)!=le32(in+60))return false;
  Record r;
  r.stage=static_cast<Stage>(in[4]);r.sequence=le32(in+8);
  std::memcpy(r.transaction,in+12,16);std::memcpy(r.manifestDigest,in+28,32);
  if(!valid(r))return false;
  out=r;return true;
}
inline bool successor(const Record& old,const Record& next){
  if(!valid(old)||!valid(next)||old.sequence==0xffffffffu||
      next.sequence!=old.sequence+1||
      std::memcmp(old.transaction,next.transaction,16)||
      std::memcmp(old.manifestDigest,next.manifestDigest,32))return false;
  const bool critical=uint8_t(old.stage)>=2&&uint8_t(old.stage)<=7;
  if(old.stage==Stage::Prepared && next.stage==Stage::Aborted)return true;
  if(critical&&next.stage==Stage::RecoveryRequired)return true;
  return uint8_t(old.stage)>=1&&uint8_t(old.stage)<=7&&
      uint8_t(next.stage)==uint8_t(old.stage)+1;
}
inline BootDisposition classify(const Record& record){
  if(!valid(record))return BootDisposition::Corrupt;
  if(record.stage==Stage::RecoveryRequired||
     (uint8_t(record.stage)>=2&&uint8_t(record.stage)<=7))
    return BootDisposition::RecoveryRequired;
  return BootDisposition::SafeButBlocked;
}
} }
