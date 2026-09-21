/* Reuse mock device I/O; execute the actual codec/runtime/collection code. */
#define main prior_runtime_fixture
#include "v3_save_runtime_test.c"
#undef main
#define af_surface_test_state af_save_runtime
#include "../overlays/v3/surface_save.c"
u32 af_surface_test_header[64];
u8 af_surface_test_players[4*0xBD0],*af_surface_test_active;
static unsigned prior_records,prior_owned,prior_clears;
static u32 prior_argument;
void af_v3_require_save_state(void) {require_state();}
void af_surface_prior_record(u32 item) {prior_records++;prior_argument=item;}
int af_surface_prior_owned(const u8 *p,u32 item) {(void)p;prior_owned++;prior_argument=item;return 17;}
void af_surface_prior_clear(u8 *p) {(void)p;prior_clears++;}

void surface_fixture_select(u32 selected) {
    header[0]=0x41465349;header[1]=1;header[2]=10;header[3]=24;
    struct SurfaceItem *rows=(struct SurfaceItem *)(header+4);
    for (u32 i=0;i<10;i++) {rows[i].item=(u16)(0x2649+i%5+(i/5)*256);rows[i].enabled=(selected>>i)&1;}
}

int main(void) {
    init();surface_fixture_select(1023);assert(af_v3_save_reset()==1);
    assert(sizeof(af_save_runtime)==1232 && AF_SAVE_STATE==1200);
    for (u32 i=0;i<64;i++) assert(af_v3_surface_profile_byte(i)==(i==9 || i==41 ? 62u : 0u));
    assert(!af_v3_surface_profile_byte(64));
    for (u32 player=0;player<4;player++) {
        af_surface_test_active=players+player*0xBD0;
        for (u32 kind=0;kind<2;kind++) {
            u32 item=0x2649+kind*256+player;
            assert(!af_v3_surface_owned(af_surface_test_active,item));
            af_v3_surface_record(0x12340000|item);
            assert(af_v3_surface_owned(af_surface_test_active,item)==1);
            for (u32 other=0;other<4;other++) if (other!=player)
                assert(!af_v3_surface_owned(players+other*0xBD0,item));
        }
        af_save_live[0x3588+player*0xB48+0x14]=(u8)(73+player);
        af_save_live[0x3588+player*0xB48+0x15]=(u8)(77-player);
    }
    af_v3_surface_record(0xABCD2600);assert(prior_records==1 && prior_argument==0xABCD2600);
    assert(af_v3_surface_owned(players,0x3000)==17 && prior_owned==1);
    af_v3_surface_record(0x2648);assert(prior_records==1);
    assert(!af_v3_surface_owned(players+1,0x2649));
    u8 working[AF_SAVE_STATE];memcpy(working,runtime->working,sizeof(working));
    assert(af_v3_save_sync()==0);memcpy(original_live,af_save_live,sizeof(original_live));
    memset(af_save_live,0,sizeof(af_save_live));af_v3_save_reset();
    assert(af_v3_save_read(buffer.bank,0)==1);
    af_v3_save_commit(buffer.bank,af_save_live,AF_SAVE_PAYLOAD);
    assert(!memcmp(working,runtime->working,sizeof(working)));
    assert(!memcmp(original_live,af_save_live,sizeof(original_live)));
    af_v3_surface_player_clear(players+2*0xBD0);assert(prior_clears==1);
    memset(working+880+64*3,0,64);assert(!memcmp(working,runtime->working,sizeof(working)));
    af_v3_surface_player_clear(players+1);assert(prior_clears==2);
    assert(!memcmp(working,runtime->working,sizeof(working)));
    /* New-town reset keeps the selected surface profile, not old ownership. */
    af_save_live[0x2F69]=2;memcpy(buffer.bank,af_save_live,AF_SAVE_PAYLOAD);
    af_v3_save_prepare(buffer.bank);
    for (u32 i=192;i<AF_SAVE_STATE;i++)
        assert(runtime->working[i]==(i>=880 && i<944 ? af_v3_surface_profile_byte(i-880) : 0));
    unsigned old_erases=erases,old_writes=writes;
    surface_fixture_select(1022);
    int reason=setjmp(halted);
    if (!reason) {af_v3_save_sync();assert(0);}
    assert(reason==7 && erases==old_erases && writes==old_writes);
    puts("format-4 runtime, surface ownership, player clearing, payload reload, and failure-before-I/O pass");
    return 0;
}
