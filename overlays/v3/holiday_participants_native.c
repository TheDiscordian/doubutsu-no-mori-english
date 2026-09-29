/* Shared native NPC and event-storage bridge for the entire generated family.
 * Actor admission, donor text, player actions, tools, and effect/audio mapping
 * remain required providers. No stub returns success for an absent provider. */
#include "holiday_participants.h"
#include "constants.h"
extern int af_holiday_native_type(unsigned int);
extern int af_holiday_observers_clip(void);
extern void *af_hp_native_get_save(int,int),*af_hp_native_reserve_save(int,int);
extern void af_hp_native_dying(int,ACTOR *);
extern const u32 *volatile af_hp_native_npc_clip;
extern int af_hp_admit(ACTOR *,GAME *);
extern int af_hp_owned(const ACTOR *);
extern int af_hp_native_player_state(GAME *);
extern void *af_hp_message_window(void),*af_hp_choice_window(void);
extern int af_hp_message_continue(void *),af_hp_choice_index(void *);
extern void af_hp_native_message(int),af_hp_native_continue(void *,int);
extern int af_hp_message(int);
extern AFHPShrine *volatile af_hp_native_shrine;
extern u8 af_hp_players[4][0xBD0],af_hp_visitor[0xBD0];
extern u8 *volatile af_hp_active;
extern volatile u8 af_hp_player_index;
extern int af_hp_source_money_check(u32);
extern void af_hp_source_get_sell_price(u32);
extern const AFHPTools *volatile af_hp_native_tools;
extern const AFHPEffects *volatile af_hp_native_effects;
extern void af_hp_native_sound(u16,xyz_t *),af_hp_native_continuous(u32,u16,xyz_t *);
/* The donor's visible offering coin has no native counterpart. Its complete
 * imported effect is a required provider, never a same-number native effect. */
extern void af_hp_coin(xyz_t,int,s16,GAME *,u16,s16,s16);
extern u8 af_hp_native_animals[15][0x528];
extern int af_hp_native_find_resident(void *,u16,int),af_hp_native_free_resident(void *);
extern ACTOR *af_hp_native_make(void *,GAME *,int,f32,f32,f32,int,int,int,int,int,int,u16,int,int,int);

ACTOR *Actor_info_make_actor(void *info,GAME *game,int profile,f32 x,f32 y,f32 z,
        int rx,int ry,int rz,int bx,int bz,int unit,u16 name,int arg,int sx,int sz) {
    if(!af_hp_available || !game || info!=af_hp_actor_info(game) || profile!=mAc_PROFILE_ROPE ||
            rx || ry || rz || bx!=-1 || bz!=-1 || unit!=-1 || name || arg!=-1 || sx!=-1 || sz!=-1 ||
            !mEv_get_save_area(mEv_EVENT_SPORTS_FAIR_TUG_OF_WAR,9))return 0;
    for(unsigned int i=0;i<AF_HP_OWNER_COUNT;i++) {
        const AFHPRecord *r=af_hp_records+i;
        if(r->part==4 && r->source && r->source->source_profile==profile)
            return af_hp_native_make(info,game,r->profile,x,y,z,rx,ry,rz,bx,bz,unit,name,arg,sx,sz);
    }
    return 0;
}
typedef struct {
    u32 arrays[4];s16 unused,duration;f32 start,end;u32 mode;f32 morph;
    u32 eye;s16 eye_type,eye_stop;u32 mouth;
    s16 mouth_type,mouth_stop,effect_frame,effect_type;u32 effect,sound;
} AFHPMotion;
_Static_assert(sizeof(AFHPMotion)==64,"Complete imported NPC motion");
extern const AFHPMotion af_hp_prayer_motion;
extern void af_holiday_keyframe_init(void *,void *,const void *,f32,f32,f32,f32,f32,int,void *);

#define FN(word,ret,...) ((ret (*)(__VA_ARGS__))(word))

static ACTOR *tool(int kind,int mode,ACTOR *parent,GAME *game,int argument,void *bank) {
    const AFHPTools *t=af_hp_native_tools;
    int native=kind==TOOL_PISTOL?36:kind==TOOL_FLAG?37:-1;
    if(native<0 || mode!=aTOL_ACTION_S_TAKEOUT || !parent || !af_hp_owned(parent) ||
            !game || !t || !t->aTOL_birth_proc)return 0;
    /* Donor special takeout is four; native special takeout is three. */
    return t->aTOL_birth_proc(native,3,parent,game,argument,bank);
}
const AFHPTools af_hp_tools_services={tool};
static int effect_id(int source) {
    switch(source) {
        case eEC_EFFECT_DUST:return 1;
        case eEC_EFFECT_ASE2:return 30;
        case eEC_EFFECT_DASH_ASIMOTO:return 31;
        case eEC_EFFECT_TUMBLE:return 53;
        default:return -1;
    }
}
static void effect(int source,xyz_t p,int priority,s16 angle,GAME *g,u16 owner,s16 a,s16 b) {
    if(!g)return;
    if(source==eEC_EFFECT_COIN) {af_hp_coin(p,priority,angle,g,owner,a,b);return;}
    int id=effect_id(source);const AFHPEffects *e=af_hp_native_effects;
    if(id>=0 && e && e->effect_make_proc)e->effect_make_proc(id,p,priority,angle,g,owner,a,b);
}
static void kill(int source,u16 owner) {
    int id=effect_id(source);const AFHPEffects *e=af_hp_native_effects;
    if(id>=0 && e && e->effect_kill_proc)e->effect_kill_proc(id,owner);
}
const AFHPEffects af_hp_effect_services={effect,kill};
void sAdo_OngenTrgStart(u32 source,xyz_t *p) {
    if(!p)return;
    switch(source) {
        case NA_SE_15D:case NA_SE_15E:case NA_SE_116:case MONO(NA_SE_53):
        case NA_SE_ARAIIKI_OTHER:case NA_SE_ARAIIKI_GIRL:case NA_SE_ARAIIKI_BOY:case NA_SE_106:
            /* Complete native counterpart callers retain these sound IDs. */
            af_hp_native_sound((u16)source,p);break;
    }
}
void sAdo_OngenPos(u32 owner,u32 source,xyz_t *p) {
    if(p && (source==0x2F || source==0x31))af_hp_native_continuous(owner,(u16)source,p);
}

