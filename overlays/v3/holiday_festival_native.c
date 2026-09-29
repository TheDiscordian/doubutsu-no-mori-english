/* Shared native services for the complete blossom, moon/meteor, countdown,
 * ball-toss, and harvest participant group. Donor identities are never passed
 * directly to native event, tool, effect, or text tables. */
#include "holiday_festival.h"
#include "constants.h"
extern int af_holiday_native_type(unsigned int),af_holiday_observers_clip(void);
extern int af_hp_native_event_status(int,int);
extern void af_hp_native_event_error(int,int);
extern const u32 *volatile af_hp_native_npc_clip;
extern const AFHPTools *volatile af_hp_native_tools;
extern const AFHPEffects *volatile af_hp_native_effects;
extern void af_hp_native_continuous(u32,u16,xyz_t *);
extern void af_hp_native_message(int),af_hp_native_continue(void *,int);
extern void af_he_native_free_string(void *,int,const u8 *,int);
extern int af_load_display_name(u8 *,u32,u32),af_hg_message_index(int);
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))(at))

int af_hg_seconds(void) {
    const lbRTC_time_c *t=af_he_clock();
    return (int)t->hour*3600+(int)t->min*60+t->sec;
}
int af_hg_head(NPC_ACTOR *actor,u8 priority,u8 type,ACTOR *target,xyz_t *position) {
    if(!actor || !af_hp_owned((ACTOR *)actor) || !af_hp_native_npc_clip ||
       !af_holiday_observers_clip())return 0;
    return FN(af_hp_native_npc_clip[0xFC/4],int,NPC_ACTOR *,u8,u8,ACTOR *,xyz_t *)(
        actor,priority,type,target,position);
}
int af_hg_event_status(int source,int mask) {
    if(source!=mEv_EVENT_METEOR_SHOWER || mask!=mEv_STATUS_ACTIVE)return 0;
    int native=af_holiday_native_type((u32)source);
    return native>=0 && af_hp_native_event_status(native,mask);
}
void af_hg_event_set(int source,int mask) {
    if(source!=mEv_EVENT_NEW_YEARS_EVE_COUNTDOWN || mask!=mEv_STATUS_PLAYSOUND)return;
    int native=af_holiday_native_type((u32)source);
    if(native>=0)af_hp_native_event_error(native,mask);
}
mNpc_EventNpc_c *af_hg_event_resident(u16 name) {
    /* Source constants and their consecutive-role arithmetic are remapped as
     * a group. Return the actual temporary identity, not the saved native name. */
    return (mNpc_EventNpc_c *)af_hp_event_lookup(name);
}
void af_hg_world_name(u8 *out,ACTOR *actor) {
    if(!out)return;
    for(unsigned int i=0;i<8;i++)out[i]=' ';
    if(!actor || !af_hp_owned(actor))return;
    const AFHPResident *resident=af_hp_event_lookup(actor->npc_id);
    if(resident && resident->used)af_load_display_name(out,8,resident->resident);
}
void af_hg_free_string(void *window,int slot,const u8 *text,int length) {
    if(window && text && slot>=1 && slot<=5 && length>=0 && length<=16)
        af_he_native_free_string(window,slot,text,length);
}
void af_hg_message(int source) {
    int target=af_hg_message_index(source);
    if(target>=0)af_hp_native_message(target);
}
void af_hg_continue_message(int source) {
    int target=af_hg_message_index(source);void *window=mMsg_Get_base_window_p();
    if(target>=0 && window)af_hp_native_continue(window,target);
}
static ACTOR *tool(int source,int mode,ACTOR *parent,GAME *game,int arg,void *bank) {
    const AFHPTools *tools=af_hp_native_tools;int native=-1,action=-1;
    if(source==TOOL_TUMBLER && mode==aTOL_ACTION_S_TAKEOUT) {native=38;action=3;}
    if(source==TOOL_CRACKER && mode==aTOL_ACTION_S_TAKEOUT) {native=35;action=3;}
    if(mode==aTOL_ACTION_TAKEOUT) {
        switch(source) {
            case TOOL_TAMA1:native=40;break;
            case TOOL_TAMA2:native=41;break;
            case TOOL_TAMA3:native=42;break;
            case TOOL_TAMA4:native=43;break;
        }
        action=0;
    }
    if(native<0 || !parent || !af_hp_owned(parent) || !game || arg!=-1 || bank ||
       !tools || !tools->aTOL_birth_proc)return 0;
    return tools->aTOL_birth_proc(native,action,parent,game,arg,bank);
}
const AFHPTools af_hg_tools_services={tool};
static int effect_id(int source) {
    switch(source) {
        case eEC_EFFECT_HANABI_SWITCH:return 43;
        case eEC_EFFECT_CLACKER:return 89;
        case eEC_EFFECT_TAMAIRE:return 92;
        default:return -1;
    }
}
static void effect(int source,xyz_t p,int priority,s16 angle,GAME *game,u16 owner,s16 a,s16 b) {
    int native=effect_id(source);const AFHPEffects *effects=af_hp_native_effects;
    if(native>=0 && game && effects && effects->effect_make_proc)
        effects->effect_make_proc(native,p,priority,angle,game,owner,a,b);
}
static void kill(int source,u16 owner) {
    int native=effect_id(source);const AFHPEffects *effects=af_hp_native_effects;
    if(native>=0 && effects && effects->effect_kill_proc)effects->effect_kill_proc(native,owner);
}
const AFHPEffects af_hg_effect_services={effect,kill};
void af_hg_sound(u32 actor,u32 source,xyz_t *position) {
    if(position && (source==0x2F || source==0x31 || source==0x32 || source==0x33))
        af_hp_native_continuous(actor,(u16)source,position);
}
