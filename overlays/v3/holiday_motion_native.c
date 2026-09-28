/* Unexported NPC helpers are relative to the live, validated outdoor clip.
 * Never retain an overlay's link-time address after it relocates. */
#include "holiday_motion.h"
#ifndef __mips__
#error Native motion bindings require the checked o32 target
#endif
typedef unsigned int u32;
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))(at))
static u32 entry(u32 at) {
    return (*(const u32 *const *)0x80136EECu)[0x108/4]+at-0x8097F0BCu;
}
void af_holiday_wander_original(void *a) {FN(entry(0x8097D8C8),void,void *)(a);}
void af_holiday_wander_init_original(void *a,void *g) {FN(entry(0x8097DB60),void,void *,void *)(a,g);}
int af_holiday_fatigue(void *a) {return FN(entry(0x8097CBD0),int,void *)(a);}
int af_holiday_mood(void *a) {return FN(entry(0x80974184),int,void *)(a);}
int af_holiday_move_next(unsigned short *p,void *a) {return FN(entry(0x8097D520),int,unsigned short *,void *)(p,a);}
int af_holiday_ones_way(void *a,unsigned short *p) {return FN(entry(0x8097D460),int,void *,unsigned short *)(a,p);}
int af_holiday_range(void *a,void *b,AFHolidayPosition p,unsigned char type) {
    return FN(entry(0x80976F74),int,void *,void *,AFHolidayPosition,unsigned char)(a,b,p,type);
}
int af_holiday_request_native(void *a,unsigned char priority,unsigned char action,unsigned char type,unsigned short *p) {
    return FN(entry(0x8097BF90),int,void *,unsigned char,unsigned char,unsigned char,unsigned short *)(a,priority,action,type,p);
}
void af_holiday_schedule_native(void *a,void *g,unsigned char type) {
    FN(entry(0x8097F0BC),void,void *,void *,unsigned char)(a,g,type);
}
