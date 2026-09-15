#ifndef AF_V3_CAMPSITE_MANAGER_H
#define AF_V3_CAMPSITE_MANAGER_H
#include "campsite_event.h"
#include "camper.h"

typedef struct AfCampControl AfCampControl;
typedef int (*AfCampCallback)(void *, AfCampControl *);
struct AfCampControl {
    int type;
    AfCampCallback start, stop, enter, leave, behind;
    unsigned int reserved[2];
};
typedef struct {
    int block_z, block_x, unit_z, unit_x;
    camp_u16 foreground, flags;
} AfCampPlace;
typedef struct {
    camp_u32 type, hours;
    camp_u16 begin, end, status, reserved;
} AfCampToday;

extern const camp_u8 selected_furniture[];
extern camp_u8 native_event_index[128];
extern AfCampToday native_today[16];
extern camp_u32 native_changes;
extern int native_field_valid(void);
extern camp_u16 native_field_id(void);
extern camp_u8 *native_get_save(int, int);
extern camp_u8 *native_reserve_save(int, int);
extern int native_clear_save(int, int);
extern int native_check_keep(int);
extern void native_set_keep(int);
extern void native_clear_keep(int);
extern void native_set_status(int, int);
extern void native_clear_status(int, int);
extern void native_reset_appeared(void);
extern void native_shuffle(int *, int, int);
extern int native_unseen(camp_u32);
extern int native_grow(camp_u32);
extern void native_mark_appeared(camp_u32);
extern AfCampPlace *native_get_place(int, int);
extern int native_get_fg(camp_u16 *, int, int, int, int);
extern AfCampPlace *native_place_tent(void *, AfCampControl *, camp_u16, camp_u8);
extern int native_remove_tent(AfCampControl *, camp_u8);

int af_v3_camper_event_start(void *, AfCampControl *);
int af_v3_camper_event_stop(void *, AfCampControl *);
int af_v3_camper_event_in(void *, AfCampControl *);
int af_v3_camper_event_out(void *, AfCampControl *);
#endif
