#include "room_static.h"

int af_v3_room_static_mv(RoomSoundActor *actor,void *room) {
    const RoomStaticTable *table=&af_v3_room_static_table;
    if (!actor || table->magic!=0x41464931u || table->count>128 ||
            table->stride!=8 || table->reserved) return 0;
    u32 index=actor->index;
    if (index>=2048 && index<3072) index-=1024;
    for (u32 i=0;i<table->count;++i) {
        const RoomStaticRecord *r=table->rows+i;
        if (r->index!=index) continue;
        if (r->reserved) return 1;
        if (r->mode==1 && r->parameter==1) {
            RoomPrivateWallet *player=room_static_private;
            /* The donor accepts every nonzero pulse and has no state gate. */
            if (actor->changed && player && player->wallet) {
                sAdo_OngenTrgStart(r->sound,actor->position);
                --player->wallet;
            }
        } else if (r->mode==2 && r->parameter<16 && !r->sound) {
            RoomStaticClip *clip=room_static_clip;
            /* Native melody handles the press and refreshes position even
               when there is no new press. Do not apply the trigger gate. */
            if (clip && clip->melody) clip->melody(actor,room,r->parameter);
        }
        return 1;
    }
    return 0;
}
