#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace cd {
// Classic CAN, normal addressing only. Passive ISO-TP trace reconstruction.
// No flow control transmission; observe an exchange initiated elsewhere.
// CAN FD, extended addressing and 32-bit FF lengths are explicitly unsupported.
class IsoTpObserver {
 public:
  enum class Result { Ignored, Pending, Complete, Fault };
  IsoTpObserver(uint32_t identifier,bool extended):id_(identifier),ext_(extended),
      valid_(extended?identifier<=0x1fffffffu:identifier<=0x7ffu){}
  Result feed(uint32_t id,bool extended,const uint8_t* data,size_t dlc,uint32_t now){
    if(!valid_||fault_)return Result::Fault;
    if(id!=id_||extended!=ext_)return poll(now)==Result::Fault?Result::Fault:Result::Ignored;
    if(poll(now)==Result::Fault)return Result::Fault;
    if(!data||dlc<1||dlc>8||complete_)return fail();
    const uint8_t type=data[0]>>4;
    if(type==0){
      const size_t n=data[0]&15;
      if(active_||n<1||n>7||n+1>dlc)return fail();
      std::memcpy(buffer_,data+1,n);used_=total_=n;complete_=true;
      return Result::Complete;
    }
    if(type==1){
      if(active_||dlc!=8)return fail();
      total_=size_t(data[0]&15)*256u+data[1];
      if(total_<=7||total_>sizeof(buffer_))return fail();
      used_=6;std::memcpy(buffer_,data+2,used_);
      active_=true;next_=1;last_=now;return Result::Pending;
    }
    if(type==2){
      if(!active_||dlc<2||(data[0]&15)!=next_)return fail();
      const size_t remaining=total_-used_;
      if((remaining>7&&dlc!=8)||(remaining<=7&&dlc-1<remaining))return fail();
      const size_t n=remaining<dlc-1?remaining:dlc-1;
      std::memcpy(buffer_+used_,data+1,n);used_+=n;
      next_=uint8_t((next_+1)&15);last_=now;
      if(used_==total_){active_=false;complete_=true;return Result::Complete;}
      return Result::Pending;
    }
    return fail();
  }
  Result poll(uint32_t now){
    if(fault_||!valid_)return Result::Fault;
    // Observer timeout, not an OEM programming timing specification.
    if(active_&&uint32_t(now-last_)>=1000u)return fail();
    return complete_?Result::Complete:Result::Pending;
  }
  const uint8_t* message()const{return complete_&&!fault_?buffer_:nullptr;}
  size_t size()const{return complete_&&!fault_?used_:0;}
  bool consume(){
    if(!complete_||fault_)return false;
    complete_=false;used_=total_=0;return true;
  }
 private:
  Result fail(){fault_=true;active_=false;complete_=false;used_=total_=0;return Result::Fault;}
  uint32_t id_,last_=0;
  bool ext_,valid_,active_=false,complete_=false,fault_=false;
  uint8_t next_=0,buffer_[4095]{};
  size_t used_=0,total_=0;
};
}
