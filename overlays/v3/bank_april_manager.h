#ifndef AF_V3_BANK_APRIL_MANAGER_H
#define AF_V3_BANK_APRIL_MANAGER_H
#include "bank_april.h"
#include "holiday_owner.h"
/* Decode the native shrine flag; never cast a source manager onto N64 RAM. */
typedef struct {int shrine_block_exists;} AFBankAprilManagerView;
int af_bank_april_manager_start(void *,AFHolidayControl *);
int af_bank_april_manager_stop(void *,AFHolidayControl *);
int af_bank_april_check_keep(int);
void af_bank_april_set_keep(int),af_bank_april_clear_keep(int);
void af_bank_april_set_status(int,int),af_bank_april_clear_status(int,int);
void *af_bank_april_actor_info(GAME_PLAY *);
extern GAME_PLAY *af_bank_april_game;
extern ACTOR *af_bank_april_make(void *,GAME *,int,f32,f32,f32,int,int,int,int,int,int,u16,int,int,int);
extern void af_bank_april_delete(ACTOR *);
extern void af_bank_april_native_set_status(int,int),af_bank_april_native_clear_status(int,int);
extern void *af_bank_april_previous_descriptor(int);
extern int af_bank_april_prior_calendar(void);
extern u8 af_bank_april_native_rtc[8];
extern const u8 af_bank_april_schedule[12];
#endif
