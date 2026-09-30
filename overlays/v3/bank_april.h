#ifndef AF_V3_BANK_APRIL_H
#define AF_V3_BANK_APRIL_H
#include "holiday_participants.h"
#include "holiday_native.h"
/* Source 17 receives a separate additive event identity. The calendar/manager
 * installer must register that identity before construction is admitted. */
enum {AF_BANK_APRIL_SOURCE=17,AF_BANK_APRIL_NATIVE=117,AF_BANK_APRIL_PROFILE=0xF6};
typedef struct {u16 talk_bitfield[4];} aAPC_event_save_data_c;
typedef struct {
    int (*talk_chk_proc)(mActor_name_t);
    void (*talk_set_proc)(mActor_name_t);
    int (*get_msg_num_proc)(mActor_name_t,int);
    aAPC_event_save_data_c *event_save_data_p;
} aAPC_Clip_c;
typedef struct {ACTOR actor_class;aAPC_Clip_c clip;} APRILFOOL_CONTROL_ACTOR;
typedef struct {struct {aAPC_Clip_c *aprilfool_control_clip;} clip;u8 player_no;} AFBankAprilCommon;
extern AFBankAprilCommon af_bank_april_common;
#define Common_Get(field) (af_bank_april_common.field)
extern void *af_bank_april_get(int,int),*af_bank_april_reserve(int,int);
extern void af_bank_april_dying(int,ACTOR *);
extern int af_bank_pelly_foreigner(void);
extern void af_bank_april_zero(void *,u32),af_bank_april_none(ACTOR *,GAME *);
#define mEv_get_save_area af_bank_april_get
#define mEv_reserve_save_area af_bank_april_reserve
#define mEv_actor_dying_message af_bank_april_dying
#define mLd_PlayerManKindCheck af_bank_pelly_foreigner
#define mActor_NONE_PROC1 af_bank_april_none
#define bzero af_bank_april_zero
extern void *af_bank_april_native_get(int,int),*af_bank_april_native_reserve(int,int);
extern void af_bank_april_native_dying(int,ACTOR *);
extern u8 af_bank_april_native_slots[264];
extern u8 af_bank_player;
extern u8 af_bank_account_mode;
int af_bank_april_construct(ACTOR *,GAME *);
int af_bank_april_destruct(ACTOR *,GAME *);
int af_bank_april_player_clear(u32);
int af_bank_april_calendar_before_cleanup(void);
void *af_bank_april_descriptor(int);
void af_bank_april_ctor(ACTOR *,GAME *),af_bank_april_dtor(ACTOR *,GAME *);
void af_bank_april_step(ACTOR *,GAME *);
#ifdef __mips__
_Static_assert(sizeof(aAPC_event_save_data_c)==8,"Complete four-player April state");
_Static_assert(sizeof(aAPC_Clip_c)==16,"Complete source April clip");
_Static_assert(__builtin_offsetof(APRILFOOL_CONTROL_ACTOR,clip)==0x174,"Native April actor prefix");
_Static_assert(sizeof(APRILFOOL_CONTROL_ACTOR)==0x184,"Complete native April actor allocation");
#endif
#endif
