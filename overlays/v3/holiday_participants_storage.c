/* Shared event-area routing for every registered participant family. No source
 * event number is passed straight to a native table. */
#include "holiday_participants.h"
extern int af_holiday_native_type(unsigned int);
extern void *af_hp_native_get_save(int,int),*af_hp_native_reserve_save(int,int);
#ifdef AF_HP_CARRIED_REGISTRY
extern void *af_cw_get_save(int,int),*af_cw_reserve_save(int,int);
#endif
static int event(int donor,int area) {
    for(unsigned int i=0;i<AF_HP_OWNER_COUNT;i++) {
        const AFHPRecord *r=af_hp_records+i;
        if(r->kind&AF_HP_NO_SAVE) {
            if(area==15 && (donor==r->event || donor==r->save))return af_holiday_native_type(donor);
        } else if(donor==r->event && (area==15 || area==r->save))return af_holiday_native_type(donor);
    }
    return -1;
}
void *mEv_get_save_area(int donor,int id) {
#ifdef AF_HP_CARRIED_REGISTRY
    if(donor==114)return af_cw_get_save(donor,id);
#endif
    int native=event(donor,id);return native<0?0:af_hp_native_get_save(native,id);
}
void *mEv_reserve_save_area(int donor,int id) {
#ifdef AF_HP_CARRIED_REGISTRY
    if(donor==114)return af_cw_reserve_save(donor,id);
#endif
    int native=event(donor,id);return native<0?0:af_hp_native_reserve_save(native,id);
}
