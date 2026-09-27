#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "goods_flags.inc"
#include "../overlays/v3/room_goods.c"
#define mCoBG_LAYER1 1
static s16 SG_angle_y[16][16];
#include "donor_goods.inc"

RoomGoodsState af_test_room_goods;
RoomGoodsClip *af_test_room_goods_clip;
static u8 owner_memory[0x12B0];
static RoomGoodsOverlay overlay={0x8576C0,0x858960,0x80962A20,0x80963CD0,owner_memory};
static RoomGoodsActor owner={.overlay=&overlay},other={.overlay=&overlay};
static unsigned count_calls,destroy_calls,draw_calls,fg_calls,depth;
static s16 expected_angle;
static int drop_x,drop_z;
static RoomGoodsPoint drop_point;
static u16 drop_item;

int af_test_goods_count(u8 *address) {
    assert(address==owner_memory+0x9C4);count_calls++;return 34;
}
void af_test_goods_destroy(u8 *address,RoomGoodsActor *actor) {
    assert(address==owner_memory+0x338 && (actor==&owner || actor==&other));destroy_calls++;
}
void af_goods_fg2(u16 item,RoomGoodsPoint position) {
    assert(item==drop_item && !memcmp(&position,&drop_point,sizeof(position)));
    assert(af_v3_goods_get(drop_z,drop_x,1)==expected_angle);fg_calls++;
}
static void draw(RoomRigGame *game,u16 item,const float *position,float scale) {
    assert(game && item==0x22FF && position[0]==20.f && scale==.01f);draw_calls++;
    for (int row=-1;row<=34;row++) {
        int yes=row>=0 && row<34 && expected_rotation[row];
        assert(af_v3_goods_single_angle(row)==(yes ? expected_angle : 0));
    }
    if (!depth) {
        depth++;s16 previous=expected_angle;expected_angle=-2345;
        assert(af_v3_goods_single(game,item,position,scale,expected_angle));
        expected_angle=previous;depth--;
        assert(af_v3_goods_single_angle(0)==expected_angle);
    }
}

#define AF_SURFACE_ITEMS_VROM 0x03400000u
#define AF_SURFACE_ITEMS_CRC 0x12345678u
#define AF_SURFACE_ITEMS_BYTES 16384u
#define AF_ROOM_GOODS_VROM 0x03404000u
#define AF_ROOM_GOODS_CRC 0x87654321u
#define AF_ROOM_GOODS_BYTES 2048u
#define AF_V3_EDITABLE_CHECKSUMS 1
#include "../overlays/v3/surface_bootstrap.c"
u32 af_test_surface_memory[AF_SURFACE_ITEMS_BYTES/4],af_test_goods_magic;
unsigned char af_test_goods_code[AF_ROOM_GOODS_BYTES];
static unsigned stage,fail_stage,init_calls;
static int init_result;
static void check_io(const void *p,u32 n,unsigned op) {
    unsigned packet=stage/4;
    assert(stage%4==op && packet<2);
    assert(p==(packet ? (void *)af_test_goods_code : (void *)af_test_surface_memory));
    assert(n==(packet ? AF_ROOM_GOODS_BYTES : AF_SURFACE_ITEMS_BYTES));
}
int af_surface_dma(void *p,u32 source,u32 n) {
    check_io(p,n,0);assert(source==(stage ? AF_ROOM_GOODS_VROM : AF_SURFACE_ITEMS_VROM));
    return ++stage==fail_stage;
}
u32 af_surface_crc(const void *p,u32 n) {
    check_io(p,n,1);stage++;
    return stage==fail_stage ? 0 : (stage==2 ? AF_SURFACE_ITEMS_CRC : AF_ROOM_GOODS_CRC);
}
void af_surface_writeback(void *p,u32 n) {check_io(p,n,2);stage++;}
void af_surface_invalidate(void *p,u32 n) {check_io(p,n,3);stage++;}
int af_surface_prior_init(void) {
    assert(stage++==8 && af_test_goods_magic==0);init_calls++;return init_result;
}

