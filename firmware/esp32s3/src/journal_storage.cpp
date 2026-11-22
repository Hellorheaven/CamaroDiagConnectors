#include "journal_storage.h"
#include "journal_writer_gate.h"
#include <nvs.h>

namespace cd { namespace journal {
namespace {
enum class Read { Missing, Valid, Error };
// Single-owner prototype: uncertain persistence poisons this boot's writer.
WriterGate writer;
Read readRecord(nvs_handle_t handle,Record& result){
  uint8_t bytes[RecordSize]{};
  size_t count=sizeof(bytes);
  const esp_err_t e=nvs_get_blob(handle,"checkpoint",bytes,&count);
  if(e==ESP_ERR_NVS_NOT_FOUND)return Read::Missing;
  return e==ESP_OK&&decode(bytes,count,result)?Read::Valid:Read::Error;
}
}
BootDisposition inspectCheckpoint(Record& out){
  out=Record{};
  if(writer.locked())return BootDisposition::Corrupt;
  nvs_handle_t handle;
  const esp_err_t e=nvs_open("cd-journal",NVS_READONLY,&handle);
  if(e==ESP_ERR_NVS_NOT_FOUND)return BootDisposition::NoRecord;
  if(e!=ESP_OK){writer.uncertain();return BootDisposition::Corrupt;}
  const Read status=readRecord(handle,out);
  nvs_close(handle);
  if(status==Read::Missing)return BootDisposition::NoRecord;
  if(status==Read::Error)writer.uncertain();
  return status==Read::Valid?classify(out):BootDisposition::Corrupt;
}
bool persistCheckpoint(const Record& next){
  uint8_t bytes[RecordSize]{},check[RecordSize]{};
  if(writer.locked())return false;
  if(!encode(next,bytes,sizeof(bytes)))return false;
  nvs_handle_t handle;
  if(nvs_open("cd-journal",NVS_READWRITE,&handle)!=ESP_OK){writer.uncertain();return false;}
  Record previous;
  const Read state=readRecord(handle,previous);
  const StoredState stored=state==Read::Missing?StoredState::Missing:
      state==Read::Valid?StoredState::Valid:StoredState::Error;
  const bool allowed=writer.permits(stored,previous,next);
  bool ok=false;
  if(allowed&&nvs_set_blob(handle,"checkpoint",bytes,sizeof(bytes))==ESP_OK&&
     nvs_commit(handle)==ESP_OK){
    size_t length=sizeof(check);
    ok=nvs_get_blob(handle,"checkpoint",check,&length)==ESP_OK&&
       length==sizeof(check)&&std::memcmp(bytes,check,sizeof(bytes))==0;
  }
  if(allowed){
    if(ok)writer.durable(next);else writer.uncertain();
  }
  nvs_close(handle);
  // A failed write/verify is an uncertain commit; caller must lock out.
  // No retries or target reset are issued here.
  return ok;
}
} }
