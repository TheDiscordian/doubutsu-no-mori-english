/* Source-derived console bindings reuse the complete native interaction flow. */
#include "room_rigs.h"
#include "sparse_furniture.h"
#ifdef __mips__
#define MEMORY(at) ((void *)(at))
#else
extern void *af_console_room_memory(u32);
#define MEMORY(at) af_console_room_memory(at)
#endif
typedef struct {u16 index;u8 game,ready;u32 reserved;} Row;
typedef struct {u32 magic,count,stride,reserved;Row rows[19];} Table;
typedef void (*Move)(RoomRig *,void *,void *,u32);
typedef struct {void *owner;u8 padding[0x54-sizeof(void *)];Move move;} Clip;
_Static_assert(__builtin_offsetof(Clip,move)==0x54 || sizeof(void *)!=4,"Console clip offset");

void af_v3_console_room_move(RoomRig *actor,void *room,void *game,void *data) {
    (void)data;
    const Table *table=MEMORY(0x804FC000u);
    if(!actor || !room || !game || !actor->changed || table->magic!=0x41464352u ||
       table->count>19 || table->stride!=sizeof(Row) || table->reserved)return;
    u32 index=actor->index;
    if(index>=2048 && index<3072)index-=1024;
    if(index<1024 || index>=2048)return;
    for(u32 i=0;i<table->count;i++) {
        const Row *r=&table->rows[i];
        if(r->index!=index)continue;
        if(!r->ready || r->ready!=1 || r->game<8 || r->game>19 || r->reserved)return;
        const u32 *profile=MEMORY(AF_V3_STATIC_IMPORT_RAM+(index-1024)*80);
        if(profile[0]!=(index<<16 | (0x2000u+index*4)) || profile[1]!=1 ||
           profile[18]!=0x804FC7E0u)return;
        Clip *clip=*(Clip **)MEMORY(0x80136F2Cu);
        if(clip && clip->owner==room && clip->move)clip->move(actor,room,game,r->game);
        return;
    }
}
