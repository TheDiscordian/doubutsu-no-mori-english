#ifndef AF_V3_ROOM_GOODS_H
#define AF_V3_ROOM_GOODS_H
#include "room_rigs.h"

#define ROOM_GOODS_MAGIC 0x41464731u
#define ROOM_GOODS_STATE_RAM 0x804DC000u
typedef struct {u32 vrom_start,vrom_end,vram_start,vram_end;u8 *loaded;} RoomGoodsOverlay;
typedef struct {u8 prefix[0x170];RoomGoodsOverlay *overlay;} RoomGoodsActor;
typedef struct {float x,y,z;} RoomGoodsPoint;
typedef struct {
    u32 magic;
    RoomGoodsActor *owner;
    s16 angles[16][16];
    s16 single_angle;
    u16 single_active;
} RoomGoodsState;
typedef struct {u16 first,last;u32 models[4];} RoomGoodsRow;
typedef struct {
    void (*single_draw)(RoomRigGame *,u16,const float *,float);
    void *drop;
} RoomGoodsClip;
#ifdef __mips__
#define room_goods_state ((RoomGoodsState *)ROOM_GOODS_STATE_RAM)
#define room_goods_clip (*(RoomGoodsClip *volatile *)0x80136F58u)
ROOM_CHECK(RoomGoodsActor,overlay,0x170);
_Static_assert(sizeof(RoomGoodsState)==524,"Loose-item angle state");
#else
extern RoomGoodsState af_test_room_goods;
extern RoomGoodsClip *af_test_room_goods_clip;
#define room_goods_state (&af_test_room_goods)
#define room_goods_clip af_test_room_goods_clip
#endif
_Static_assert(sizeof(RoomGoodsRow)==20,"Native loose-item category stride");

int af_v3_goods_ctor(RoomGoodsActor *);
void af_v3_goods_destruct(RoomGoodsActor *);
s16 af_v3_goods_get(int,int,int);
void af_v3_goods_set(int,int,int,s16);
void af_v3_goods_drop_fg(u16,RoomGoodsPoint,int,int);
s16 af_v3_goods_single_angle(int);
s16 af_v3_goods_grid_angle(RoomGoodsActor *,int,int,int,const RoomGoodsRow *);
int af_v3_goods_single(RoomRigGame *,u16,const float *,float,s16);
#endif
