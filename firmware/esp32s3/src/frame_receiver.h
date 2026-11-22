#pragma once
#include "binary_frame.h"

// Bounded single-frame stream receiver. No transport/authentication or
// command dispatcher. After any framing error the caller must reset the
// transport session; no scanning for embedded magic or replay of suffixes.
namespace cd {
class FrameReceiver {
 public:
  enum class Result : uint8_t { Pending, Ready, Fault };
  Result feed(uint8_t byte, uint32_t now) {
    if (fault_ || ready_) return fail();
    if (used_ != 0 && uint32_t(now - first_) >= 2000u) return fail();
    if (used_ == 0) first_ = now;
    if (used_ >= sizeof(buffer_)) return fail();
    buffer_[used_++] = byte;
    if ((used_ == 1 && byte != 'C') ||
        (used_ == 2 && byte != 'D') ||
        (used_ == 3 && byte != 1) ||
        (used_ == 4 && (byte < 1 || byte > 3))) return fail();
    if (used_ == 8) {
      const uint16_t len = le16(buffer_ + 6);
      if (len > 4096) return fail();
      expected_ = size_t(len) + 12;
    }
    if (expected_ && used_ == expected_) {
      if (decode(buffer_, used_, view_) != FrameError::None) return fail();
      ready_ = true; return Result::Ready;
    }
    return Result::Pending;
  }
  Result poll(uint32_t now) {
    if (fault_) return Result::Fault;
    if (ready_) return Result::Ready;
    if (used_ && uint32_t(now - first_) >= 2000u) return fail();
    return Result::Pending;
  }
  const FrameView* frame() const { return ready_ && !fault_ ? &view_ : nullptr; }
  // Call after consuming a complete frame; never clears a fault.
  bool consume() {
    if (!ready_ || fault_) return false;
    clear(); return true;
  }
  // Only transport owner may invoke after closing/re-establishing session.
  void resetSession() { clear(); fault_ = false; }
 private:
  Result fail() { fault_ = true; ready_ = false; view_ = FrameView{}; return Result::Fault; }
  void clear() { used_ = 0; expected_ = 0; first_ = 0; ready_ = false; view_ = FrameView{}; }
  uint8_t buffer_[4108]{};
  size_t used_ = 0, expected_ = 0;
  uint32_t first_ = 0;
  bool fault_ = false, ready_ = false;
  FrameView view_{};
};
}
