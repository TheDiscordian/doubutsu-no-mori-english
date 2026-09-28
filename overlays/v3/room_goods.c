/* Native loose-item rotation, with flags compiled from donor categories. */
#include "room_goods.h"
#if !defined(AF_GOODS_ROTATE_LOW) || !defined(AF_GOODS_ROTATE_HIGH)
#error Missing checked native category rotation flags
#endif
extern void af_goods_fg2(u16,RoomGoodsPoint);
#ifndef AF_GOODS_TABLE_OFFSET
#define AF_GOODS_TABLE_OFFSET 0xFB0u
#define AF_GOODS_ROW_COUNT 34u
#define AF_GOODS_VROM 0x8576C0u
#endif

static u8 *owner_base(RoomGoodsActor *owner) {
    RoomGoodsOverlay *o=owner ? owner->overlay : 0;
    if (!o || o->vrom_start!=AF_GOODS_VROM || o->vram_start!=0x80962A20u ||
            o->vram_end<0x80963CD0u || !o->loaded) return 0;
    return o->loaded;
}

static RoomGoodsState *live(void) {
    RoomGoodsState *state=room_goods_state;
    return state->magic==ROOM_GOODS_MAGIC && state->owner ? state : 0;
}

#ifdef AF_DIARY_GOODS
/* Model resources stay unchanged in ROM for normal catalogue DMA. Only this
 * loaded room owner's display-list pointers become physical RDRAM pointers. */
#ifdef __mips__
#define model_config ((const u32 *)0x806E3000u)
#else
extern u32 af_test_goods_model_config[];
#define model_config af_test_goods_model_config
#endif
extern void af_goods_writeback(void *,u32);
extern void af_v3_save_halt(int) __attribute__((noreturn));
static void models(u8 *base) {
    const u32 *c=model_config;
    if(c[0]!=0x41464452u || c[1]!=1 || c[2]>320 || c[3]>0x10000u ||
       c[4]!=AF_GOODS_TABLE_OFFSET || c[5]!=AF_GOODS_ROW_COUNT ||
       c[6]<c[4]+(c[5]+1)*20u || c[7]>c[3] || c[6]>=c[7])af_v3_save_halt(-1);
    for(u32 i=0;i<c[2];i++) {
        const u32 *r=c+8+i*3;
        if((r[0]&3u) || r[0]<c[6] || r[0]>c[7]-4 ||
           r[1]>>24!=6 || r[2]<c[6] || r[2]>=c[7])af_v3_save_halt(-1);
        u32 target=((u32)(uptr)base&0x1FFFFFFFu)+r[2];
        u32 *word=(u32 *)(base+r[0]);
        if(*word!=r[1] && *word!=target)af_v3_save_halt(-1);
        *word=target;
    }
    af_goods_writeback(base+c[6],c[7]-c[6]);
}
#endif

int af_v3_goods_ctor(RoomGoodsActor *owner) {
    u8 *base=owner_base(owner);
    if (!base) return 0;
#ifdef AF_DIARY_GOODS
    if(owner->overlay->vram_end!=0x80962A20u+model_config[3])af_v3_save_halt(-1);
    models(base);
#endif
    /* Preserve the original category-count operation and initialise only this
       overlay lifetime's transient angles. No save fields are allocated. */
#ifdef __mips__
    int count=((int (*)(void))(base+0x9C4))();
#else
    extern int af_test_goods_count(u8 *);
    int count=af_test_goods_count(base+0x9C4);
#endif
    RoomGoodsState *state=room_goods_state;
    *state=(RoomGoodsState){.owner=owner};state->magic=ROOM_GOODS_MAGIC;
    return count;
}

void af_v3_goods_destruct(RoomGoodsActor *owner) {
    /* Preserve dropped-object restoration, and clear state even when native
       clip allocation failed. The caller retains its original clip free. */
    u8 *base=owner_base(owner);
    if (base) {
#ifdef __mips__
        ((void (*)(RoomGoodsActor *))(base+0x338))(owner);
#else
        extern void af_test_goods_destroy(u8 *,RoomGoodsActor *);
        af_test_goods_destroy(base+0x338,owner);
#endif
    }
    if (room_goods_state->owner==owner) {
        room_goods_state->magic=0;room_goods_state->owner=0;
    }
}

s16 af_v3_goods_get(int z,int x,int layer) {
    RoomGoodsState *state=live();
    return state && layer==1 && x>=0 && x<16 && z>=0 && z<16 ? state->angles[z][x] : 0;
}

void af_v3_goods_set(int z,int x,int layer,s16 angle) {
    RoomGoodsState *state=live();
    if (state && layer==1 && x>=0 && x<16 && z>=0 && z<16) state->angles[z][x]=angle;
}

void af_v3_goods_drop_fg(u16 item,RoomGoodsPoint position,int x,int z) {
    af_goods_fg2(item,position);
    af_v3_goods_set(z,x,1,0);
}

static int rotating(int row) {
    if (row<0 || (u32)row>=AF_GOODS_ROW_COUNT) return 0;
    return row<32 ? ((AF_GOODS_ROTATE_LOW>>row)&1u) : ((AF_GOODS_ROTATE_HIGH>>(row-32))&1u);
}

s16 af_v3_goods_single_angle(int row) {
    RoomGoodsState *state=live();
    return state && state->single_active && rotating(row) ? state->single_angle : 0;
}

s16 af_v3_goods_grid_angle(RoomGoodsActor *owner,int x,int z,int layer,const RoomGoodsRow *row) {
    RoomGoodsState *state=live();
    if (!state || state->owner!=owner || layer!=1 || !row) return 0;
    u8 *base=owner_base(owner);
    uptr first=(uptr)base+AF_GOODS_TABLE_OFFSET,at=(uptr)row;
    if (!base || at<first || at>=first+AF_GOODS_ROW_COUNT*sizeof(*row) || (at-first)%sizeof(*row)) return 0;
    return rotating((int)((at-first)/sizeof(*row))) ? af_v3_goods_get(z,x,layer) : 0;
}

int af_v3_goods_single(RoomRigGame *game,u16 item,const float *position,float scale,s16 angle) {
    RoomGoodsState *state=live();RoomGoodsClip *clip=room_goods_clip;
    if (!state || !clip || !clip->single_draw || !game || !position) return 0;
    /* Scope the angle to this one complete native draw. Other single-object
       callers, including dropped-item animations, retain their native pose. */
    s16 previous=state->single_angle;u16 active=state->single_active;
    state->single_angle=angle;state->single_active=1;
    clip->single_draw(game,item,position,scale);
    state->single_angle=previous;state->single_active=active;
    return 1;
}
