#ifndef AF_V3_HOLIDAY_SCENE_H
#define AF_V3_HOLIDAY_SCENE_H
/* Full donor event-to-announcement mapping. Returns zero for an event without
 * a title, -1 for a malformed packet, or the complete native message ID. */
int af_holiday_scene_message(const unsigned char *,unsigned int,unsigned int donor,unsigned int title_flags);
/* Replace the native initializer's function-table pointer, not its entry:
 * original door copy, colour, camera, timers, and original-event messages stay. */
int af_holiday_scene_demo_init(void);
#endif
