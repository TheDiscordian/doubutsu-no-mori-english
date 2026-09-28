#ifndef AF_V3_HOLIDAY_SCENE_NATIVE_H
#define AF_V3_HOLIDAY_SCENE_NATIVE_H
#include "holiday_transition.h"
/* Live state shared by every scheduled holiday transition. The caller still
 * supplies its checked identity/status graph; these are not fabricated gates. */
int af_holiday_scene_read(void *,AFHolidayTransition *);
void af_holiday_scene_commit(void *,const AFHolidayTransition *,unsigned int);
void af_holiday_scene_tempo(void *);
void af_holiday_scene_climate(void *,int);
int af_holiday_scene_bind(AFHolidayTransitionServices *);
#endif
