#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#ifdef AF_V3_ROOM_NEEDLE
#define AF_V3_ROOM_RIG_PACKET
#define AF_V3_ROOM_JOINT
#endif
#include "../overlays/v3/room_carry_native.h"

RoomCarryNative af_test_carry_native;
RoomCarryProfile *af_test_carry_profiles[AF_V3_FURNITURE_CAPACITY];
RoomCarryWork af_test_carry_work;
RoomGoodsState af_test_room_goods;
RoomGoodsClip *af_test_room_goods_clip;
static u8 room_memory[0x18F00],goods_memory[0x12B0];
static RoomGoodsOverlay room_overlay={0x82D7F0,0x844400,0x80936710,0x8094F610,room_memory};
static RoomGoodsOverlay goods_overlay={0x8576C0,0x858960,0x80962A20,0x80963CD0,goods_memory};
static RoomCarryOwner owner={.overlay=&room_overlay};
static RoomGoodsActor goods_owner={.overlay=&goods_overlay};
static RoomRig actors[3];static u8 used[3];static u16 fg[256];static int places[256];
static RoomCarryProfile profiles[3];static RoomRigGame game;
static int contact[2]={1,0},player,permission,expected_shape,expected_destination,rotation;
static unsigned permissions,constructors,persists,custom_draws,loose_draws,checks;
static int expected_cell=-1,expected_child=-1;
static s16 drawn_angle;static float drawn_position[3];

static int cell(const float *pos) {return (int)(pos[0]/40.f)+16*(int)(pos[2]/40.f);}
static void original_ctor(RoomCarryOwner *o) {assert(o==&owner);constructors++;}
static void persist(void) {
    if (expected_cell>=0) assert(fg[expected_cell]==0x22FF);
    if (expected_child>=0) assert(fg[expected_child]==0x1000+actors[1].index*4 && places[expected_child]==1);
    assert(af_test_carry_native.carry.parent_id==-1);persists++;
}
static u16 *get_fg(s16 layer) {assert(layer==1);return fg;}
static int lookup(u16 *item,int *id,int x,int z,s16 layer) {
    assert(x>=0 && x<16 && z>=0 && z<16 && layer==1);
    int i=x+16*z;*item=fg[i];*id=places[i];return places[i]>=0 && places[i]<3;
}
static void set_furniture(RoomRig *actor,RoomGoodsPoint pos,int on) {
    assert(actor==actors+1 && actor->layer==1);
    float point[]={pos.x,pos.y,pos.z};int at=cell(point);
    assert(at>=0 && at<256);fg[at]=on ? (u16)(0x1000+actor->index*4) : 0;
}
static void set_place(u8 shape,int at,int id,s16 layer) {
    assert(shape==4 && at>=0 && at<256 && layer==1);places[at]=id;
}
static int permit_move(u8 shape,int destination) {
    assert(shape==expected_shape && destination==expected_destination);
    assert(af_test_carry_native.carry.parent_id==-1);permissions++;return permission;
}
static int permit_b(RoomRig *actor,void *c,void *p,s16 state) {
    assert(actor==actors && c==contact && p==&player && state==rotation);
    permissions++;return permission;
}
static int permit_ac(RoomRig *actor) {assert(actor==actors);permissions++;return permission;}
static void custom_draw(RoomRig *actor,RoomCarryOwner *o,void *p,RoomRigGame *g) {
    assert(actor==actors && o==&owner && p==profiles && g==&game);custom_draws++;
}
void *af_test_carry_resolve(u32 address) {
    switch(address) {
        case 0x8093B498:return original_ctor;
        case 0x80937140:return persist;
        case 0x80936A10:return get_fg;
        case 0x80945ED8:return lookup;
        case 0x80943C10:return set_furniture;
        case 0x80937ABC:return set_place;
        case 0x8093CAF8:return permit_move;
        case 0x8093FBE0:return permit_b;
        case 0x8093FD14:return permit_ac;
        case 0x80946F40:return custom_draw;
        default:assert(!"unexpected relocated call");return NULL;
    }
}
float af_carry_ground(RoomGoodsPoint pos,float offset) {assert(pos.y==0 && offset==0);return 0;}
float sin_s(s16 a) {return sinf((float)a*(6.2831853071795864769f/65536.f));}
float cos_s(s16 a) {return cosf((float)a*(6.2831853071795864769f/65536.f));}
void Matrix_RotateY(s16 angle,int mode) {assert(mode==1);drawn_angle=angle;}
int af_test_goods_count(u8 *at) {assert(at==goods_memory+0x9C4);return 34;}
void af_test_goods_destroy(u8 *at,RoomGoodsActor *actor) {assert(at==goods_memory+0x338 && actor==&goods_owner);}
void af_goods_fg2(u16 item,RoomGoodsPoint pos) {(void)item;(void)pos;assert(!"unexpected drop");}
static void single_draw(RoomRigGame *g,u16 item,const float *pos,float scale) {
    assert(g==&game && item==0x22FF && scale==.01f && custom_draws==loose_draws+1);
    drawn_angle=af_v3_goods_single_angle(0);memcpy(drawn_position,pos,sizeof(drawn_position));loose_draws++;
}
static RoomGoodsClip clip={.single_draw=single_draw};
static void setup(int mixed) {
    memset(actors,0,sizeof(actors));memset(fg,0,sizeof(fg));
    for (int i=0;i<256;i++) places[i]=0xC8;
    for (int i=0;i<3;i++) {
        used[i]=1;actors[i].id=i;actors[i].index=100+i;actors[i].shape_type=4;
        profiles[i].height=50;af_test_carry_profiles[100+i]=profiles+i;
    }
    actors[0].position[0]=mixed ? 120 : 100;actors[0].position[2]=mixed ? 120 : 100;
    actors[0].shape_type=mixed ? 5 : 4;
    actors[1].position[0]=100;actors[1].position[1]=50;actors[1].position[2]=100;
    actors[1].layer=1;fg[34]=(u16)(0x1000+actors[1].index*4);places[34]=1;
    if (mixed) fg[35]=0x22FF;
    af_test_carry_work=(RoomCarryWork){actors,used,3};af_test_room_goods_clip=&clip;
    assert(af_v3_goods_ctor(&goods_owner)==34);af_v3_goods_set(2,3,1,1200);
    af_v3_carry_ctor(&owner);assert(af_test_carry_native.magic==ROOM_CARRY_NATIVE_MAGIC);
    permission=1;expected_shape=actors[0].shape_type;expected_destination=35;
    expected_cell=-1;expected_child=-1;custom_draws=loose_draws=0;
    assert(!af_v3_carry_blocked(contact));
}
static void assert_near(float a,float b) {assert(fabsf(a-b)<.001f);checks++;}