int af_hp_native_resident_index(u16 name) {
    return (name>>12)==14?af_hp_native_find_resident(af_hp_native_animals,name,15):-1;
}
int af_hp_native_resident_valid(int index,u16 name) {
    if(index<0 || index>=15 || name>>12!=14)return 0;
    const u8 *p=af_hp_native_animals[index];
    return *(const u16 *)p==name && p[11]<6 && !af_hp_native_free_resident((void *)p);
}
void mEv_actor_dying_message(int donor,ACTOR *a) {
    int native=af_holiday_native_type(donor);
    if(a && native>=0 && (donor==1 || donor==14 || donor==15))af_hp_native_dying(native,a);
}
void *af_hp_actor_info(GAME_PLAY *g) {return g?(u8 *)g+0x1C78:0;}
u32 af_hp_frame(GAME_PLAY *g) {return g?*(u32 *)((u8 *)g+0x1EA0):0;}
AFHPShrine *af_hp_shrine(void) {return af_hp_native_shrine;}
int af_hp_continue(void) {
    void *window=af_hp_message_window();return window?af_hp_message_continue(window):0;
}
int af_hp_choice(void) {
    void *window=af_hp_choice_window();return window?af_hp_choice_index(window):-1;
}
void mDemo_Set_msg_num(int source) {
    int target=af_hp_message(source);if(target>=0)af_hp_native_message(target);
}
void af_hp_continue_message(int source) {
    int target=af_hp_message(source);void *window=af_hp_message_window();
    if(target>=0 && window)af_hp_native_continue(window,target);
}
int mPlib_get_player_actor_main_index(GAME *g) {
    /* Only these states are observed by this family. Return a non-state for
     * every other native ID instead of aliasing a donor state by coincidence. */
    switch(af_hp_native_player_state(g)) {
        case 0x49:return mPlayer_INDEX_DEMO_WAIT;
        case 0x4A:return mPlayer_INDEX_DEMO_WALK;
        case 0x55:return mPlayer_INDEX_THROW_MONEY;
        case 0x56:return mPlayer_INDEX_PRAY;
        default:return -1;
    }
}
AFHPPrivate *af_hp_private(void) {
    unsigned int player=af_hp_player_index;
    if(player>4)return 0;
    u8 *expected=player<4?af_hp_players[player]:af_hp_visitor;
    if(af_hp_active!=expected || expected[0x10]>1)return 0;
    return (AFHPPrivate *)expected;
}
int mSP_money_check(int amount) {
    return amount>=0 && af_hp_private() && af_hp_source_money_check((u32)amount);
}
void mSP_get_sell_price(int amount) {
    /* The source controller asks before payment. Recheck immediately before
     * mutation so a stale player/insufficient wallet cannot consume bags. */
    if(mSP_money_check(amount))af_hp_source_get_sell_price((u32)amount);
}

void af_hp_motion_override(ACTOR *a) {
    if(!a || !af_hp_owned(a) || ((NPC_ACTOR *)a)->draw.animation_id!=71)return;
    const AFHPMotion *m=&af_hp_prayer_motion;
    static const u16 frames[]={0x198,0x354,0x510};
    for(unsigned int i=0;i<3;i++) {
        /* An equipped hand tool and a speaking mouth own their sub-animation;
         * only the same branches as the original complete initializer change. */
        if((i==1 && ((u8 *)a)[0x729]) || (i==2 && ((NPC_ACTOR *)a)->talk_info.type))continue;
        u8 *frame=(u8 *)a+frames[i];
        f32 current=i?m->start:((AFHPFrame *)frame)->current_frame;
        f32 speed=((AFHPFrame *)frame)->speed;
        void *skeleton=*(void **)(frame+0x18);
        af_holiday_keyframe_init(frame,skeleton,m,m->start,m->end,current,speed,m->morph,m->mode,0);
    }
}

extern void af_hp_previous_animation(ACTOR *,int,int);
void af_hp_animation(ACTOR *a,int index,int talk) {
    /* Chain the existing complete initializer, including Tortimer's cane.
     * Hook the shared entry so default-animation calls receive the complete
     * imported prayer motion too, not just explicit source clip calls. */
    af_hp_previous_animation(a,index,talk);
    af_hp_motion_override(a);
}
