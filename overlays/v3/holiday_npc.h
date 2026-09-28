#ifndef AF_V3_HOLIDAY_NPC_H
#define AF_V3_HOLIDAY_NPC_H
#include "holiday_actor.h"

/* Native profile allocation must cover this entire object. The original NPC
 * prefix is preserved; none of the donor's 0x994-based fields is reused. */
typedef struct {
    unsigned int npc[0x93C/4];
    void *game;
    unsigned int constructed,failed;
    AFHolidayActor actor;
    AFHolidayActorOps ops;
    AFHolidayWorld world;
} AFHolidayNpc;
extern const unsigned int af_holiday_npc_bytes;
typedef struct {
    AFDiaryDates dates;
    /* Both callbacks receive this AFHolidayNpc, as do the shared world ops. */
    int (*lighthouse_after)(void *);
    void (*lighthouse_start)(void *);
} AFHolidayEventWorld;

/* Required installation services, deliberately unresolved until their complete
 * resources and event owner are installed. The binding fills the remaining ops
 * (event/field/variant, shrine/runner, walking-only schedule, animations/sound,
 * RNG, message/demo transport, and conditional melody restoration). It also
 * validates the actual outdoor clip, complete allocated actor size, selected
 * profile, full voice, and cane resources before native construction. */
int af_holiday_npc_bind(AFHolidayNpc *);
/* Event ownership supplies real dates/vacation state; the native world adapter
 * supplies player identity, inventory, diary storage, and trophy receipts. */
int af_holiday_npc_event_world(AFHolidayNpc *,AFHolidayEventWorld *);
int af_holiday_npc_world(AFHolidayNpc *,AFHolidayWorld *,unsigned int *gender);
int af_holiday_npc_resources(AFHolidayNpc *); /* apply voice/cane after native ctor */
void af_holiday_npc_unregister(AFHolidayNpc *);
int af_holiday_npc_continue(AFHolidayNpc *); /* actual MainNormalContinue */
int af_holiday_dialogue_bind(AFHolidayNpc *);

void af_holiday_npc_ctor(AFHolidayNpc *,void *);
void af_holiday_npc_dtor(AFHolidayNpc *,void *);
void af_holiday_npc_init(AFHolidayNpc *,void *);
void af_holiday_npc_move(AFHolidayNpc *,void *);
void af_holiday_npc_draw(AFHolidayNpc *,void *);
void af_holiday_npc_save(AFHolidayNpc *,void *);
void af_holiday_npc_schedule(AFHolidayNpc *,void *,int);
void af_holiday_npc_think(AFHolidayNpc *,void *,int);
void af_holiday_npc_request(AFHolidayNpc *,void *);
void af_holiday_npc_prepare(AFHolidayNpc *);
int af_holiday_npc_start(AFHolidayNpc *,void *);
int af_holiday_npc_end(AFHolidayNpc *,void *);
#endif
