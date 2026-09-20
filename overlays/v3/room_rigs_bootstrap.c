#include "room_rigs.h"
extern int af_room_dma(void *,u32,u32);
extern u32 af_room_crc(void *,u32);
extern void af_room_writeback(void *,u32);
extern void af_room_invalidate(void *,u32);
extern void af_room_fault(const char *,const char *);

static int load(void) {
    /* Startup reloads this cache word, even when Expansion Pak RAM survives a reset. */
    volatile u32 *ready=(volatile u32 *)0x804B1E00u;
    void *packet=(void *)0x804B8000u;
    if (*ready==AF_ROOM_CRC) return 1;
    if (af_room_dma(packet,AF_ROOM_VROM,AF_ROOM_BYTES) ||
            af_room_crc(packet,AF_ROOM_BYTES)!=AF_ROOM_CRC) {
        af_room_fault("V3 room rigs","Invalid room code");return 0;
    }
    af_room_writeback(packet,AF_ROOM_BYTES);
    af_room_invalidate(packet,AF_ROOM_BYTES);
    *ready=AF_ROOM_CRC;
    return 1;
}
void af_v3_room_boot_ct(RoomRig *actor,u8 *data) {
    if (load()) ((void (*)(RoomRig *,u8 *))AF_ROOM_CT)(actor,data);
}
void af_v3_room_boot_mv(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    if (load()) ((void (*)(RoomRig *,void *,RoomRigGame *,u8 *))AF_ROOM_MV)(actor,room,game,data);
}
void af_v3_room_boot_dw(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    if (load()) ((void (*)(RoomRig *,void *,RoomRigGame *,u8 *))AF_ROOM_DW)(actor,room,game,data);
}
#ifdef AF_ROOM_SOUND_MV
void af_v3_room_boot_sound_mv(void *actor,void *room,RoomRigGame *game,u8 *data) {
    if (load()) ((void (*)(void *,void *,RoomRigGame *,u8 *))AF_ROOM_SOUND_MV)(actor,room,game,data);
}
#endif
#ifdef AF_ROOM_MATERIAL_DW
void af_v3_room_boot_material_dw(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    if (load()) ((void (*)(RoomRig *,void *,RoomRigGame *,u8 *))AF_ROOM_MATERIAL_DW)(actor,room,game,data);
}
#endif
