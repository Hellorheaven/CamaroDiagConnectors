#pragma once
#include <cstddef>
#include <cstdint>

// Reference fixed-size SPI packet for isolated interprocessor diagnostics.
// No authentication or physical permission. CRC only detects corruption.
// A response is fetched in a separate transaction after the request.
namespace cd { namespace link {
static constexpr size_t Size=16;
enum class Kind:uint8_t { Request=1, Response=2 };
enum class Op:uint8_t { Ping=1, Status=2 };
struct Packet {
  Kind kind=Kind::Request;
  Op op=Op::Ping;
  uint16_t seq=0;
};
inline uint32_t crc(const uint8_t* p,size_t n) {
  uint32_t value=0xffffffffu;
  for(size_t i=0;i<n;++i){
    value^=p[i];
    for(unsigned j=0;j<8;++j)
      value=(value>>1)^((value&1u)?0xedb88320u:0u);
  }
  return value^0xffffffffu;
}
inline bool valid(const Packet& p) {
  return (p.kind==Kind::Request||p.kind==Kind::Response) &&
         (p.op==Op::Ping||p.op==Op::Status);
}
inline bool encode(const Packet& p,uint8_t* out,size_t n) {
  if(!out||n!=Size||!valid(p))return false;
  out[0]='C';out[1]='I';out[2]=1;out[3]=uint8_t(p.kind);
  out[4]=uint8_t(p.op);out[5]=0;
  out[6]=uint8_t(p.seq);out[7]=uint8_t(p.seq>>8);
  // status/capabilities reserved and zero: no power, CAN TX or flash.
  for(size_t i=8;i<12;++i)out[i]=0;
  const auto c=crc(out,12);
  for(unsigned i=0;i<4;++i)out[12+i]=uint8_t(c>>(8*i));
  return true;
}
inline bool decode(const uint8_t* in,size_t n,Packet& result) {
  result=Packet{};
  if(!in||n!=Size||in[0]!='C'||in[1]!='I'||in[2]!=1||in[5]!=0)return false;
  for(size_t i=8;i<12;++i)if(in[i])return false;
  const auto c=crc(in,12);
  for(unsigned i=0;i<4;++i)if(in[12+i]!=uint8_t(c>>(8*i)))return false;
  Packet p;
  p.kind=static_cast<Kind>(in[3]);p.op=static_cast<Op>(in[4]);
  p.seq=uint16_t(in[6])|(uint16_t(in[7])<<8);
  if(!valid(p))return false;
  result=p;return true;
}
class DiagnosticSlave {
 public:
  bool transact(const uint8_t* request,size_t n,uint8_t* response,size_t m){
    Packet p;
    if(closed_||!decode(request,n,p)||p.kind!=Kind::Request||p.seq!=next_){
      closed_=true;return false;
    }
    p.kind=Kind::Response;
    if(!encode(p,response,m)){closed_=true;return false;}
    if(next_==0xffffu)closed_=true;else ++next_;
    return true;
  }
  bool closed()const{return closed_;}
 private:
  uint16_t next_=0;
  bool closed_=false;
};
inline bool correlate(const Packet& request,const Packet& reply){
  return valid(request)&&valid(reply)&&request.kind==Kind::Request&&
         reply.kind==Kind::Response&&request.op==reply.op&&request.seq==reply.seq;
}
} }
