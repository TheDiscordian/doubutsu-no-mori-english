#define AF_V3_CLOTHING_PROFILE 1
#define AF_V3_REWARD_PROFILE 1
#define main previous_runtime_test_main
#include "v3_save_runtime_test.c"
#undef main
#define af_reward_state af_save_runtime
#include "../overlays/v3/reward_state.c"

u8 af_reward_players[4*0xBD0],*af_reward_active=af_reward_players;
static unsigned stopped,private_clears;
static u8 *cleared_private;
static _Alignas(16) u8 actor[0x1400];
void af_v3_require_save_state(void) { require_state(); }
void af_v3_catalogue_clear(u8 *p) { ++private_clears;cleared_private=p; }
void af_v3_reward_stop_fanfare(void *p) { assert(p==actor);++stopped; }

int main(void) {
    init();
    assert(sizeof(af_save_runtime)==912 && AF_SAVE_STATE==880);
    u8 *flags=af_save_runtime.working+AF_SAVE_REWARD_OFFSET;
    u8 prefix[AF_SAVE_REWARD_OFFSET];memcpy(prefix,af_save_runtime.working,sizeof(prefix));
    assert(!af_v3_reward_data_valid(0));
    for(u32 player=0;player<4;player++) for(u32 category=0;category<2;category++)
        for(u32 index=0;index<(category?4u:33u);index++) {
            assert(af_v3_reward_flag(player,category,index,0)==0);
            assert(af_v3_reward_flag(player,category,index,1)==1);
            assert(af_v3_reward_flag(player,category,index,0)==1);
        }
    const u8 full[12]={15,255,255,255,0,0,0,31,15,0,0,0};
    for(u32 i=0;i<4;i++) assert(!memcmp(flags+12*i,full,12));
    assert(af_v3_reward_data_valid(flags));
    assert(!memcmp(prefix,af_save_runtime.working,sizeof(prefix)));
    assert(af_v3_reward_flag(4,0,0,1)==AF_SAVE_ARGUMENT);
    assert(af_v3_reward_flag(0,2,0,1)==AF_SAVE_ARGUMENT);
    assert(af_v3_reward_flag(0,0,33,1)==AF_SAVE_ARGUMENT);
    assert(af_v3_reward_flag(0,1,4,1)==AF_SAVE_ARGUMENT);
    assert(af_v3_reward_flag(0,1,0,2)==AF_SAVE_ARGUMENT);
    assert(af_v3_save_sync()==0 && writes==512);
    memcpy(saved,chip,AF_SAVE_BANK);
    assert(read32(saved+AF_SAVE_PAYLOAD+4)==0x00030680);
    af_v3_save_reset();assert(!memcmp(flags,(u8[48]){0},48));
    af_v3_save_commit(saved,af_save_live,AF_SAVE_PAYLOAD);
    for(u32 i=0;i<4;i++) assert(!memcmp(flags+12*i,full,12));
    af_v3_reward_player_clear(af_reward_players+2*0xBD0);
    assert(private_clears==1 && cleared_private==af_reward_players+2*0xBD0);
    for(u32 i=0;i<4;i++) assert(!memcmp(flags+12*i,i==2?(u8[12]){0}:full,12));
    af_reward_active=af_reward_players+2*0xBD0;
    for(int type=0;type<4;type++) {
        *(int *)(actor+0xD18)=type;af_v3_reward_settle(actor,0);
        assert(flags[2*12+8]==(1u<<(type+1))-1u);
        assert(!memcmp(flags+2*12,(u8[8]){0},8));
    }
    assert(stopped==4);
    *(int *)(actor+0xD18)=4;af_v3_reward_settle(actor,0);af_v3_reward_settle(0,0);
    assert(stopped==4);
    *(int *)(actor+0xD18)=0;af_reward_active=af_reward_players+1;
    int reason=setjmp(halted);
    if(!reason) { af_v3_reward_settle(actor,0);assert(0); }
    assert(reason==1 && stopped==4);
    af_v3_save_reset();
    flags[9]=1;unsigned erases_before=erases,writes_before=writes;
    reason=setjmp(halted);
    if(!reason) { af_v3_save_sync();assert(0); }
    assert(reason==9 && erases==erases_before && writes==writes_before);
    af_v3_save_reset();
    af_v3_save_commit(saved,af_save_live,AF_SAVE_PAYLOAD);
    af_save_live[0x2F69]=2;memcpy(buffer.bank,af_save_live,AF_SAVE_PAYLOAD);
    af_v3_save_prepare(buffer.bank);
    assert(!memcmp(flags,(u8[48]){0},48));
    flags[8]=1;af_v3_save_clear(af_save_live);
    assert(!memcmp(flags,(u8[48]){0},48));
    for(u32 i=0;i<4;i++) assert(af_save_runtime.guard[i]==0xAF53C0DE);
    puts("pass: independent reward bits, settlement, clearing, lifecycle, and failure before device writes");
}
