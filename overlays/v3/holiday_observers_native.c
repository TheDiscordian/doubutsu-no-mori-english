#include "holiday_observers.h"
#ifndef __mips__
#error Native observer bindings require the checked o32 target
#endif
extern const unsigned int af_holiday_npc_descriptor[8];
extern const unsigned int *volatile af_holiday_native_clip;
extern void *af_holiday_native_find(void *,short,int);
int af_holiday_observers_clip(void) {
    unsigned int at=af_holiday_observers_clip_address(af_holiday_npc_descriptor);
    if(!at || (unsigned int)af_holiday_native_clip!=at)return 0;
    return af_holiday_observers_clip_entries(af_holiday_npc_descriptor[4],af_holiday_native_clip);
}
void *af_holiday_observers_find(void *game,short profile,int part) {
    return game?af_holiday_native_find((unsigned char *)game+0x1C78,profile,part):0;
}
