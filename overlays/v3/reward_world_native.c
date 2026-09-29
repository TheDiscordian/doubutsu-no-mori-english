/* Gift actors use actual native world observations and narrow NPC services.
 * The installer binds these providers only after admitting the complete family.
 * Donor-only scene state, masks, and Shrine ownership are separate dependencies.
 */
#include "reward_event.h"
#include "constants.h"
extern const s16 af_rw_native_weather;
extern const volatile u8 af_rw_native_cheated;
extern const u32 *volatile af_hp_native_npc_clip;
extern const AFHPTools *volatile af_hp_native_tools;
extern int af_holiday_observers_clip(void);
extern int af_hp_native_player_state(GAME *);
extern void af_rw_native_wait(GAME *);
extern int af_v3_reward_event(void *,int);
extern int af_hp_native_resident_index(u16),af_hp_native_resident_valid(int,u16);
extern u8 af_hp_native_animals[15][0x528];
extern void af_rw_effect_request(int,xyz_t,int,s16,void *,u16,s16,s16);
extern void af_rw_effect_kill(int,u16);

mDemo_Clip_c *af_rw_demo_clip;
int af_rw_calendar_clean(void) {return af_rw_native_cheated==0;}
int af_rw_block_x(GAME_PLAY *g) {return g?((const s8 *)g)[0xE4]:-1;}
int af_rw_block_z(GAME_PLAY *g) {return g?((const s8 *)g)[0xE5]:-1;}
u8 *af_rw_menu_refuse(GAME_PLAY *g) {return g?(u8 *)g+0x1D9E:0;}
int af_rw_weather(void) {
    return af_rw_native_weather>=0 && af_rw_native_weather<5?af_rw_native_weather:-1;
}
u8 *af_rw_sub_animation(NPC_ACTOR *a) {
    /* Native 80975BDC writes the umbrella sub-animation BYTE at 729. The
     * word at 708 is a texture-bank index and must never be overwritten. */
    return a && af_hp_owned((ACTOR *)a)?(u8 *)a+0x729:0;
}
u16 af_rw_umbrella(NPC_ACTOR *a) {
    /* The native constructor copies the ordinary umbrella kind to 85F;
     * native 80975B40 reads that same byte for the tool request. */
    return a && af_hp_owned((ACTOR *)a) && ((u8 *)a)[0x85F]<32?((u8 *)a)[0x85F]:0xFFFF;
}
int af_rw_is_resident(NPC_ACTOR *a) {
    if(!a || !af_hp_owned((ACTOR *)a))return 0;
    const AFHPResident *r=af_hp_event_lookup(a->actor_class.npc_id);
    if(!r || !r->used)return 0;
    int index=af_hp_native_resident_index(r->resident);
    if(!af_hp_native_resident_valid(index,r->resident))return 0;
    return *(const u32 *)((const u8 *)a+0x174)==
        (u32)(__UINTPTR_TYPE__)af_hp_native_animals[index];
}
void af_rw_npc_save(ACTOR *a,GAME *g) {
    if(a && g && af_hp_admit(a,g) && af_hp_native_npc_clip &&
       af_holiday_observers_clip() && af_hp_native_npc_clip[0xC8/4])
        ((void (*)(ACTOR *,GAME *))(__UINTPTR_TYPE__)af_hp_native_npc_clip[0xC8/4])(a,g);
}
const AFHPNpcServices *af_rw_npc_services(void) {
    return af_hp_native_npc_clip && af_holiday_observers_clip()?&af_hp_npc_services:0;
}
static ACTOR *umbrella(int kind,int mode,ACTOR *a,GAME *g,int arg,void *bank) {
    const AFHPTools *tools=af_hp_native_tools;
    if(kind<0 || kind>=32 || mode!=aTOL_ACTION_S_TAKEOUT || !a || !g || arg!=-1 || bank ||
       !af_hp_admit(a,g) || !tools || !tools->aTOL_birth_proc)return 0;
    /* The stored 85F value is already a native ordinary umbrella kind.
     * Only the source special-takeout action needs translation (4 -> 3). */
    return tools->aTOL_birth_proc(kind,3,a,g,arg,bank);
}
const AFHPTools af_rw_tools={umbrella};
static int effect_id(int source) {
    switch(source) {
        case eEC_EFFECT_MAKE_HEM:return 122;
        case eEC_EFFECT_MAKE_HEM_KIRA:return 123;
        case eEC_EFFECT_MAKE_HEM_LIGHT:return 124;
        default:return -1;
    }
}
static void effect(int source,xyz_t p,int priority,s16 angle,GAME *g,u16 item,s16 a,s16 b) {
    int native=effect_id(source);
    if(native>=0)af_rw_effect_request(native,p,priority,angle,g,item,a,b);
}
static void kill(int source,u16 item) {
    int native=effect_id(source);if(native>=0)af_rw_effect_kill(native,item);
}
const AFHPEffects af_rw_effects={effect,kill};
int mPlib_check_player_actor_main_index_OutDoorMove2(GAME *g) {
    if(!g || !af_cw_player_actor(g))return 1;
    /* Native Takeout is 71 (808D4EE8 takes the requested tool); 72 is Putin
     * (808D5434 reads the submenu tool). GC additionally has CompletePayment,
     * which the N64 does not have. Its unused extended action must not alias
     * native action 104 or an unrelated source table label. */
    switch(af_hp_native_player_state(g)) {
        case 0:case 1:case 5:case 17:case 71:return 1;
        default:return 0;
    }
}
void mPlib_request_main_wait_type3(GAME *g) {
    if(g && af_cw_player_actor(g))af_rw_native_wait(g);
}
int mPlib_request_main_demo_get_golden_item2_type1(GAME *g,int type) {
    return g && af_cw_player_actor(g) && type>=0 && type<4?af_v3_reward_event(g,type):0;
}
int mPr_GetPossessionItemIdx(void *p,u16 item) {
    if(!p || p!=af_rw_private())return -1;
    const u8 *items=(const u8 *)p+0x14;
    for(unsigned i=0;i<15;i++)if((u16)((u32)items[i*2]*256+items[i*2+1])==item)return (int)i;
    return -1;
}
