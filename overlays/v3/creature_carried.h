/* Additional carried creatures share the complete insect lifecycle. These
 * platform services require real native/event bindings before installation. */
#ifndef AF_V3_CREATURE_CARRIED_H
#define AF_V3_CREATURE_CARRIED_H
#include "creature_insects.h"

typedef struct {
    struct { u8 block_x[5],block_z[5]; } hitodama_block_data;
    u16 flags;
    u8 reserved[32];
} AfSpiritCommon;
_Static_assert(sizeof(AfSpiritCommon)==44,"complete spirit event common storage");
AfSpiritCommon *af_carried_spirit_common(void);
int af_carried_spirit_running(void);
void af_carried_spirit_event_bind(AfSpiritCommon *,const volatile u16 *);
void *af_carried_insect_light_context(GAME *);
u32 af_carried_game_frame(const GAME *);
f32 search_position_distanceXZ(const xyz_t *,const xyz_t *);
s16 search_position_angleY(const xyz_t *,const xyz_t *);
f32 af_carried_absf(f32),sqrtf(f32);
void add_calc_short_angle2(s16 *,s16,f32,s16,s16);
void Light_point_ct(AfInsectPointLight *,s16,s16,s16,u8,u8,u8,s16);
void *Global_light_list_new(GAME *,void *,AfInsectPointLight *);
void Global_light_list_delete(void *,void *);
#endif
