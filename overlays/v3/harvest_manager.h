#ifndef AF_V3_HARVEST_MANAGER_H
#define AF_V3_HARVEST_MANAGER_H
#include "holiday_owner.h"
#include "harvest_state.h"
/* Only a decoded view reaches the donor callback, never a donor struct cast
 * onto the real N64 manager actor. */
typedef struct {void *native;int shrine_block_exists;} AFHarvestManagerView;
int af_hr_manager_start(void *,AFHolidayControl *);
int af_hr_manager_stop(void *,AFHolidayControl *);
int af_hr_manager_in(void *,AFHolidayControl *);
int af_hr_manager_out(void *,AFHolidayControl *);
int af_hr_manager_behind(void *,AFHolidayControl *);
int af_hr_manager_check_keep(int);
void af_hr_manager_set_keep(int),af_hr_manager_clear_keep(int);
AFHolidayPlace *af_hr_manager_make_hide(AFHarvestManagerView *,AFHolidayControl *,unsigned short,int);
AFHolidayPlace *af_hr_manager_walk_hide(AFHarvestManagerView *,AFHolidayControl *,int);
AFHolidayPlace *af_hr_manager_show(AFHarvestManagerView *,AFHolidayControl *,int);
extern void af_hr_manager_native_set_status(int,int),af_hr_manager_native_clear_status(int,int);
extern int af_hr_manager_native_check_status(int,int);
#endif