#define AF_SURFACE_ITEMS_VROM 0x03400000u
#define AF_SURFACE_ITEMS_CRC 0x12345678u
#define AF_SURFACE_ITEMS_BYTES 16384u
#define AF_ROOM_GOODS_VROM 0x03404000u
#define AF_ROOM_GOODS_CRC 0x87654321u
#define AF_ROOM_GOODS_BYTES 1280u
#define AF_ROOM_CARRY_VROM 0x03404500u
#define AF_ROOM_CARRY_CRC 0x43214321u
#define AF_ROOM_CARRY_BYTES 8192u
#define AF_V3_EDITABLE_CHECKSUMS 1
#include "../overlays/v3/surface_bootstrap.c"
u32 af_test_surface_memory[AF_SURFACE_ITEMS_BYTES/4],af_test_goods_magic,af_test_carry_magic;
unsigned char af_test_goods_code[AF_ROOM_GOODS_BYTES],af_test_carry_code[AF_ROOM_CARRY_BYTES];
static unsigned stage,fail_stage,init_calls;
static void check_io(const void *p,u32 n,unsigned op) {
    const void *targets[]={af_test_surface_memory,af_test_goods_code,af_test_carry_code};
    const u32 sizes[]={AF_SURFACE_ITEMS_BYTES,AF_ROOM_GOODS_BYTES,AF_ROOM_CARRY_BYTES};
    assert(stage/4<3 && stage%4==op && p==targets[stage/4] && n==sizes[stage/4]);
}
int af_surface_dma(void *p,u32 source,u32 n) {
    const u32 sources[]={AF_SURFACE_ITEMS_VROM,AF_ROOM_GOODS_VROM,AF_ROOM_CARRY_VROM};
    check_io(p,n,0);assert(source==sources[stage/4]);return ++stage==fail_stage;
}
u32 af_surface_crc(const void *p,u32 n) {
    const u32 crc[]={AF_SURFACE_ITEMS_CRC,AF_ROOM_GOODS_CRC,AF_ROOM_CARRY_CRC};
    check_io(p,n,1);u32 value=crc[stage/4];return ++stage==fail_stage ? 0 : value;
}
void af_surface_writeback(void *p,u32 n) {check_io(p,n,2);stage++;}
void af_surface_invalidate(void *p,u32 n) {check_io(p,n,3);stage++;}
int af_surface_prior_init(void) {assert(stage++==12 && !af_test_goods_magic && !af_test_carry_magic);init_calls++;return 1;}

#ifdef AF_V3_ROOM_NEEDLE
#include "v3_room_needle_binding.inc"
#endif

