#ifndef AF_V3_HOLIDAY_OBSERVERS_H
#define AF_V3_HOLIDAY_OBSERVERS_H
#include "holiday_npc.h"

/* Native adapters are also the seam for the bounded connected host check. */
int af_holiday_observers_clip(void);
int af_holiday_observers_shrine(short [3]);
const unsigned char *af_holiday_observers_save(int type,int id);
void *af_holiday_observers_find(void *game,short profile,int part);
void af_holiday_observers_delete(void *actor);
/* Validate metadata before dereferencing a relocated native clip. */
unsigned int af_holiday_observers_clip_address(const unsigned int descriptor[8]);
int af_holiday_observers_clip_entries(unsigned int base,const unsigned int *clip);
#endif
