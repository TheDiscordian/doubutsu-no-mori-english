/* Exercise the existing full-payload save code, not a new simulated codec. */
#define main original_save_checks
#include "v3_save_runtime_test.c"
#undef main
int main(void) {
    init();
    for (u32 home=0;home<4;home++) {
        af_save_live[0x3588+home*0xB48+0x14]=(u8)(74+home);
        af_save_live[0x3588+home*0xB48+0x15]=(u8)(77-home);
    }
    assert(af_v3_save_sync()==0);
    memcpy(original_live,af_save_live,sizeof(original_live));
    memset(af_save_live,0,sizeof(af_save_live));af_v3_save_reset();
    assert(af_v3_save_read(buffer.bank,0)==1);
    af_v3_save_commit(buffer.bank,af_save_live,AF_SAVE_PAYLOAD);
    assert(!memcmp(original_live,af_save_live,sizeof(original_live)));
    assert(erases==1 && writes==512);
    puts("complete native payload including all four full-byte surface pairs survives host save/read/commit");
}
