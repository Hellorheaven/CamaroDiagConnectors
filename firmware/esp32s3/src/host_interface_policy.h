#pragma once
#include <cstdint>

namespace cd {
// Planning/simulation only. Never wired to an output, radio or ECU.
// A future single hardware owner must independently verify all evidence.
enum class HostInterface : uint8_t { None, NativeUsb, NativeWireless, PcBridge, J2534, KklFtdi, BluetoothAt };
enum class HostOperation : uint8_t { Discovery, DiagnosticRead, Maintenance, RawBus, ImageRead, Program };
enum class InterfaceBlock : uint8_t { None, Unknown, Busy, Recovery, Unqualified, Authorization, Profile, Electrical, LegacyUnsafe, NativeRequired };
struct InterfaceEvidence {
  bool qualified = false;
  bool localConsent = false;
  bool authenticated = false;
  bool exactProfile = false;
  bool electricalStable = false;
  bool recoveryPending = false;
  bool diagnosticAllowlistEnforced = false;
};
inline bool legacyInterface(HostInterface mode) {
  return mode==HostInterface::KklFtdi || mode==HostInterface::BluetoothAt;
}
inline bool validMode(HostInterface mode){
  switch(mode){
    case HostInterface::NativeUsb: case HostInterface::NativeWireless: case HostInterface::PcBridge:
    case HostInterface::J2534: case HostInterface::KklFtdi: case HostInterface::BluetoothAt:return true;
    default:return false;
  }
}
// No raw pass-through grants authority to write. A future programming transaction
// must follow the separate target-qualified programming_policy and durable journal.
inline InterfaceBlock interfaceAdmission(HostInterface requested, HostOperation operation,
    bool sessionOccupied, const InterfaceEvidence& e) {
  if(!validMode(requested) || uint8_t(operation)>uint8_t(HostOperation::Program))
    return InterfaceBlock::Unknown;
  if(sessionOccupied)return InterfaceBlock::Busy;
  if(operation==HostOperation::Discovery)
    return requested==HostInterface::NativeUsb?InterfaceBlock::None:InterfaceBlock::Unqualified;
  if(e.recoveryPending)return InterfaceBlock::Recovery;
  if(!e.qualified)return InterfaceBlock::Unqualified;
  if(!e.localConsent || (!legacyInterface(requested)&&!e.authenticated))
    return InterfaceBlock::Authorization;
  if(!e.exactProfile)return InterfaceBlock::Profile;
  if(!e.electricalStable)return InterfaceBlock::Electrical;
  if(legacyInterface(requested)){
    // Legacy FTDI/AT clients do not speak the authenticated native protocol.
    // Only verified allowlisted reads can ever be considered by this model.
    if(operation!=HostOperation::DiagnosticRead || !e.diagnosticAllowlistEnforced)
      return InterfaceBlock::LegacyUnsafe;
    return InterfaceBlock::None;
  }
  if(operation!=HostOperation::DiagnosticRead || !e.diagnosticAllowlistEnforced)
    return InterfaceBlock::NativeRequired;
  return InterfaceBlock::None;
}
}
