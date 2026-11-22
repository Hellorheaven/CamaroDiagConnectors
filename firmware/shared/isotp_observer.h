#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>

namespace cd {
// Passive ISO-TP, normal addressing. Explicit Classic CAN or CAN FD channel.
// 12-bit FF lengths only; maximum payload 4095. No flow-control transmission,
// extended address byte, functional routing, padding policy or ECU access.
class IsoTpObserver {
 public:
  enum class Result { Ignored, Pending, Complete, Fault };
  IsoTpObserver(uint32_t identifier,bool extended,bool fd=false):id_(identifier),ext_(extended),
      valid_(extended?identifier<=0x1fffffffu:identifier<=0x7ffu),fd_(fd){}
  static bool validDataLength(size_t length,bool fd){
    if(length>=1&&length<=8)return true;
    return fd&&(length==12||length==16||length==20||length==24||
                length==32||length==48||length==64);
  }
  // Legacy callers describe Classic CAN only. FD must be explicitly supplied.
  Result feed(uint32_t id,bool extended,const uint8_t* data,size_t dlc,uint32_t now,bool fd=false){
    if(!valid_||fault_)return Result::Fault;
    if(id!=id_||extended!=ext_||fd!=fd_)return poll(now)==Result::Fault?Result::Fault:Result::Ignored;
    if(poll(now)==Result::Fault)return Result::Fault;
    if(!data||!validDataLength(dlc,fd_)||complete_)return fail();
    const uint8_t type=data[0]>>4;
    if(type==0){
      size_t header=1,n=data[0]&15;
      if(dlc>8){
        if(n!=0)return fail();
        header=2;n=data[1];
      }
      if(active_||n<1||n>dlc-header)return fail();
      std::memcpy(buffer_,data+header,n);used_=total_=n;complete_=true;
      return Result::Complete;
    }
    if(type==1){
      if(active_||dlc<8)return fail();
      total_=size_t(data[0]&15)*256u+data[1];
      const size_t singleCapacity=dlc-(dlc>8?2u:1u);
      if(total_<=singleCapacity||total_>sizeof(buffer_))return fail();
      ll_=dlc;used_=dlc-2;std::memcpy(buffer_,data+2,used_);
      active_=true;next_=1;last_=now;return Result::Pending;
    }
    if(type==2){
      if(!active_||dlc<2||dlc>ll_||(data[0]&15)!=next_)return fail();
      const size_t remaining=total_-used_;
      if(dlc<ll_&&remaining>dlc-1)return fail();
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
    complete_=false;used_=total_=ll_=0;return true;
  }
 private:
  Result fail(){fault_=true;active_=false;complete_=false;used_=total_=ll_=0;return Result::Fault;}
  uint32_t id_,last_=0;
  bool ext_,valid_,fd_,active_=false,complete_=false,fault_=false;
  uint8_t next_=0,buffer_[4095]{};
  size_t used_=0,total_=0,ll_=0;
};
}