int main(void) {
    assert(!af_v3_goods_get(0,0,1));af_v3_goods_set(0,0,1,123);
    assert(!af_v3_goods_ctor(NULL) && !count_calls);
    assert(af_v3_goods_ctor(&owner)==34 && count_calls==1);
    assert(af_test_room_goods.magic==ROOM_GOODS_MAGIC && af_test_room_goods.owner==&owner);
    unsigned comparisons=0;
    for (int layer=0;layer<3;layer++) for (int z=0;z<16;z++) for (int x=0;x<16;x++) {
        s16 angle=(s16)(x*2131-z*1827+layer*983);
        af_v3_goods_set(z,x,layer,angle);
        Shop_Goods_Actor_single_set_angle_y(z,x,layer,angle);
        assert(af_v3_goods_get(z,x,layer)==Shop_Goods_Actor_single_get_angle_y(z,x,layer));
        comparisons++;
        for (int row=0;row<34;row++) {
            RoomGoodsRow *p=(RoomGoodsRow *)(owner_memory+0xFB0+20*row);
            assert(af_v3_goods_grid_angle(&owner,x,z,layer,p)==
                (layer==1 && expected_rotation[row] ? SG_angle_y[z][x] : 0));
        }
    }
    assert(!memcmp(SG_angle_y,af_test_room_goods.angles,sizeof(SG_angle_y)));
    for (int z=-1;z<=16;z++) for (int x=-1;x<=16;x++) if (z<0 || x<0 || z==16 || x==16) {
        RoomGoodsState before=af_test_room_goods;af_v3_goods_set(z,x,1,123);
        assert(!af_v3_goods_get(z,x,1) && !memcmp(&before,&af_test_room_goods,sizeof(before)));
    }
    RoomGoodsRow *rows=(RoomGoodsRow *)(owner_memory+0xFB0);
    assert(!af_v3_goods_grid_angle(&other,1,1,1,rows));
    assert(!af_v3_goods_grid_angle(&owner,1,1,1,rows+34));
    assert(!af_v3_goods_grid_angle(&owner,1,1,1,(RoomGoodsRow *)(owner_memory+0xFB1)));
    assert(!af_v3_goods_grid_angle(&owner,1,1,1,(RoomGoodsRow *)owner_memory));
    assert(!af_v3_goods_grid_angle(&owner,1,1,1,NULL));
    overlay.vrom_start^=16;assert(!af_v3_goods_grid_angle(&owner,1,1,1,rows));overlay.vrom_start^=16;
    assert(!af_v3_goods_single_angle(0));
    RoomRigGame game={0};float position[3]={20.f,40.f,60.f};
    assert(!af_v3_goods_single(&game,0x22FF,position,.01f,1));
    RoomGoodsClip clip={.single_draw=draw};af_test_room_goods_clip=&clip;expected_angle=12345;
    assert(af_v3_goods_single(&game,0x22FF,position,.01f,expected_angle));
    assert(draw_calls==2 && !af_v3_goods_single_angle(0) && !af_test_room_goods.single_active);
    assert(!af_v3_goods_single(NULL,0x22FF,position,.01f,1));
    assert(!af_v3_goods_single(&game,0x22FF,NULL,.01f,1));
    drop_x=4;drop_z=9;drop_item=0xFFFF;drop_point=(RoomGoodsPoint){10.f,30.f,50.f};
    af_v3_goods_set(drop_z,drop_x,1,expected_angle);
    af_v3_goods_drop_fg(drop_item,drop_point,drop_x,drop_z);
    assert(fg_calls==1 && !af_v3_goods_get(drop_z,drop_x,1));
    af_v3_goods_destruct(&other);assert(destroy_calls==1 && af_test_room_goods.magic==ROOM_GOODS_MAGIC);
    af_v3_goods_destruct(&owner);assert(destroy_calls==2 && !af_test_room_goods.magic && !af_test_room_goods.owner);
    assert(!af_v3_goods_single(&game,0x22FF,position,.01f,1));
    af_test_room_goods_clip=NULL;assert(af_v3_goods_ctor(&owner)==34);
    for (int z=0;z<16;z++) for (int x=0;x<16;x++) assert(!af_v3_goods_get(z,x,1));
    af_v3_goods_destruct(&owner);assert(destroy_calls==3 && !af_test_room_goods.magic);
    const unsigned failures[]={0,1,2,5,6};
    for (unsigned i=0;i<sizeof(failures)/sizeof(*failures);i++) for (int result=0;result<2;result++) {
        stage=0;fail_stage=failures[i];init_calls=0;init_result=result;af_test_goods_magic=ROOM_GOODS_MAGIC;
        assert(af_v3_surface_init()==(fail_stage ? 0 : result));
        assert(stage==(fail_stage ? fail_stage : 9));
        assert(init_calls==!fail_stage && af_test_goods_magic==(fail_stage ? ROOM_GOODS_MAGIC : 0));
    }
    printf("%u donor grid comparisons; all 34 categories, scoped drawing, drop, lifetime, and startup checks pass\n",comparisons);
    return 0;
}
