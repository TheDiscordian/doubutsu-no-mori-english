#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/save_codec.c"
#include "../overlays/v3/save_runtime.c"

struct AfSaveRuntime af_save_runtime;
u8 af_save_current[AF_SAVE_PROFILE], af_save_live[AF_SAVE_PAYLOAD];
static u8 chip[AF_SAVE_BANK * 2], allocation[AF_SAVE_BANK];
static struct { u8 before[16], bank[AF_SAVE_BANK], after[16]; } buffer;
static u8 original_live[AF_SAVE_PAYLOAD], saved[AF_SAVE_BANK];
static int alloc_fail, erase_fail, read_fail, page_fail = -1, page_failures;
static unsigned erases, writes, releases, headers, clears;
static jmp_buf halted;

void af_save_copy(const void *src, void *dest, u32 size) { memcpy(dest, src, size); }
void af_save_header(u8 *bank) {
    ++headers;
    memcpy(bank + 4, "NAFJ", 4);
    memcpy(bank + 8, af_save_live + 0x2F68, 2);
    memset(bank + 0xA, 0x12, 8);
}
u32 af_save_sum(const u8 *bank, u32 size) { assert(size == AF_SAVE_PAYLOAD); return sum(bank); }
u8 *af_save_allocate(u32 size) { assert(size == AF_SAVE_BANK); return alloc_fail ? 0 : allocation; }
void af_save_release(void *p) { assert(p == allocation); ++releases; }
int af_save_erase(void) {
    ++erases;
    if (erase_fail) return -1;
    memset(chip, 0xFF, sizeof(chip));
    return 0;
}
int af_save_write_page(const u8 *data, u32 page) {
    assert(page < 512 && data == allocation + page * 128);
    ++writes;
    if ((int)page == page_fail && page_failures-- > 0) return -1;
    memcpy(chip + page * 128, data, 128);
    return 0;
}
int af_v3_original_save_read(u8 *bank, u32 page) {
    assert(page == 0 || page == 512);
    memcpy(bank, chip + page * 128, AF_SAVE_BANK);
    return !read_fail;
}
void af_v3_original_save_clear(u8 *bank) {
    ++clears;
    memset(bank + 4, 0xFF, 6);
    memset(bank + 0xA, 0, 10);
}
void af_save_halt(int reason) { longjmp(halted, -reason); }

static void init(void) {
    memset(&buffer, 0xA5, sizeof(buffer));
    memset(af_save_live, 0x53, sizeof(af_save_live));
    af_save_live[0x2F68] = 0x30; af_save_live[0x2F69] = 1;
    memset(af_save_current, 0, sizeof(af_save_current));
    af_save_current[29] = 0x24; af_save_current[49] = 2; af_save_current[53] = 64;
    assert(af_v3_save_reset() == 1);
    assert(af_save_runtime.magic == 0xAF535633 && af_save_runtime.guard[3] == 0xAF53C0DE);
    assert(!memcmp(af_save_runtime.working, af_save_current, AF_SAVE_PROFILE));
    for (u32 i = AF_SAVE_PROFILE; i < AF_SAVE_STATE; ++i) assert(!af_save_runtime.working[i]);
    assert(af_v3_save_collect(af_save_runtime.working, 2, 0x3227, 1) == 1);
    assert(af_v3_save_collect(af_save_runtime.working, 3, 0x32BA, 1) == 1);
}

