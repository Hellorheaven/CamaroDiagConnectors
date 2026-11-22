#include "../src/host_interface_policy.h"
#include <cassert>
#include <initializer_list>
using namespace cd;
int main(){
  InterfaceEvidence e;
  assert(interfaceAdmission(HostInterface::NativeUsb,HostOperation::Discovery,false,e)==InterfaceBlock::None);
  assert(interfaceAdmission(HostInterface::KklFtdi,HostOperation::Discovery,false,e)==InterfaceBlock::Unqualified);
  for(auto mode:{HostInterface::KklFtdi,HostInterface::BluetoothAt,HostInterface::J2534,HostInterface::PcBridge,HostInterface::NativeWireless,HostInterface::NativeUsb}){
    assert(interfaceAdmission(mode,HostOperation::DiagnosticRead,true,e)==InterfaceBlock::Busy);
    assert(interfaceAdmission(mode,HostOperation::DiagnosticRead,false,e)==InterfaceBlock::Unqualified);
  }
  e.qualified=true;e.localConsent=true;e.authenticated=true;e.exactProfile=true;e.electricalStable=true;
  for(auto mode:{HostInterface::KklFtdi,HostInterface::BluetoothAt}){
    assert(interfaceAdmission(mode,HostOperation::DiagnosticRead,false,e)==InterfaceBlock::LegacyUnsafe);
    e.diagnosticAllowlistEnforced=true;
    assert(interfaceAdmission(mode,HostOperation::DiagnosticRead,false,e)==InterfaceBlock::None);
    for(auto op:{HostOperation::Maintenance,HostOperation::RawBus,HostOperation::ImageRead,HostOperation::Program})
      assert(interfaceAdmission(mode,op,false,e)==InterfaceBlock::LegacyUnsafe);
    e.diagnosticAllowlistEnforced=false;
  }
  e.diagnosticAllowlistEnforced=true;
  e.authenticated=false;
  assert(interfaceAdmission(HostInterface::J2534,HostOperation::DiagnosticRead,false,e)==InterfaceBlock::Authorization);
  e.localConsent=false;
  assert(interfaceAdmission(HostInterface::KklFtdi,HostOperation::DiagnosticRead,false,e)==InterfaceBlock::Authorization);
  e.localConsent=true;e.authenticated=true;e.recoveryPending=true;
  for(auto mode:{HostInterface::KklFtdi,HostInterface::NativeUsb,HostInterface::PcBridge})
    assert(interfaceAdmission(mode,HostOperation::DiagnosticRead,false,e)==InterfaceBlock::Recovery);
  e.recoveryPending=false;
  assert(interfaceAdmission(HostInterface::NativeUsb,HostOperation::Program,false,e)==InterfaceBlock::NativeRequired);
  assert(interfaceAdmission(HostInterface::None,HostOperation::Discovery,false,e)==InterfaceBlock::Unknown);
  assert(interfaceAdmission(HostInterface::NativeUsb,static_cast<HostOperation>(255),false,e)==InterfaceBlock::Unknown);
}
