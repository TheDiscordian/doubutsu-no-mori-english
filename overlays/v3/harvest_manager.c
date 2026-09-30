/* Complete source start/stop/in/behind callbacks with actual native placement.
 * The independent keep flag avoids the unextended native keep bit arrays. */
#include "harvest_manager.h"
#include "holiday_hiding.h"
typedef unsigned int u32;
extern AFHolidayPlace *af_holiday_native_get_place(int,unsigned char);
extern int af_hr_source_start(AFHarvestManagerView *,AFHolidayControl *);
extern int af_hr_source_stop(AFHarvestManagerView *,AFHolidayControl *);
extern int af_hr_source_in(AFHarvestManagerView *,AFHolidayControl *);
extern int af_hr_source_behind(AFHarvestManagerView *,AFHolidayControl *);
static u32 keep;
static int valid(const AFHolidayControl *c) {
    return c && c->type==AF_HR_NATIVE && af_hr_enabled_mask() &&
        af_hr_manager_native_check_status(AF_HR_NATIVE,AF_HE_EXIST) &&
        !af_hr_manager_native_check_status(AF_HR_NATIVE,AF_HE_ERROR);
}
static int view(void *manager,AFHarvestManagerView *out) {
    int seed;
    if(!manager || !af_holiday_hide_native_fluctuation(manager,&seed))return 0;
    /* Native schedule_init writes shrine coordinates 22C/230 and its separate
     * existence word 234. 228 belongs to the station, not the shrine. */
    *out=(AFHarvestManagerView){manager,((const int *)manager)[0x234/4]!=0};return 1;
}
int af_hr_manager_check_keep(int type) {
    if(type!=AF_HR_NATIVE)return 0;
    if(!af_holiday_native_get_place(type,0x51))keep=0;
    return keep!=0;
}
void af_hr_manager_set_keep(int type) {if(type==AF_HR_NATIVE)keep=1;}
void af_hr_manager_clear_keep(int type) {if(type==AF_HR_NATIVE)keep=0;}
AFHolidayPlace *af_hr_manager_make_hide(AFHarvestManagerView *m,AFHolidayControl *c,
        unsigned short name,int id) {
    if(!m || !valid(c) || name!=0xD08D || id!=0x51)return 0;
    AFHolidayPlace *p=0;
    return af_holiday_hide_native_make(m->native,AF_HR_NATIVE,0xD0D1,id,
        AF_HR_SOURCE+name+id,&p)==1?p:0;
}
AFHolidayPlace *af_hr_manager_walk_hide(AFHarvestManagerView *m,AFHolidayControl *c,int id) {
    if(!m || !valid(c) || id!=0x51)return 0;
    int seed;if(!af_holiday_hide_native_fluctuation(m->native,&seed))return 0;
    AFHolidayPlace *p=0;
    return af_holiday_hide_native_walk(m->native,AF_HR_NATIVE,0xD08D,id,
        (int)((u32)seed+AF_HR_SOURCE),&p)==1?p:0;
}
AFHolidayPlace *af_hr_manager_show(AFHarvestManagerView *m,AFHolidayControl *c,int id) {
    if(!m || !valid(c) || id!=0x51)return 0;
    int seed;if(!af_holiday_hide_native_fluctuation(m->native,&seed))return 0;
    int result=af_holiday_hide_native_show(m->native,AF_HR_NATIVE,id,
        (int)((u32)seed+AF_HR_SOURCE+(u32)id),&c->block);
    if(result==2)return (void *)-1;
    return result==1?af_holiday_native_get_place(AF_HR_NATIVE,id):0;
}
int af_hr_manager_start(void *manager,AFHolidayControl *c) {
    AFHarvestManagerView m;
    return valid(c) && view(manager,&m)?af_hr_source_start(&m,c):0;
}
int af_hr_manager_stop(void *manager,AFHolidayControl *c) {
    AFHarvestManagerView m;
    /* STOP must clear transient state even after selection or the day changes. */
    return c && c->type==AF_HR_NATIVE && view(manager,&m)?af_hr_source_stop(&m,c):0;
}
int af_hr_manager_in(void *manager,AFHolidayControl *c) {
    AFHarvestManagerView m;
    return valid(c) && view(manager,&m)?af_hr_source_in(&m,c):0;
}
int af_hr_manager_out(void *manager,AFHolidayControl *c) {
    return manager && c && c->type==AF_HR_NATIVE?
        af_hr_manager_native_check_status(AF_HR_NATIVE,AF_HE_STOP):0;
}
int af_hr_manager_behind(void *manager,AFHolidayControl *c) {
    AFHarvestManagerView m;
    return valid(c) && view(manager,&m)?af_hr_source_behind(&m,c):0;
}
