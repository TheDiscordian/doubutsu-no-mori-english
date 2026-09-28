/* GAFE01 surface interaction, preserving the native N64 hold/move controller. */
#include "diary_room.h"
#include "diary_items.h"

int af_diary_on_surface(const RoomRig *actor,const u16 *fg,const u8 *layers,
    u32 capacity,u16 selected,const float player[3]) {
    if(!actor || !fg || !layers || !player || actor->layer || actor->index>=capacity ||
       layers[actor->index]!=1 || !(player[0]>=0 && player[0]<640 && player[2]>=0 && player[2]<640))return 0;
    int cells[4],count=af_v3_room_carry_cells(cells,actor->position,actor->shape_type);
    for(int i=0;i<count;i++) {
        u16 item=fg[cells[i]];
        if(item<AF_DIARY_ITEM_FIRST || item>=AF_DIARY_ITEM_FIRST+AF_DIARY_ITEM_COUNT ||
           !(selected&(1u<<(item-AF_DIARY_ITEM_FIRST))))continue;
        float dx=(cells[i]&15)*40.0f+20.0f-player[0];
        float dz=(cells[i]>>4)*40.0f+20.0f-player[2];
        /* Donor uses OR: the player stands beside one edge, not inside a 12px
         * circle around the centre of the occupied table cell. */
        if((dx>-12 && dx<12) || (dz>-12 && dz<12))return 1;
    }
    return 0;
}
int af_diary_room_tap(const RoomCarryWork *work,const AFDiaryContact *lower,
    const AFDiaryContact *upper,const u16 *fg,const u8 *layers,
    RoomCarryProfile *const *profiles,u32 capacity,u16 selected,const float player[3]) {
    if(!work || !work->actors || !work->used || !profiles || work->count<1 || work->count>48)return 0;
    const AFDiaryContact *contacts[2]={upper,lower};
    for(int i=0;i<2;i++) {
        const AFDiaryContact *c=contacts[i];
        if(!c || c->flag!=1 || c->id<0 || c->id>=work->count || !work->used[c->id])continue;
        RoomRig *a=work->actors+c->id;
        if(a->id!=c->id || a->index>=capacity || !profiles[a->index])continue;
        if(af_diary_on_surface(a,fg,layers,capacity,selected,player))return 1;
    }
    return 0;
}
static void *core(u32 address) {
#ifdef __mips__
    return (void *)address;
#else
    return af_test_diary_resolve(address);
#endif
}
static void *room(u8 *base,u32 address) {
#ifdef __mips__
    return base+(address-0x80936710u);
#else
    (void)base;return af_test_diary_resolve(address);
#endif
}
static int owner(void) {
    u16 field=((u16 (*)(void))core(0x80087C88))();
    if(field<0x6000 || field>0x6003)return -1;
#ifdef __mips__
    u8 *houses=(u8 *)0x8012A428;
#else
    u8 *houses=af_test_diary_houses;
#endif
    if(!houses)return -1;
    void *id=houses+(field-0x6000)*0xB48;
    if(((int (*)(void *))core(0x800B7914))(id))return -1;
    int player=((int (*)(void *))core(0x800B7FD4))(id);
    return player>=0 && player<4?player:-1;
}
int af_diary_room_move(RoomCarryOwner *actor,void *game,AFDiaryContact *lower,AFDiaryContact *upper) {
#ifdef __mips__
    RoomGoodsOverlay *o=actor?actor->overlay:0;
#else
    /* Native pointer at +170 is four bytes, immediately before the state.
     * A host eight-byte pointer cannot be overlaid on those native fields. */
    RoomGoodsOverlay *o=actor?af_test_diary_owner_overlay:0;
#endif
    if(!o || o->vrom_start!=0x82D7F0 || o->vram_start!=0x80936710 ||
       o->vram_end<0x8094F610 || !o->loaded)return 0;
    u8 *a=(u8 *)actor,*base=o->loaded;
    u16 selected=af_diary_native_selected();
    /* These are the existing native A-release gates. Seven N64 updates equal
     * the source's fourteen 60 Hz updates; do not lengthen furniture holding. */
    int state=*(s16 *)(a+0x174);
    if(selected && *(int *)(a+0x4D8)!=1 && *(s16 *)(a+0x4CE)!=1 &&
       !*(s16 *)(a+0x3F0) && !*(s16 *)(a+0x3E8) && (state==1 || state==6) &&
       *(s16 *)(a+0x4CC)>=0 && *(s16 *)(a+0x4CC)<7 &&
       !((int (*)(u16))core(0x80078D30))(0x8000)) {
#ifdef __mips__
        RoomCarryWork *work=(RoomCarryWork *)(base+0x10E50);
        const u8 *layers=(const u8 *)0x80474200;
#else
        RoomCarryWork *work=&af_test_carry_work;
        const u8 *layers=af_test_diary_layers;
#endif
        u16 *fg=((u16 *(*)(s16))room(base,0x80936A10))(1);
        u8 *player=((u8 *(*)(void *))core(0x800B1C84))(game);
        if(player && af_diary_room_tap(work,lower,upper,fg,layers,carry_profiles,
            AF_V3_FURNITURE_CAPACITY,selected,(const float *)(player+0x28))) {
            int resident=owner();
            if(resident>=0 && af_diary_native_open(game,resident)) {
                *(s16 *)(a+0x174)=0;return 1;
            }
            /* A diary owns this tap even if the house is vacant or menu
             * allocation fails. Do not accidentally activate its supporting TV. */
            *(s16 *)(a+0x174)=0;return 0;
        }
    }
    return ((int (*)(RoomCarryOwner *,void *,AFDiaryContact *,AFDiaryContact *))
        room(base,0x8093DB64))(actor,game,lower,upper);
}
