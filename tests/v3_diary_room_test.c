#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_goods.c"
#include "goods_config.inc"

RoomGoodsState af_test_room_goods;
RoomGoodsClip *af_test_room_goods_clip;
static _Alignas(16) u8 memory[0x10000], before[0x10000];
static RoomGoodsOverlay overlay={AF_GOODS_VROM,0,0x80962A20,0,memory};
static RoomGoodsActor owner={.overlay=&overlay};
static unsigned flushes,counts,destructs,draws;
static jmp_buf failure;
static int expecting_failure;

void af_v3_save_halt(int result) {
    assert(expecting_failure && result==-1);longjmp(failure,1);
}
void af_goods_writeback(void *p,u32 n) {
    assert(p==memory+model_config[6] && n==model_config[7]-model_config[6]);flushes++;
}
int af_test_goods_count(u8 *p) {
    assert(p==memory+0x9C4 && flushes==counts+1);counts++;return AF_GOODS_ROW_COUNT;
}
void af_test_goods_destroy(u8 *p,RoomGoodsActor *o) {
    assert(p==memory+0x338 && o==&owner);destructs++;
}
void af_goods_fg2(u16 item,RoomGoodsPoint position) {(void)item;(void)position;}
static void draw(RoomRigGame *g,u16 item,const float *p,float scale) {
    assert(g && item==0x2B10 && p && scale==1.f);draws++;
    for(int i=0;i<50;i++) {
        u32 bits=i<32 ? AF_GOODS_ROTATE_LOW : AF_GOODS_ROTATE_HIGH;
        assert(af_v3_goods_single_angle(i)==((bits>>(i<32 ? i : i-32))&1 ? 2345 : 0));
    }
    assert(!af_v3_goods_single_angle(50) && !af_v3_goods_single_angle(-1));
}

int main(void) {
    overlay.vram_end=overlay.vram_start+model_config[3];
    memset(memory,0xA5,sizeof(memory));
    for(u32 i=0;i<model_config[2];i++) {
        const u32 *r=model_config+8+i*3;memcpy(memory+r[0],&r[1],4);
    }
    memcpy(before,memory,sizeof(memory));
    assert(!af_v3_goods_ctor(0));
    assert(af_v3_goods_ctor(&owner)==50 && counts==1);
    for(u32 i=0;i<model_config[2];i++) {
        const u32 *r=model_config+8+i*3;u32 value=((u32)(uptr)memory&0x1FFFFFFF)+r[2];
        assert(*(u32 *)(memory+r[0])==value);memcpy(before+r[0],&value,4);
    }
    assert(!memcmp(before,memory,sizeof(memory)));
    assert(af_v3_goods_ctor(&owner)==50 && counts==2); /* Repeated init is safe. */
    assert(!memcmp(before,memory,sizeof(memory)));
    for(int row=34;row<50;row++) for(int rotation=0;rotation<4;rotation++) {
        s16 angle=(s16)(rotation*0x4000);
        af_v3_goods_set(3,7,1,angle);
        RoomGoodsRow *r=(RoomGoodsRow *)(memory+AF_GOODS_TABLE_OFFSET+row*20);
        assert(af_v3_goods_grid_angle(&owner,7,3,1,r)==angle);
        assert(!af_v3_goods_grid_angle(&owner,7,3,0,r));
    }
    assert(!af_v3_goods_grid_angle(&owner,7,3,1,(RoomGoodsRow *)(memory+AF_GOODS_TABLE_OFFSET+50*20)));
    RoomGoodsClip clip={.single_draw=draw};af_test_room_goods_clip=&clip;
    RoomRigGame game={0};float p[3]={0};
    assert(af_v3_goods_single(&game,0x2B10,p,1.f,2345) && draws==1);
    assert(!af_v3_goods_single_angle(34));
    af_v3_goods_destruct(&owner);
    assert(destructs==1 && !af_test_room_goods.magic && !af_test_room_goods.owner);
    /* Corrupt dimensions, source words, and resource bounds reject before count. */
    const u32 fields[]={0,2,3,4,5,6,7,8,9,10};
    const u32 invalid[]={0,321,0x10001,0,0,0,0,1,0,0x10000};
    expecting_failure=1;
    for(u32 i=0;i<sizeof(fields)/sizeof(*fields);i++) {
        u32 field=fields[i],saved=model_config[field];model_config[field]=invalid[i];
        if(!setjmp(failure)) {af_v3_goods_ctor(&owner);assert(0);}
        model_config[field]=saved;
    }
    *(u32 *)(memory+model_config[8])=0;
    if(!setjmp(failure)) {af_v3_goods_ctor(&owner);assert(0);}
    assert(counts==2 && flushes==2);
    puts("Current model fixups, retained bytes, all 16 covers and rotations, scoped draws, and failure gates pass");
    return 0;
}
