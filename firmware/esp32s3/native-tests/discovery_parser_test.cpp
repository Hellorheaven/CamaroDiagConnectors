#include "../src/discovery_parser.h"
#include <cassert>
#include <string>

using R = DiscoveryParser::Result;

static R line(DiscoveryParser& parser, const std::string& value, uint32_t now = 0) {
  R result = R::None;
  for (unsigned char byte : value) result = parser.feed(byte, now);
  return result;
}

int main() {
  DiscoveryParser parser;
  assert(line(parser, "PING\n") == R::Ping);
  assert(line(parser, "CAPS\r\n") == R::Caps);
  assert(line(parser, "STATUS\n") == R::Status);
  assert(line(parser, "FLASH\n") == R::Unsupported);
  assert(line(parser, "PING extra\n") == R::Unsupported);
  assert(line(parser, "\n") == R::Unsupported);
  assert(line(parser, std::string("PING\0FLASH\n", 11)) == R::Malformed);
  assert(line(parser, "PI\rNG\n") == R::Malformed);
  assert(line(parser, "PING\r\r\n") == R::Malformed);
  assert(line(parser, "\tPING\n") == R::Malformed);
  assert(line(parser, std::string(1, char(0xff)) + "\n") == R::Malformed);
  assert(line(parser, std::string(96, 'X') + "\n") == R::Unsupported);
  assert(line(parser, std::string(97, 'X') + "PING\n") == R::TooLong);
  assert(line(parser, "PING\n") == R::Ping);
  assert(line(parser, "PI", 10) == R::None);
  assert(line(parser, "NG\n", 1010) == R::Timeout);
  assert(line(parser, "PING\n", 1011) == R::Ping);
  assert(line(parser, "PI", 0xffffff00u) == R::None);
  assert(line(parser, "NG\n", 0x00000300u) == R::Timeout);
  assert(line(parser, "CAPS\n", 0x00000301u) == R::Caps);
  assert(line(parser, "STA", 1000) == R::None);
  assert(line(parser, "TUS\n", 1999) == R::Status);
}
