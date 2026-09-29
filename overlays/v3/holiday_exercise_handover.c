/* Complete native handover transport for the donor's card conversations.
 * The N64 engine already implements discard (7), inspect/return (8), and the
 * ordinary transfer/wait transitions; reuse those real animations and owners. */
#include "holiday_exercise.h"
#include "constants.h"
typedef struct {
    u32 birth,change_master,change_mode;
    u8 request_mode,player_after_mode;u16 item;
    ACTOR *master,*target;
    u8 present,changed,pad[2];ACTOR *actor;u32 rebuild;
} NativeHandover;
extern NativeHandover *volatile af_he_native_handover;
extern ACTOR *af_he_native_player(GAME *);
extern int af_he_native_request_give(GAME *,u16,int,int,int);
extern int af_he_item(u16);
extern void af_he_fault(void);
#ifdef __mips__
_Static_assert(sizeof(NativeHandover)==0x24,"Complete native handover clip");
_Static_assert(__builtin_offsetof(NativeHandover,master)==0x10,"Native handover owner");
_Static_assert(__builtin_offsetof(NativeHandover,actor)==0x1C,"Native handover actor");
#endif
static NativeHandover *clip(void) {
    NativeHandover *h=af_he_native_handover;
    if(!af_he_talk_actor() || !h || !h->actor || !h->birth || !h->change_mode) {
        af_he_fault();return 0;
    }
    return h;
}
void *af_he_handover_master(void) {
    NativeHandover *h=clip();
    /* Missing transport must not look like a finished handover. */
    return h?h->master:(void *)&af_he_native_handover;
}
int af_he_handover_mode(void) {
    NativeHandover *h=clip();return h?h->request_mode:-1;
}
void af_he_handover_after(int mode) {
    NativeHandover *h=clip();ACTOR *a=af_he_talk_actor();
    if(!h || mode!=8 || h->request_mode!=aHOI_REQUEST_TRANS_WAIT ||
            (h->master!=a && h->target!=a) ||
            h->item<ITM_EXCERCISE_CARD00 || h->item>ITM_EXCERCISE_CARD12) {
        af_he_fault();return;
    }
    h->player_after_mode=(u8)mode;
}
int mPlib_request_main_give_type1(GAME *game,u16 item,int mode,int present,int surface) {
    NativeHandover *h=clip();ACTOR *actor=af_he_talk_actor();
    int native=af_he_item(item);
    if(!h || !game || !actor || native<0 || item!=ITM_EXCERCISE_CARD00 ||
            (mode!=7 && mode!=8) || present || surface) {
        af_he_fault();return 0;
    }
    const u8 *player=(const u8 *)af_he_native_player(game);
    /* Native TALK is 40, and its actual talk actor lives at D10. The request
     * helper itself checks priority and returns the give callback's result. */
    if(!player || h->master || *(const int *)(player+0xCF0)!=0x40 ||
            *(ACTOR *const *)(player+0xD10)!=actor)return 0;
    return af_he_native_request_give(game,(u16)native,mode,present,surface)==1;
}
