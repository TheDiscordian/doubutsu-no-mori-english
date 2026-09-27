/* Shared owner paths: native stereos and imported radios use the same state. */
#include "room_music_native.h"
#ifndef AF_ROOM_RADIO_SONG
#error The complete source/native song binding is required
#endif
static u8 *owner_base(RoomMusicOwner *owner) {
    RoomGoodsOverlay *o=owner ? owner->actor.overlay : 0;
    if (!o || o->vrom_start!=0x82D7F0u || o->vram_start!=0x80936710u ||
            o->vram_end<0x8094F610u || !o->loaded) return 0;
    return o->loaded;
}
static void *resolved(u8 *base,u32 address) {
#ifdef __mips__
    return base+(address-0x80936710u);
#else
    return af_test_music_resolve(base,address);
#endif
}
void af_v3_room_music_native_apply(RoomMusicOwner *owner,RoomRig *actor) {
    if (owner_base(owner)) af_v3_room_music_apply(&owner->music,actor,AF_ROOM_RADIO_SONG);
}
void af_v3_room_music_native_disk_dt(RoomRig *actor,RoomMusicOwner *owner) {
    if (!owner_base(owner) || !actor || actor->index>=AF_V3_FURNITURE_CAPACITY) return;
    RoomMusicProfile *profile=room_music_profiles[actor->index];
    if (profile && (profile->interaction&8))
        af_v3_room_music_disk_dt(actor,&owner->music,AF_ROOM_RADIO_SONG);
}
void af_v3_room_music_native_move(RoomRig *actor,RoomMusicOwner *owner) {
    u8 *base=owner_base(owner);
    if (!base || !actor) return;
    af_v3_room_radio_move(actor,&owner->music,AF_ROOM_RADIO_SONG,
        (void (*)(RoomRig *))resolved(base,0x809385E4u));
}
void af_v3_room_music_native_radio_dt(RoomRig *actor) {
    RoomMusicClip *clip=room_music_clip;RoomMusicOwner *owner=clip ? clip->owner : 0;
    if (actor && owner_base(owner)) af_v3_room_radio_dt(actor,&owner->music,AF_ROOM_RADIO_SONG);
}
