#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_ROOM_RADIO_SONG 27
#include "../overlays/v3/room_music.c"
#include "../overlays/v3/room_music_native.c"

static unsigned events[64],event_count,checks,notes;
static void event(unsigned kind,unsigned value) {assert(event_count<64);events[event_count++]=(kind<<16)|value;}
void mBGMPsComp_make_ps_room(u8 song,u16 timer) {assert(!timer);event(1,song);}
void mBGMPsComp_delete_ps_room(u8 song,u16 timer) {assert(!timer);event(2,song);}
void mBGMPsComp_MDPlayerPos_make(void) {event(3,0);}
void mBGMPsComp_MDPlayerPos_delete(void) {event(4,0);}
static unsigned matrix_calls;
void Matrix_RotateY(s16 angle,int mode) {assert(angle==-0x7000 && mode==1);++matrix_calls;}
void *_Matrix_to_Mtx(void *p) {assert(!((uptr)p&15));memset(p,0x51,64);return p;}
void osWritebackDCache(void *p,int n) {assert(p && n==64);}
static void request(int id,EffectPosition pos,int priority,s16 angle,void *game,u16 item,s16 a,s16 b) {
    assert(id==32 && pos.x==4 && pos.y==7 && pos.z==20 && priority==1 && angle==0x2000 && game);
    assert(item==0x1FCC && a==1 && !b);++notes;
}
static RoomEffectClip effect_clip={.request=request};
RoomEffectClip *af_test_effect_clip=&effect_clip;
RoomMusicClip *af_test_music_clip;
RoomMusicProfile *af_test_music_profiles[AF_V3_FURNITURE_CAPACITY];
static RoomRig native_actors[4];
static u8 used[4]={1,1,1,0};
static RoomMusicProfile profiles[4]={ {.interaction=8},{.interaction=0x4000},{.interaction=0},{.interaction=0x4000} };
static u8 overlay_memory[8];
static void exclusive(RoomRig *selected) {
    event(5,(unsigned)(selected-native_actors));
    for (unsigned i=0;i<4;++i) if (used[i] && (profiles[i].interaction&0x4008)) {
        native_actors[i].switched=0;native_actors[i].changed=1;
    }
    selected->switched=1;selected->changed=1;
}
void *af_test_music_resolve(u8 *base,u32 address) {
    assert(base==overlay_memory && address==0x809385E4);return exclusive;
}

/* Compile the actual checked donor helpers, with only their engine types and
   service calls supplied here. No handwritten reference state machine. */
typedef struct {u16 name;u8 switch_bit,switch_changed_flag;s16 haniwa_state;} FTR_ACTOR;
typedef struct {int md_no,last_md_no;u8 reserve_flag;s16 timer;FTR_ACTOR *reserved_ftr_actor,*active_ftr_actor;int active_flag;} aMR_bgm_info_c;
typedef struct {aMR_bgm_info_c bgm_info;} MY_ROOM_ACTOR;
typedef MY_ROOM_ACTOR ACTOR;
typedef struct {u16 interaction_type;} aFTR_PROFILE;
static FTR_ACTOR donor_actors[4];
static aFTR_PROFILE donor_profiles[4]={{8},{0x4000},{0},{0x4000}};
static struct {FTR_ACTOR *ftr_actor_list;u8 *used_list;int list_size;} l_aMR_work={donor_actors,used,4};
static aFTR_PROFILE *aMR_GetFurnitureProfile(u16 name) {assert(name<4);return donor_profiles+name;}
#define TRUE 1
#define FALSE 0
#define BGM_SPORTSFAIR_AEROBICS 27
#define aFTR_INTERACTION_TYPE_MUSIC_DISK 8
#define aFTR_INTERACTION_TYPE_RADIO_AEROBICS 0x4000
#define aFTR_CHECK_INTERACTION(flags,bit) ((flags)&(bit))
static void aMR_ReserveDefaultBgm(ACTOR *,FTR_ACTOR *);
static void aMR_ChangeMDBgm(ACTOR *,FTR_ACTOR *);
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#include "donor_room_music.inc"
#pragma GCC diagnostic pop

