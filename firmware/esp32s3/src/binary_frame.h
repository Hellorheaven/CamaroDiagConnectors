#pragma once
#include <cstddef>
#include <cstdint>

// Binary discovery frame v1, matching host/python framing.py.
// CRC protects accidental corruption, not authenticity. No physical command.
namespace cd {
enum class FrameError { None, Size, Header, Length, Crc, Opcode };
struct FrameView {
  uint8_t opcode = 0;
  uint16_t sequence = 0;
  const uint8_t* payload = nullptr;
  uint16_t length = 0;
};
inline uint16_t le16(const uint8_t* p) {
  return uint16_t(p[0]) | (uint16_t(p[1]) << 8);
}
inline uint32_t le32(const uint8_t* p) {
  return uint32_t(p[0]) | (uint32_t(p[1]) << 8) |
         (uint32_t(p[2]) << 16) | (uint32_t(p[3]) << 24);
}
inline uint32_t crc32(const uint8_t* data, size_t n) {
  uint32_t crc = 0xffffffffu;
  for (size_t i = 0; i < n; ++i) {
    crc ^= data[i];
    for (unsigned bit = 0; bit < 8; ++bit)
      crc = (crc >> 1) ^ ((crc & 1u) ? 0xedb88320u : 0u);
  }
  return crc ^ 0xffffffffu;
}
inline FrameError decode(const uint8_t* data, size_t size, FrameView& result) {
  result = FrameView{};
  if (!data || size < 12 || size > 4108) return FrameError::Size;
  if (data[0] != 'C' || data[1] != 'D' || data[2] != 1) return FrameError::Header;
  const uint16_t len = le16(data + 6);
  if (len > 4096 || size != size_t(len) + 12) return FrameError::Length;
  if (crc32(data, size - 4) != le32(data + size - 4)) return FrameError::Crc;
  if (data[3] < 1 || data[3] > 3) return FrameError::Opcode;
  result.opcode = data[3];
  result.sequence = le16(data + 4);
  result.payload = data + 8;
  result.length = len;
  return FrameError::None;
}
}  // namespace cd