int main(void) {
    assert(af_v3_carry_blocked(contact));assert(!af_v3_carry_parent(actors));
    setup(1);
    permission=0;unsigned p=permissions;
    assert(!af_v3_carry_permit_move(5,35,actors) && permissions==p+1);
    assert(fg[34] && fg[35] && af_test_carry_native.carry.parent_id==-1);
    permission=1;actors[0].kept_item=1;assert(!af_v3_carry_permit_move(5,35,actors));actors[0].kept_item=0;
    used[1]=0;assert(!af_v3_carry_permit_move(5,35,actors));used[1]=1;assert(fg[34] && fg[35]);
    assert(af_v3_carry_permit_move(5,35,actors));assert(!fg[34] && !fg[35] && places[34]==0xC8);
    assert(af_v3_carry_parent(actors+1)==actors && !af_v3_carry_angle(actors+1));
    assert(af_v3_carry_blocked(contact));
    actors[0].state=1;actors[0].position[0]+=20;
    assert(af_v3_carry_after_move(actors,&owner)==3);assert_near(actors[1].position[0],120);
    af_v3_carry_draw(actors,&owner,profiles,&game);
    assert(custom_draws==1 && loose_draws==1 && drawn_angle==1200);
    assert_near(drawn_position[0],160);assert_near(drawn_position[1],50);assert_near(drawn_position[2],100);
    actors[0].position[0]+=20;actors[0].state=0;
    assert(af_v3_carry_after_move(actors,&owner)==3);
    assert(fg[35]==0x1000+actors[1].index*4 && fg[36]==0x22FF && places[35]==1);
    assert(af_v3_goods_get(2,4,1)==1200 && af_test_carry_native.carry.parent_id==-1);
    assert(!af_v3_carry_parent(actors+1));expected_cell=36;expected_child=35;
    af_v3_carry_destruct(&owner);assert(!af_test_carry_native.magic);
    for (int direction=-1;direction<=1;direction+=2) {
        setup(0);rotation=direction>0 ? 8 : 7;
        permission=0;assert(!af_v3_carry_permit_rotate_b(actors,contact,&player,rotation));
        permission=1;assert(af_v3_carry_permit_rotate_b(actors,contact,&player,rotation));
        actors[0].state=direction>0 ? 3 : 4;actors[0].s_angle_y=(s16)(direction*8192);
        af_v3_carry_after_move(actors,&owner);assert(af_v3_carry_angle(actors+1)==direction*8192);
        af_v3_carry_draw_rotation(123,1,actors+1);assert(drawn_angle==123+direction*8192);
        actors[0].s_angle_y=(s16)(direction*16384);actors[0].state=0;af_v3_carry_after_move(actors,&owner);
        assert(actors[1].s_angle_y==direction*16384);assert_near(actors[1].angle_y,direction*90.f);
        assert(fg[34] && places[34]==1);expected_child=34;af_v3_carry_destruct(&owner);
    }
    setup(0);permission=0;assert(!af_v3_carry_permit_rotate_ac(actors));permission=1;
    assert(af_v3_carry_permit_rotate_ac(actors));actors[0].state=3;actors[0].angle_y_target=90;
    expected_child=34;af_v3_carry_destruct(&owner);assert(actors[1].s_angle_y==16384);
    setup(1);assert(af_v3_carry_permit_move(5,35,actors));actors[0].state=9;
    memcpy(actors[0].target_position,actors[0].position,sizeof(actors[0].position));actors[0].target_position[0]+=40;
    expected_cell=36;expected_child=35;af_v3_carry_destruct(&owner);
    assert(fg[36]==0x22FF && places[35]==1 && !af_test_carry_native.magic);
    setup(0);assert(af_v3_carry_permit_rotate_ac(actors));actors[0].state=0;fg[34]=0x22FF;
    af_v3_carry_after_move(actors,&owner);assert(af_test_carry_native.failed_restoration && af_test_carry_native.carry.parent_id==0);
    fg[34]=0;af_v3_carry_after_move(actors,&owner);assert(!af_test_carry_native.failed_restoration && fg[34]);
    expected_child=34;af_v3_carry_destruct(&owner);
    setup(0);memset(fg,0,sizeof(fg));af_v3_goods_destruct(&goods_owner);af_test_room_goods_clip=NULL;
    assert(af_v3_carry_permit_move(4,35,actors));assert(af_test_carry_native.carry.parent_id==-1);
    af_v3_carry_destruct(&owner);
    const unsigned failures[]={0,1,2,5,6,9,10};
    for (unsigned i=0;i<sizeof(failures)/sizeof(*failures);i++) {
        stage=0;init_calls=0;fail_stage=failures[i];af_test_goods_magic=1;af_test_carry_magic=1;
        assert(af_v3_surface_init()==!fail_stage && stage==(fail_stage ? fail_stage : 13));
        assert(init_calls==!fail_stage && af_test_carry_magic==!!fail_stage);
        assert(af_test_goods_magic==(fail_stage && fail_stage<9));
    }
    printf("native carrying adapters: permissions, translation, both rotations, parent drawing, cleanup, retry, and startup pass (%u numeric checks)\n",checks);
#ifdef AF_V3_ROOM_NEEDLE
    test_needle_binding();
#endif
    return 0;
}
