#include "room_rigs.h"
#ifdef AF_ROOM_REACTIONS
#include "room_reactions.h"
#endif
#ifdef AF_ROOM_COLOURS
#include "room_colours.h"
#endif
extern int af_room_dma(void *,u32,u32);
extern u32 af_room_crc(void *,u32);
extern void af_room_writeback(void *,u32);
extern void af_room_invalidate(void *,u32);
extern void af_room_fault(const char *,const char *);

#ifdef AF_ROOM_EFFECTS
int af_v3_room_boot_load(void) {
#define load af_v3_room_boot_load
#else
static int load(void) {
#endif
    /* Startup reloads this cache word, even when Expansion Pak RAM survives a reset. */
    volatile u32 *ready=(volatile u32 *)0x804B1E00u;
    void *packet=(void *)AF_ROOM_RAM;
    if (*ready==AF_ROOM_CRC) return 1;
    if (af_room_dma(packet,AF_ROOM_VROM,AF_ROOM_BYTES) ||
            af_room_crc(packet,AF_ROOM_BYTES)!=AF_ROOM_CRC) {
        af_room_fault("V3 room rigs","Invalid room code");return 0;
    }
    af_room_writeback(packet,AF_ROOM_BYTES);
    af_room_invalidate(packet,AF_ROOM_BYTES);
#ifdef AF_ROOM_REACTIONS
    /* Publish no callback until its separate mutable state is invalidated.
       The controller-side bridge checks the ready word before entering. */
    *(volatile u32 *)ROOM_REACTION_STATE_RAM=0;
#endif
#ifdef AF_ROOM_COLOURS
    *(volatile u32 *)ROOM_COLOUR_RAM=0;
#endif
    *ready=AF_ROOM_CRC;
    return 1;
}
typedef void (*RoomEntry2)(RoomRig *,u8 *);
typedef void (*RoomEntry4)(RoomRig *,void *,RoomRigGame *,u8 *);
/* Share argument preservation and checked loading across callback entries.
   Every entry, including destruction, still validates its resident packet. */
static __attribute__((noinline)) void call2(RoomRig *actor,u8 *data,RoomEntry2 entry,int (*loader)(void)) {
    if (loader()) entry(actor,data);
}
static __attribute__((noinline)) void call4(RoomRig *actor,void *room,RoomRigGame *game,u8 *data,
                                          RoomEntry4 entry,int (*loader)(void)) {
    if (loader()) entry(actor,room,game,data);
}
void af_v3_room_boot_ct(RoomRig *actor,u8 *data) {
    call2(actor,data,(RoomEntry2)AF_ROOM_CT,load);
}
#ifdef AF_ROOM_DT
void af_v3_room_boot_dt(RoomRig *actor,u8 *data) {
    call2(actor,data,(RoomEntry2)AF_ROOM_DT,load);
}
#endif
void af_v3_room_boot_mv(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    call4(actor,room,game,data,(RoomEntry4)AF_ROOM_MV,load);
}
#ifdef AF_ROOM_MOVE_ALLOWED
int af_v3_room_boot_move_allowed(const RoomRig *actor) {
    if (!actor) return 0;
    if (actor->state!=6 && actor->state!=13) return 1;
    if (!load()) return 0;
    return ((int (*)(const RoomRig *))AF_ROOM_MOVE_ALLOWED)(actor);
}
#endif
void af_v3_room_boot_dw(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    call4(actor,room,game,data,(RoomEntry4)AF_ROOM_DW,load);
}
#ifdef AF_ROOM_MUSIC_APPLY
/* These entries also serve original stereos before any imported draw callback. */
void af_v3_room_boot_music_apply(RoomRig *owner,u8 *actor) {
    call2(owner,actor,(RoomEntry2)AF_ROOM_MUSIC_APPLY,load);
}
void af_v3_room_boot_music_disk_dt(RoomRig *actor,u8 *owner) {
    call2(actor,owner,(RoomEntry2)AF_ROOM_MUSIC_DISK_DT,load);
}
#endif
#ifdef AF_ROOM_SOUND_MV
void af_v3_room_boot_sound_mv(void *actor,void *room,RoomRigGame *game,u8 *data) {
    call4(actor,room,game,data,(RoomEntry4)AF_ROOM_SOUND_MV,load);
}
#endif
#ifdef AF_ROOM_SCROLL_DW
static int load_scroll(void) {
    volatile u32 *ready=(volatile u32 *)0x804B1E04u;
    void *packet=(void *)0x804BA000u;
    if (*ready!=AF_ROOM_SCROLL_CRC) {
        if (af_room_dma(packet,AF_ROOM_SCROLL_VROM,AF_ROOM_SCROLL_BYTES) ||
                af_room_crc(packet,AF_ROOM_SCROLL_BYTES)!=AF_ROOM_SCROLL_CRC) {
            af_room_fault("V3 room materials","Invalid scroll code");return 0;
        }
        af_room_writeback(packet,AF_ROOM_SCROLL_BYTES);
        af_room_invalidate(packet,AF_ROOM_SCROLL_BYTES);
        *ready=AF_ROOM_SCROLL_CRC;
    }
    return 1;
}
void af_v3_room_boot_scroll_dw(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    call4(actor,room,game,data,(RoomEntry4)AF_ROOM_SCROLL_DW,load_scroll);
}
#ifdef AF_ROOM_SCROLL_CT
void af_v3_room_boot_scroll_ct(RoomRig *actor,u8 *data) {
    call2(actor,data,(RoomEntry2)AF_ROOM_SCROLL_CT,load_scroll);
}
void af_v3_room_boot_scroll_mv(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    call4(actor,room,game,data,(RoomEntry4)AF_ROOM_SCROLL_MV,load_scroll);
}
void af_v3_room_boot_scroll_dt(RoomRig *actor,u8 *data) {
    call2(actor,data,(RoomEntry2)AF_ROOM_SCROLL_DT,load_scroll);
}
#ifdef AF_ROOM_SCROLL_MOVE_SOUND
void af_v3_room_boot_scroll_move_sound(u32 floor,float *position) {
    if (load_scroll()) ((void (*)(u32,float *))AF_ROOM_SCROLL_MOVE_SOUND)(floor,position);
}
#endif
#endif
#endif
#ifdef AF_ROOM_MATERIAL_DW
void af_v3_room_boot_material_dw(RoomRig *actor,void *room,RoomRigGame *game,u8 *data) {
    call4(actor,room,game,data,(RoomEntry4)AF_ROOM_MATERIAL_DW,load);
}
#endif
