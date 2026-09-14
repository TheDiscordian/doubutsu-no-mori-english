/* Complete-bank FlashRAM integration; original payload RAM stays F980 bytes. */
#include "save_runtime.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
extern int af_v3_original_save_read(u8 *, u32);
extern void af_v3_original_save_clear(u8 *);
#ifdef __mips__
#define runtime ((struct AfSaveRuntime *)0x8046C000u)
#define current ((const u8 *)0x80460020u)
#define live ((u8 *)0x80126EA0u)
#define native_copy ((void (*)(const void *, void *, u32))0x800360E0u)
#define native_header ((void (*)(u8 *))0x8008EFDCu)
#define native_sum ((u32 (*)(const u8 *, u32))0x8008EE7Cu)
#define allocate ((u8 *(*)(u32))0x8009BFC0u)
#define release ((void (*)(void *))0x8009C040u)
#define erase ((int (*)(void))0x800CDC10u)
#define write_page ((int (*)(const u8 *, u32))0x800CDC30u)
#else
extern struct AfSaveRuntime af_save_runtime;
extern u8 af_save_current[AF_SAVE_PROFILE], af_save_live[AF_SAVE_PAYLOAD];
extern void af_save_copy(const void *, void *, u32), af_save_header(u8 *);
extern u32 af_save_sum(const u8 *, u32);
extern u8 *af_save_allocate(u32);
extern void af_save_release(void *);
extern int af_save_erase(void), af_save_write_page(const u8 *, u32);
extern void af_save_halt(int) __attribute__((noreturn));
#define runtime (&af_save_runtime)
#define current af_save_current
#define live af_save_live
#define native_copy af_save_copy
#define native_header af_save_header
#define native_sum af_save_sum
#define allocate af_save_allocate
#define release af_save_release
#define erase af_save_erase
#define write_page af_save_write_page
#endif

void af_v3_save_halt(int reason) __attribute__((noreturn));
void af_v3_save_halt(int reason) {
    runtime->error = reason;
#ifdef __mips__
    const char *message = reason == AF_SAVE_PROFILE_MISSING ?
        "V3 save needs other imports.\n\nPower off. Rebuild with the\nsame imports, or add the\nmissing ones. Keep your save." :
        reason == AF_SAVE_FORMAT ?
        "V3 save format is different.\n\nPower off and use the V3\nbuild that created this save.\nKeep your original save file." :
        "V3 save check failed.\n\nNo further save writes.\nPower off and keep a backup.\nReport this with your profile.";
    ((void (*)(void))0x800292F4u)();
    ((void (*)(void))0x80027CF8u)();
    ((void (*)(const char *, ...))0x8002A448u)(message);
    for (;;) ((void (*)(void *))0x8002DE10u)(0);
#else
    af_save_halt(reason);
#endif
}

static void require_state(void) {
    if (runtime->magic != 0xAF535633u || runtime->error) af_v3_save_halt(AF_SAVE_ARGUMENT);
    for (u32 i = 0; i < 4; ++i)
        if (runtime->guard[i] != 0xAF53C0DEu) af_v3_save_halt(AF_SAVE_ARGUMENT);
    for (u32 i = 0; i < AF_SAVE_PROFILE; ++i)
        if (runtime->working[i] != current[i]) af_v3_save_halt(AF_SAVE_PROFILE_MISSING);
}

int af_v3_save_reset(void) {
    runtime->magic = 0xAF535633u;
    runtime->error = 0;
    runtime->ready = runtime->town = 0;
    for (u32 i = 0; i < AF_SAVE_STATE; ++i)
        runtime->working[i] = i < AF_SAVE_PROFILE ? current[i] : 0;
    for (u32 i = 0; i < 4; ++i) runtime->guard[i] = 0xAF53C0DEu;
    return 1;
}

int af_v3_save_signature(const u8 *bank) {
    return bank && bank[4] == 'N' && bank[5] == 'A' && bank[6] == 'F' &&
        (bank[7] == 'J' || bank[7] == '3');
}

int af_v3_save_read(u8 *bank, u32 page) {
    require_state();
    if (!bank || (page != 0 && page != 512)) return 0;
    int result = af_v3_original_save_read(bank, page) == 1 ?
        af_v3_save_check(bank, AF_SAVE_BANK, current, 0) : AF_SAVE_CHECKSUM;
    if (result == AF_SAVE_PROFILE_MISSING || result == AF_SAVE_FORMAT) af_v3_save_halt(result);
    if (result < 0) {
        /* Some native callers ignore read failure. Preserve a recognised header
         * so they report damage, but force a nonzero native checksum as well. */
        u32 old = (u32)bank[0x12] << 8 | bank[0x13];
        u32 bad = (old - native_sum(bank, AF_SAVE_PAYLOAD) + 1) & 0xFFFFu;
        bank[0x12] = bad >> 8; bank[0x13] = bad;
        return 0;
    }
    if (result == AF_SAVE_LEGACY)
        for (u32 i = AF_SAVE_PAYLOAD; i < AF_SAVE_BANK; ++i) bank[i] = 0;
    return 1;
}

void af_v3_save_clear(u8 *bank) {
    af_v3_original_save_clear(bank);
    if (bank == live) af_v3_save_reset();
}

void af_v3_save_prepare(u8 *bank) {
    require_state();
    if (!bank || bank == live) af_v3_save_halt(AF_SAVE_ARGUMENT);
    native_header(bank);
    u32 town = (u32)bank[8] << 8 | bank[9];
    if (runtime->ready && runtime->town != town)
        for (u32 i = AF_SAVE_PROFILE; i < AF_SAVE_STATE; ++i) runtime->working[i] = 0;
    int result = af_v3_save_pack(bank, AF_SAVE_BANK, runtime->working);
    if (result != AF_SAVE_OK) af_v3_save_halt(result);
    runtime->town = town;
    runtime->ready = 1;
}

void af_v3_save_commit(const u8 *bank, u8 *destination, u32 count) {
    require_state();
    if (!bank || destination != live || count != AF_SAVE_PAYLOAD) af_v3_save_halt(AF_SAVE_ARGUMENT);
    int result = af_v3_save_check(bank, AF_SAVE_BANK, current, runtime->working);
    if (result < 0) af_v3_save_halt(result);
    native_copy(bank, destination, count);
    runtime->town = (u32)bank[8] << 8 | bank[9];
    runtime->ready = 1;
}

int af_v3_save_sync(void) {
    require_state();
    u8 *bank = allocate(AF_SAVE_BANK);
    if (!bank) return -1;
    native_copy(live, bank, AF_SAVE_PAYLOAD);
    af_v3_save_prepare(bank);
    int result = erase();
    if (result == 0) {
        for (u32 page = 0; page < 512; ++page) {
            result = write_page(bank + page * 128, page);
            for (u32 retry = 0; result == -1 && retry < 3; ++retry)
                result = write_page(bank + page * 128, page);
            if (result != 0) break;
        }
    }
    if (result == 0) native_copy(bank, live, 0x14);
    release(bank);
    return result == 0 ? 0 : -1;
}
