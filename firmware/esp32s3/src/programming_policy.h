#pragma once
#include <cstdint>

// Offline policy model only. No actuator, memory access or physical permission.
// The physical implementation must supply independently verified evidence.
namespace cd {
enum class Route : uint8_t { Unknown, Obd, Can, Bench, Boot, Bam, Bdm, Jtag, Nexus, Swd, Isp, ChipOff };
struct Preconditions {
  Route route = Route::Unknown;
  bool authenticated = false;
  bool exclusive = false;
  bool exactProfile = false;
  bool electricalStable = false;
  bool imageVerified = false;
  bool backupVerified = false;
  bool recoveryQualified = false;
  bool planVerified = false;
  bool dataStaged = false;
  bool journalReady = false;
  bool physicalRouteQualified = false;
};
enum class Block : uint8_t { None, Route, Authentication, Exclusive, Profile, Electrical, Image, Backup, Recovery, Plan, Staging, Journal, Qualification };
inline Block preflight(const Preconditions& p) {
  switch (p.route) {
    case Route::Obd: case Route::Can: case Route::Bench: case Route::Boot:
    case Route::Bam: case Route::Bdm: case Route::Jtag: case Route::Nexus:
    case Route::Swd: case Route::Isp: case Route::ChipOff: break;
    default: return Block::Route;
  }
  if (!p.authenticated) return Block::Authentication;
  if (!p.exclusive) return Block::Exclusive;
  if (!p.exactProfile) return Block::Profile;
  if (!p.electricalStable) return Block::Electrical;
  if (!p.imageVerified) return Block::Image;
  if (!p.backupVerified) return Block::Backup;
  if (!p.recoveryQualified) return Block::Recovery;
  if (!p.planVerified) return Block::Plan;
  if (!p.dataStaged) return Block::Staging;
  if (!p.journalReady) return Block::Journal;
  if (!p.physicalRouteQualified) return Block::Qualification;
  return Block::None;
}
enum class Phase : uint8_t { Idle, Prepared, Erasing, Programming, Verifying, Completed, RecoveryRequired };
enum class Event : uint8_t { Prepare, BeginErase, Erased, Programmed, Verified, Fault };
// Pure state model: every fault in critical phases requires recovery,
// never emits a reset, power-off or hardware write. No automatic retry.
inline Phase transition(Phase current, Event event, const Preconditions& p) {
  if (current == Phase::RecoveryRequired || current == Phase::Completed) return current;
  if (event == Event::Fault)
    return (current == Phase::Idle || current == Phase::Prepared) ? Phase::Idle : Phase::RecoveryRequired;
  if (preflight(p) != Block::None)
    return (current == Phase::Idle || current == Phase::Prepared) ? Phase::Idle : Phase::RecoveryRequired;
  switch (current) {
    case Phase::Idle: if (event == Event::Prepare) return Phase::Prepared; break;
    case Phase::Prepared: if (event == Event::BeginErase) return Phase::Erasing; break;
    case Phase::Erasing: if (event == Event::Erased) return Phase::Programming; break;
    case Phase::Programming: if (event == Event::Programmed) return Phase::Verifying; break;
    case Phase::Verifying: if (event == Event::Verified) return Phase::Completed; break;
    default: break;
  }
  return current == Phase::Idle || current == Phase::Prepared ? Phase::Idle : Phase::RecoveryRequired;
}
}  // namespace cd