int main(void) {
    init();
    memcpy(original_live, af_save_live, sizeof(original_live));
    memcpy(buffer.bank, af_save_live, AF_SAVE_PAYLOAD);
    af_v3_save_prepare(buffer.bank);
    assert(af_v3_save_check(buffer.bank, AF_SAVE_BANK, af_save_current, 0) == AF_SAVE_OK);
    assert(af_save_runtime.ready == 1 && af_save_runtime.town == 0x3001);
    assert(!memcmp(original_live, af_save_live, sizeof(original_live)));
    assert(!erases && !writes);
    memcpy(saved, buffer.bank, sizeof(saved));
    assert(af_v3_save_sync() == 0);
    assert(erases == 1 && writes == 512 && releases == 1);
    assert(!memcmp(chip, saved, AF_SAVE_BANK));
    for (u32 i = AF_SAVE_BANK; i < sizeof(chip); ++i) assert(chip[i] == 0xFF);
    assert(!memcmp(af_save_live, saved, 0x14));
    memcpy(original_live, af_save_live, sizeof(original_live));
    af_v3_save_reset();
    assert(af_v3_save_read(buffer.bank, 0) == 1);
    assert(!af_save_runtime.ready);
    assert(!memcmp(af_save_live, original_live, sizeof(original_live)));
    assert(!memcmp(buffer.bank, saved, AF_SAVE_BANK));
    af_v3_save_commit(buffer.bank, af_save_live, AF_SAVE_PAYLOAD);
    assert(af_save_runtime.ready && af_save_runtime.town == 0x3001);
    assert(af_v3_save_collect(af_save_runtime.working, 2, 0x3224, 0) == 1);
    assert(af_v3_save_collect(af_save_runtime.working, 3, 0x32B8, 0) == 1);
    assert(af_v3_save_signature(af_save_live) == 1 && af_v3_save_signature(0) == 0);
    af_v3_save_clear(buffer.bank);
    assert(af_save_runtime.ready && clears == 1);  /* Clearing a temp bank is not a town reset. */
    af_v3_save_clear(af_save_live);
    assert(!af_save_runtime.ready && clears == 2);
    assert(af_v3_save_collect(af_save_runtime.working, 2, 0x3224, 0) == 0);
    memcpy(af_save_live, original_live, sizeof(original_live));

    memcpy(chip, saved, AF_SAVE_BANK);
    chip[0x800] ^= 1;
    assert(af_v3_save_read(buffer.bank, 0) == 0);
    assert(af_save_sum(buffer.bank, AF_SAVE_PAYLOAD) == 1 && af_v3_save_signature(buffer.bank));
    memcpy(chip, saved, AF_SAVE_BANK);
    read_fail = 1;
    assert(af_v3_save_read(buffer.bank, 0) == 0);
    assert(af_save_sum(buffer.bank, AF_SAVE_PAYLOAD) == 1);
    read_fail = 0;
    assert(af_v3_save_read(0, 0) == 0 && af_v3_save_read(buffer.bank, 1) == 0);
    assert(!memcmp(af_save_live, original_live, sizeof(original_live)));

    memcpy(chip, saved, AF_SAVE_BANK);
    chip[7] = 'J';
    u32 balance = ((((u32)chip[0x12] << 8) | chip[0x13]) - sum(chip)) & 0xFFFF;
    chip[0x12] = balance >> 8; chip[0x13] = balance;
    memset(chip + AF_SAVE_PAYLOAD, 0xA5, AF_SAVE_CAPSULE);
    assert(af_v3_save_read(buffer.bank, 0) == 1);
    for (u32 i = AF_SAVE_PAYLOAD; i < AF_SAVE_BANK; ++i) assert(!buffer.bank[i]);
    assert(af_v3_save_signature(buffer.bank));
    af_v3_save_commit(buffer.bank, af_save_live, AF_SAVE_PAYLOAD);
    assert(af_v3_save_collect(af_save_runtime.working, 2, 0x3224, 0) == 0);

    u8 future[AF_SAVE_STATE];
    memcpy(future, af_save_runtime.working, sizeof(future));
    future[31] |= 0x80;
    memcpy(chip, saved, AF_SAVE_BANK);
    assert(af_v3_save_pack(chip, AF_SAVE_BANK, future) == 1);
    int reason = setjmp(halted);
    if (!reason) { af_v3_save_read(buffer.bank, 0); assert(0); }
    assert(reason == 7 && af_save_runtime.error == -7 && erases == 1 && writes == 512);
    af_v3_save_reset();
    memcpy(chip, saved, AF_SAVE_BANK);
    chip[AF_SAVE_PAYLOAD + 5] = 2;
    reason = setjmp(halted);
    if (!reason) { af_v3_save_read(buffer.bank, 0); assert(0); }
    assert(reason == 4 && erases == 1 && writes == 512);
    af_v3_save_reset();
    af_save_runtime.guard[0] ^= 1;
    reason = setjmp(halted);
    if (!reason) { af_v3_save_sync(); assert(0); }
    assert(reason == 1 && erases == 1 && writes == 512);
    af_v3_save_reset();
    af_save_runtime.working[AF_SAVE_PROFILE] = 1;  /* Bad ownership cannot reach erase. */
    reason = setjmp(halted);
    if (!reason) { af_v3_save_sync(); assert(0); }
    assert(reason == 8 && erases == 1 && writes == 512);
    af_v3_save_reset();
    alloc_fail = 1;
    assert(af_v3_save_sync() == -1 && erases == 1 && writes == 512);
    alloc_fail = 0; erase_fail = 1;
    assert(af_v3_save_sync() == -1 && erases == 2 && writes == 512 && releases == 2);
    erase_fail = 0; page_fail = 12; page_failures = 1;
    assert(af_v3_save_sync() == 0 && erases == 3 && writes == 1025 && releases == 3);
    page_failures = 10;
    assert(af_v3_save_sync() == -1 && erases == 4 && writes == 1041 && releases == 4);
    for (u32 i = 0; i < 16; ++i) assert(buffer.before[i] == 0xA5 && buffer.after[i] == 0xA5);
    puts("Prepare/read/commit, catalogue state, legacy migration, failure-before-I/O, retries, and guards pass");
    return 0;
}
