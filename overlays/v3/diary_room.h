#ifndef AF_V3_DIARY_ROOM_H
#define AF_V3_DIARY_ROOM_H
#include "room_carry_native.h"

/* The real native routine calls with lower/upper contacts. Only flag/id are
 * read; the remaining native contact fields retain their original layout. */
typedef struct {int flag,id;} AFDiaryContact;
int af_diary_on_surface(const RoomRig *,const u16 *foreground,const u8 *layers,
    u32 capacity,u16 selected,const float player_position[3]);
int af_diary_room_tap(const RoomCarryWork *,const AFDiaryContact *lower,
    const AFDiaryContact *upper,const u16 *foreground,const u8 *layers,
    RoomCarryProfile *const *profiles,u32 capacity,u16 selected,const float player_position[3]);
int af_diary_room_move(RoomCarryOwner *,void *game,AFDiaryContact *,AFDiaryContact *);
/* Bound by the connected native menu/selection packet, not stubbed at install. */
extern u16 af_diary_native_selected(void);
extern int af_diary_native_open(void *game,int owner);
#ifndef __mips__
extern void *af_test_diary_resolve(u32);
extern const u8 *af_test_diary_layers;
extern u8 *af_test_diary_houses;
extern RoomGoodsOverlay *af_test_diary_owner_overlay;
#endif
#endif
