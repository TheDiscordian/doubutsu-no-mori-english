#ifndef AF_V3_PRIVATE_SAVE_BANK_H
#define AF_V3_PRIVATE_SAVE_BANK_H
#include "save_codec.h"

/* Temporary I/O memory, not persistent town state or a scene allocation. */
struct AfPrivateSaveBank {
    af_save_u32 magic, busy, front_guard[2];
    af_save_u8 bank[AF_SAVE_BANK];
    af_save_u32 end_guard[4];
};
_Static_assert(sizeof(struct AfPrivateSaveBank) == AF_SAVE_BANK + 32,
               "Private save bank includes both guard boundaries");
void af_v3_private_bank_init(void);
af_save_u8 *af_v3_private_bank_acquire(af_save_u32 size);
void af_v3_private_bank_release(void *bank);
#endif
