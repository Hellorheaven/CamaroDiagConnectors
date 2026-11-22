#pragma once
#include <cstddef>
#include <cstdint>
#include <cstring>

// Bounded ASCII discovery parser. No vehicle commands or hardware operations.
class DiscoveryParser {
 public:
  enum class Result { None, Ping, Caps, Status, Unsupported, Malformed, TooLong, Timeout };

  Result feed(uint8_t byte, uint32_t now) {
    expire(now);
    if (byte == '\n') {
      Result result = error_;
      if (result == Result::None) {
        const size_t len = count_ - (terminal_cr_ ? 1u : 0u);
        if (matches("PING", len)) result = Result::Ping;
        else if (matches("CAPS", len)) result = Result::Caps;
        else if (matches("STATUS", len)) result = Result::Status;
        else result = Result::Unsupported;
      }
      reset();
      return result;
    }
    if (error_ != Result::None) return Result::None;
    last_ = now;
    if (terminal_cr_ || (byte != '\r' && (byte < 0x20 || byte > 0x7e))) {
      error_ = Result::Malformed;
    } else if (count_ == sizeof(buffer_)) {
      error_ = Result::TooLong;
    } else {
      buffer_[count_++] = static_cast<char>(byte);
      terminal_cr_ = byte == '\r';
    }
    return Result::None;
  }

  // On timeout discard the remainder through LF, never execute a suffix.
  void expire(uint32_t now) {
    if (count_ && error_ == Result::None && uint32_t(now - last_) >= 1000u)
      error_ = Result::Timeout;
  }

 private:
  bool matches(const char* command, size_t length) const {
    return std::strlen(command) == length && std::memcmp(buffer_, command, length) == 0;
  }
  void reset() {
    count_ = 0;
    terminal_cr_ = false;
    error_ = Result::None;
  }
  char buffer_[96]{};
  size_t count_ = 0;
  uint32_t last_ = 0;
  bool terminal_cr_ = false;
  Result error_ = Result::None;
};
