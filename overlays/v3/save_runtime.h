#ifndef AF_V3_SAVE_RUNTIME_H
#define AF_V3_SAVE_RUNTIME_H
#include "save_codec.h"
struct AfSaveRuntime {
    af_save_u32 magic;
    int error;
    af_save_u32 ready, town;
    af_save_u8 working[AF_SAVE_STATE];
    af_save_u32 guard[4];
};
_Static_assert(sizeof(struct AfSaveRuntime) == AF_SAVE_STATE+32, "V3 save-state layout");
_Static_assert(sizeof(struct AfSaveRuntime) <= 0x390, "V3 save-state reservation");
int af_v3_save_reset(void);
int af_v3_save_signature(const af_save_u8 *bank);
int af_v3_save_read(af_save_u8 *bank, af_save_u32 page);
void af_v3_save_clear(af_save_u8 *bank);
void af_v3_save_prepare(af_save_u8 *bank);
void af_v3_save_commit(const af_save_u8 *bank, af_save_u8 *destination, af_save_u32 count);
int af_v3_save_sync(void);
#endif
