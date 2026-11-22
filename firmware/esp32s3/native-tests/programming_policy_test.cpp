#include "../src/programming_policy.h"
#include <cassert>
#include <initializer_list>

using namespace cd;
int main() {
  Preconditions p;
  assert(preflight(p) == Block::Route);
  p.route = Route::Bench;
  assert(preflight(p) == Block::Authentication);
  p.authenticated = true; assert(preflight(p) == Block::Exclusive);
  p.exclusive = true; assert(preflight(p) == Block::Profile);
  p.exactProfile = true; assert(preflight(p) == Block::Electrical);
  p.electricalStable = true; assert(preflight(p) == Block::Image);
  p.imageVerified = true; assert(preflight(p) == Block::Backup);
  p.backupVerified = true; assert(preflight(p) == Block::Recovery);
  p.recoveryQualified = true; assert(preflight(p) == Block::Plan);
  p.planVerified = true; assert(preflight(p) == Block::Staging);
  p.dataStaged = true; assert(preflight(p) == Block::Journal);
  p.journalReady = true; assert(preflight(p) == Block::Qualification);
  p.physicalRouteQualified = true;
  assert(preflight(p) == Block::None);
  assert(transition(Phase::Idle, Event::Prepare, p) == Phase::Prepared);
  assert(transition(Phase::Prepared, Event::BeginErase, p) == Phase::Erasing);
  assert(transition(Phase::Erasing, Event::Erased, p) == Phase::Programming);
  assert(transition(Phase::Programming, Event::Programmed, p) == Phase::Verifying);
  assert(transition(Phase::Verifying, Event::Verified, p) == Phase::Completed);
  for (Phase phase : {Phase::Erasing, Phase::Programming, Phase::Verifying}) {
    assert(transition(phase, Event::Fault, p) == Phase::RecoveryRequired);
    assert(transition(phase, Event::BeginErase, p) == Phase::RecoveryRequired);
  }
  assert(transition(Phase::RecoveryRequired, Event::Prepare, p) == Phase::RecoveryRequired);
  assert(transition(Phase::Prepared, Event::Fault, p) == Phase::Idle);
  p.electricalStable = false;
  assert(transition(Phase::Prepared, Event::BeginErase, p) == Phase::Idle);
  assert(transition(Phase::Programming, Event::Programmed, p) == Phase::RecoveryRequired);
  p.route = static_cast<Route>(255);
  assert(preflight(p) == Block::Route);
}
