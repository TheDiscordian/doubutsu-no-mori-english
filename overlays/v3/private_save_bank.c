/* Shared complete-bank workspace for synchronous saving and allocated loading.
 * The enclosing installer reserves and initializes it before any caller runs. */
#include "private_save_bank.h"
#define MAGIC 0x41465042u
#define GUARD 0xAF53B0DEu
extern void af_v3_save_halt(int) __attribute__((noreturn));
#ifdef __mips__
#ifndef AF_PRIVATE_SAVE_BANK_RAM
#error Private save bank requires a checked explicit RAM reservation
#endif
#define owner ((struct AfPrivateSaveBank *)AF_PRIVATE_SAVE_BANK_RAM)
#else
extern struct AfPrivateSaveBank af_test_private_save_bank;
#define owner (&af_test_private_save_bank)
#endif

static void check(void) {
    if (owner->magic != MAGIC || owner->busy > 1u)
        af_v3_save_halt(AF_SAVE_ARGUMENT);
    for (af_save_u32 i = 0; i < 2; ++i)
        if (owner->front_guard[i] != GUARD) af_v3_save_halt(AF_SAVE_ARGUMENT);
    for (af_save_u32 i = 0; i < 4; ++i)
        if (owner->end_guard[i] != GUARD) af_v3_save_halt(AF_SAVE_ARGUMENT);
}

void af_v3_private_bank_init(void) {
    /* Startup only: profile/town resets must not release an outstanding bank. */
    owner->magic = MAGIC;
    owner->busy = 0;
    for (af_save_u32 i = 0; i < 2; ++i) owner->front_guard[i] = GUARD;
    for (af_save_u32 i = 0; i < 4; ++i) owner->end_guard[i] = GUARD;
}

af_save_u8 *af_v3_private_bank_acquire(af_save_u32 size) {
    check();
    if (size != AF_SAVE_BANK || owner->busy) return 0;
    owner->busy = 1;
    return owner->bank;
}

void af_v3_private_bank_release(void *bank) {
    check();
    if (bank != owner->bank || !owner->busy) af_v3_save_halt(AF_SAVE_ARGUMENT);
    owner->busy = 0;
}
