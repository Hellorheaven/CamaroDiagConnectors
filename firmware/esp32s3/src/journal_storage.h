#pragma once
#include "journal_record.h"
namespace cd { namespace journal {
// ESP32 NVS prototype, single owner only. Not wired to physical programming.
// No erase/clear API. Storage corruption never authorizes a new transaction.
BootDisposition inspectCheckpoint(Record& out);
bool persistCheckpoint(const Record& next);
} }
