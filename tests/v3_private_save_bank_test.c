#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/private_save_bank.c"

struct AfPrivateSaveBank af_test_private_save_bank;
static jmp_buf halted;
void af_v3_save_halt(int reason) { longjmp(halted, -reason); }

int main(void) {
    memset(&af_test_private_save_bank, 0xA5, sizeof(af_test_private_save_bank));
    af_v3_private_bank_init();
    assert(!af_v3_private_bank_acquire(AF_SAVE_BANK - 1));
    assert(!af_v3_private_bank_acquire(AF_SAVE_BANK + 1));
    af_save_u8 *bank = af_v3_private_bank_acquire(AF_SAVE_BANK);
    assert(bank == af_test_private_save_bank.bank);
    memset(bank, 0x73, AF_SAVE_BANK);
    assert(!af_v3_private_bank_acquire(AF_SAVE_BANK));
    assert(bank[0] == 0x73 && bank[AF_SAVE_BANK - 1] == 0x73);
    af_v3_private_bank_release(bank);
    assert(af_v3_private_bank_acquire(AF_SAVE_BANK) == bank);
    assert(bank[0] == 0x73 && bank[AF_SAVE_BANK - 1] == 0x73);
    af_v3_private_bank_release(bank);

    int reason = setjmp(halted);
    if (!reason) { af_v3_private_bank_release(bank); assert(0); }
    assert(reason == -AF_SAVE_ARGUMENT);
    bank = af_v3_private_bank_acquire(AF_SAVE_BANK);
    reason = setjmp(halted);
    if (!reason) { af_v3_private_bank_release(bank + 1); assert(0); }
    assert(reason == -AF_SAVE_ARGUMENT && af_test_private_save_bank.busy);
    af_v3_private_bank_release(bank);

    af_test_private_save_bank.front_guard[0] ^= 1;
    reason = setjmp(halted);
    if (!reason) { af_v3_private_bank_acquire(AF_SAVE_BANK); assert(0); }
    assert(reason == -AF_SAVE_ARGUMENT);
    af_v3_private_bank_init();
    bank = af_v3_private_bank_acquire(AF_SAVE_BANK);
    af_test_private_save_bank.end_guard[3] ^= 1;
    reason = setjmp(halted);
    if (!reason) { af_v3_private_bank_release(bank); assert(0); }
    assert(reason == -AF_SAVE_ARGUMENT && af_test_private_save_bank.busy);
    puts("Private complete-bank ownership, reuse, and guards pass");
    return 0;
}
