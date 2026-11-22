#include "../src/host_session_arbiter.h"
#include <cassert>
using namespace cd;
int main(){
  HostSessionArbiter a;
  HostSessionArbiter::Lease one,two,denied;
  InterfaceEvidence e;
  assert(!a.acquire(HostInterface::NativeUsb,e,one));
  e.qualified=true;e.localConsent=true;e.authenticated=true;
  e.exactProfile=true;e.electricalStable=true;e.diagnosticAllowlistEnforced=true;
  assert(a.acquire(HostInterface::NativeUsb,e,one));
  assert(a.allowsRead(one,e));
  assert(!a.acquire(HostInterface::PcBridge,e,denied)&&!denied.generation);
  assert(!a.acquire(HostInterface::KklFtdi,e,denied));
  assert(a.release(one));
  assert(a.acquire(HostInterface::PcBridge,e,two));
  assert(two.generation!=one.generation);
  assert(!a.owns(one)&&!a.release(one)&&!a.allowsRead(one,e));
  assert(a.owns(two)&&a.allowsRead(two,e));
  e.electricalStable=false;assert(!a.allowsRead(two,e));
  e.electricalStable=true;e.authenticated=false;assert(!a.allowsRead(two,e));
  e.authenticated=true;e.recoveryPending=true;assert(!a.allowsRead(two,e));
  a.latchRecovery();e.recoveryPending=false;
  assert(a.recoveryRequired()&&!a.owns(two)&&!a.release(two));
  assert(!a.acquire(HostInterface::NativeUsb,e,denied));
  HostSessionArbiter reopened(true);
  assert(!reopened.acquire(HostInterface::J2534,e,denied));
  HostSessionArbiter legacy;
  e.authenticated=false;
  assert(legacy.acquire(HostInterface::KklFtdi,e,one));
  assert(!legacy.acquire(HostInterface::BluetoothAt,e,denied));
  e.localConsent=false;assert(!legacy.allowsRead(one,e));
}