static int donor_id(FTR_ACTOR *actor) {return actor ? (int)(actor-donor_actors) : -1;}
static int native_id(RoomRig *actor) {return actor ? (int)(actor-native_actors) : -1;}
static void compare(RoomMusic *n,aMR_bgm_info_c *d) {
    assert(n->song==d->md_no && n->previous_song==d->last_md_no && n->reserved==d->reserve_flag);
    assert(n->timer==d->timer && n->active==d->active_flag);
    assert(native_id(n->reserved_actor)==donor_id(d->reserved_ftr_actor));
    assert(native_id(n->active_actor)==donor_id(d->active_ftr_actor));
    for (unsigned i=0;i<4;++i) {
        assert(native_actors[i].switched==donor_actors[i].switch_bit);
        assert(native_actors[i].changed==donor_actors[i].switch_changed_flag);
        assert(native_actors[i].haniwa_state==donor_actors[i].haniwa_state);
    }
    ++checks;
}
static unsigned saved_events[64],saved_count;
static void save_events(void) {memcpy(saved_events,events,sizeof(events));saved_count=event_count;event_count=0;}
static void compare_events(int exclusive_id) {
    unsigned extra=exclusive_id>=0;
    if (extra)assert(saved_count && saved_events[0]==((5u<<16)|(unsigned)exclusive_id));
    assert(saved_count==event_count+extra && !memcmp(saved_events+extra,events,event_count*sizeof(*events)));
    event_count=0;
}
static void reset(RoomMusic *n,aMR_bgm_info_c *d) {
    memset(native_actors,0,sizeof(native_actors));memset(donor_actors,0,sizeof(donor_actors));
    for (unsigned i=0;i<4;++i) {native_actors[i].index=i;donor_actors[i].name=i;}
    *n=(RoomMusic){.song=-1,.previous_song=-1};*d=(aMR_bgm_info_c){.md_no=-1,.last_md_no=-1};event_count=0;
}
int main(void) {
    RoomGoodsOverlay overlay={.vrom_start=0x82D7F0,.vram_start=0x80936710,.vram_end=0x8094F610,.loaded=overlay_memory};
    RoomMusicOwner owner={.actor.overlay=&overlay};RoomMusicClip clip={&owner};af_test_music_clip=&clip;
    MY_ROOM_ACTOR donor;RoomMusic *n=&owner.music;aMR_bgm_info_c *d=&donor.bgm_info;
    for (unsigned i=0;i<4;++i)af_test_music_profiles[i]=profiles+i;
    const int songs[]={-1,27,128,183};
    for (unsigned active=0;active<2;++active)for (unsigned reserve=0;reserve<3;++reserve)
    for (unsigned prev=0;prev<4;++prev)for (unsigned song=0;song<4;++song) {
        reset(n,d);n->song=d->md_no=songs[song];n->previous_song=d->last_md_no=songs[prev];
        n->active=d->active_flag=active;n->reserved=d->reserve_flag=reserve;
        n->active_actor=native_actors;d->active_ftr_actor=donor_actors;
        af_v3_room_music_native_apply(&owner,native_actors+1);save_events();
        aMR_ChangeMDBgm(&donor,donor_actors+1);compare_events(-1);compare(n,d);
    }
    for (unsigned on=0;on<3;++on)for (unsigned changed=0;changed<3;++changed)for (int h=-1;h<3;++h) {
        reset(n,d);n->song=d->md_no=128;n->previous_song=d->last_md_no=128;n->active=d->active_flag=1;
        n->active_actor=native_actors;d->active_ftr_actor=donor_actors;
        for (unsigned i=0;i<4;++i)native_actors[i].switched=donor_actors[i].switch_bit=1;
        native_actors[1].switched=donor_actors[1].switch_bit=on;
        native_actors[1].changed=donor_actors[1].switch_changed_flag=changed;
        native_actors[1].haniwa_state=donor_actors[1].haniwa_state=h;
        af_v3_room_music_native_move(native_actors+1,&owner);save_events();
        aMR_RadioCommonMove(donor_actors+1,&donor);compare_events(h!=1 && changed ? 1 : -1);compare(n,d);
        /* Owner applies deferred haniwa startup through the same shared path. */
        af_v3_room_music_native_apply(&owner,native_actors+1);save_events();
        aMR_ChangeMDBgm(&donor,donor_actors+1);compare_events(-1);compare(n,d);
        af_v3_room_music_native_radio_dt(native_actors+1);save_events();
        aMR_RadioCommonDt(donor_actors+1,&donor);compare_events(-1);compare(n,d);
        af_v3_room_radio_ct(native_actors+1);aMR_RadioCommonCt(donor_actors+1,1);compare(n,d);
    }
    for (unsigned i=0;i<4;++i)for (unsigned song=0;song<4;++song)for (unsigned on=0;on<3;++on) {
        reset(n,d);n->song=d->md_no=songs[song];n->active=d->active_flag=1;
        n->active_actor=native_actors+i;d->active_ftr_actor=donor_actors+i;
        native_actors[i].switched=donor_actors[i].switch_bit=on;
        af_v3_room_music_native_disk_dt(native_actors+i,&owner);save_events();
        aMR_MiniDiskCommonDt(donor_actors+i,&donor);compare_events(-1);compare(n,d);
    }
    /* Verify direct general reservation separately from the restricted native
       minidisk item-ID reservation. */
    reset(n,d);af_v3_room_music_reserve(n,native_actors+1,27,15);aMR_ReserveBgm(&donor,27,donor_actors+1,15);compare(n,d);
    RoomMusic before=*n;overlay.loaded=0;af_v3_room_music_native_apply(&owner,native_actors+1);
    af_v3_room_music_native_move(native_actors+1,&owner);af_v3_room_music_native_radio_dt(native_actors+1);
    assert(!memcmp(n,&before,sizeof(before)) && !event_count);overlay.loaded=overlay_memory;

    RoomRig *a=native_actors+1;RoomRigGame game={0};a->position[0]=4;a->position[1]=10;a->position[2]=20;a->s_angle_y=0x3000;
    a->switched=1;a->joint[0][0]=0;
    for (unsigned i=0;i<180;++i)af_v3_room_radio_notes(a,&game,0x1FCC);
    assert(notes==9 && a->joint[0][0]==36);a->switched=0;
    af_v3_room_radio_notes(a,&game,0x1FCC);assert(notes==9 && a->joint[0][0]==36);
    a->switched=1;af_v3_room_radio_notes(a,&game,0x1FCC);assert(notes==10 && a->joint[0][0]==2);
    af_test_effect_clip=0;a->joint[0][0]=36;af_v3_room_radio_notes(a,&game,0x1FCC);assert(a->joint[0][0]==2 && notes==10);

    _Alignas(16) u8 arena[256];RoomRigGraphics gfx={.head=(RoomCommand *)arena,.tail=arena+sizeof(arena)};game.gfx=&gfx;
    af_v3_room_radio_draw(a,&game,0x06000020,0x06000000);
    assert(matrix_calls==1 && (u8 *)gfx.head==arena+24 && gfx.tail==arena+192);
    RoomCommand *commands=(RoomCommand *)arena;
    assert(commands[0].a==0xDA380003 && commands[0].b==(u32)(uptr)(arena+192));
    assert(commands[1].a==0xDB060020 && commands[1].b==0x06000000);
    assert(commands[2].a==0xDE000000 && commands[2].b==0x06000020);
    gfx.tail=(u8 *)gfx.head+80;RoomRigGraphics saved=gfx;
    af_v3_room_radio_draw(a,&game,0x06000020,0x06000000);assert(!memcmp(&saved,&gfx,sizeof(gfx)) && matrix_calls==1);
    printf("%u actual-donor music comparisons; native owner, notes, and bounded drawing pass\n",checks);
}
