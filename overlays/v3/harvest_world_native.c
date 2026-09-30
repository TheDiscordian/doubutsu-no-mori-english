/* The native constructor installs its force-angle callback at player 123C.
 * That callback queues native rotation and retains ordinary collision/motion;
 * the donor's larger player layout must never be used for this call. */
#include "harvest_event.h"
extern GAME *volatile af_hr_native_game;
GAME *af_hr_game(void) {return af_hr_native_game;}
u32 af_hr_frame(void) {
    GAME *game=af_hr_game();
    return game?af_hp_frame(game):0;
}
void af_hr_force_angle(GAME *game,const xyz_t *position,const s_xyz *angle,int flags) {
    if(!game || game!=af_hr_game() || position || !angle || flags!=32)return;
    const u8 *player=(const u8 *)af_cw_player_actor(game);
    if(!player)return;
#ifdef __mips__
    u32 address=*(const u32 *)(player+0x123C);
    if(address<0x80000000u || address>=0x80800000u)return;
    void (*force)(GAME *,const xyz_t *,const s_xyz *,u8)=
        (void (*)(GAME *,const xyz_t *,const s_xyz *,u8))(__UINTPTR_TYPE__)address;
#else
    extern void af_hr_test_force(GAME *,const xyz_t *,const s_xyz *,u8);
    void (*force)(GAME *,const xyz_t *,const s_xyz *,u8)=af_hr_test_force;
#endif
    force(game,0,angle,(u8)flags);
}
