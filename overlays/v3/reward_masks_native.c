/* Real native resident masks and separately registered special artwork.
 * The source gift role never aliases Tortimer to a town animal/save record. */
#include "reward_event.h"
#include "constants.h"
#include "actors.h"
extern const u32 *volatile af_hp_native_npc_clip;
extern int af_holiday_observers_clip(void);
extern int af_cw_native_field_width(void),af_cw_native_field_height(void);

static PRESENT_DEMO_ACTOR *director(void) {
    mDemo_Clip_c *clip=af_rw_demo_clip;
    ACTOR *actor=clip?(ACTOR *)clip->demo_class:0;
    if(!actor || clip->type!=mDemo_CLIP_TYPE_PRESENT_DEMO ||
       *(const s16 *)actor!=0xF1 || !af_hp_owned(actor))return 0;
    PRESENT_DEMO_ACTOR *demo=(PRESENT_DEMO_ACTOR *)actor;
    return demo->type>=aPRD_TYPE_BIRTHDAY && demo->type<=aPRD_TYPE_GOLDEN_NET?demo:0;
}
u16 af_rw_present_name(void) {
    PRESENT_DEMO_ACTOR *demo=director();
    return demo?(demo->type==aPRD_TYPE_BIRTHDAY?0xD0CE:0xD0D0):0;
}
mNpc_MaskNpc_c *mNpc_GetSameMaskNpc(u16 name) {
    PRESENT_DEMO_ACTOR *demo=director();
    if(!demo || demo->type!=aPRD_TYPE_BIRTHDAY || name!=0xD0CE)return 0;
    AFHPResident *mask=af_hp_event_lookup(name);
    return mask && mask->used && mask->resident==af_rw_birthday_giver()?mask:0;
}
int mNpc_RegistMaskNpc(u16 mask,u16 animal,u16 cloth) {
    PRESENT_DEMO_ACTOR *demo=director();
    if(!demo || cloth || mask!=af_rw_present_name())return 0;
    if(demo->type==aPRD_TYPE_BIRTHDAY)
        return animal==af_rw_birthday_giver() &&
            af_hp_resident_bind(0xD073,animal,cloth)==0xD0CE;
    /* The mayor mask uses the complete static gift record, its full native
     * descriptor, and its own allocation. It is not a temporary resident. */
    return animal==SP_NPC_EV_SONCHO && af_hp_descriptor(0xF4)!=0;
}
static int setup(GAME_PLAY *g,u16 name,int rx,int ry,int rz,int bx,int bz,int x,int z) {
    if(!g || !af_hp_native_npc_clip || !af_holiday_observers_clip() ||
       !af_hp_native_npc_clip[0] || rx!=-1 || ry!=-1 || rz!=-1 ||
       bx<0 || bz<0 || bx>=af_cw_native_field_width() || bz>=af_cw_native_field_height() ||
       x<0 || x>=16 || z<0 || z>=16)return 0;
    const AFHPRecord *record=0;
    for(unsigned i=0;i<AF_HP_OWNER_COUNT;++i)
        if(af_hp_records[i].count==1 && af_hp_records[i].name==name &&
           (af_hp_records[i].kind&AF_HP_REWARD))record=af_hp_records+i;
    if(!record || !af_rw_owner_enabled(record) || !af_rw_owner_active(record,g))return 0;
    if(name==0xD0CE && !mNpc_GetSameMaskNpc(name))return 0;
    if(name==0xD0D0 && name!=af_rw_present_name())return 0;
    return ((AFRewardSetupNpc)(__UINTPTR_TYPE__)af_hp_native_npc_clip[0])
        (g,name,rx,ry,rz,bx,bz,x,z);
}
AFRewardSetupNpc af_rw_npc_setup(void) {
    return af_hp_native_npc_clip && af_holiday_observers_clip() && af_hp_native_npc_clip[0]?setup:0;
}
void af_rw_release_gift_mask(ACTOR *actor) {
    if(actor && af_hp_owned(actor) && actor->npc_id==0xD0CE)
        af_hp_event_unregister(actor->npc_id);
}
