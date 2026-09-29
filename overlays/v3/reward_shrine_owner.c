/* Native overlay VMA is not its live RAM address. Resolve complete unchanged
 * Shrine entries through this actor's loaded descriptor on every call. */
#include "reward_event.h"
extern void af_v3_save_halt(int) __attribute__((noreturn));
__UINTPTR_TYPE__ af_rw_shrine_entry(const ACTOR *actor,u32 address) {
    if(!actor || address<0x80A0A1F0 || address>=0x80A0B030 || address&3u)return 0;
    const u32 *descriptor=(const u32 *)(__UINTPTR_TYPE__)
        *(const u32 *)((const u8 *)actor+0x170);
    if(!descriptor || descriptor[0]!=0x8D8EC0 || descriptor[2]!=0x80A0A1F0 ||
       descriptor[3]<0x80A0B2D8 || descriptor[3]-descriptor[2]>0x8000 ||
       !descriptor[4] || descriptor[4]&15u)return 0;
#ifdef __mips__
    if(descriptor[4]<0x80000000u || descriptor[4]>0x80800000u-(descriptor[3]-descriptor[2]))return 0;
#endif
    return (__UINTPTR_TYPE__)descriptor[4]+address-descriptor[2];
}
static __UINTPTR_TYPE__ required(const ACTOR *actor,u32 address) {
    __UINTPTR_TYPE__ entry=af_rw_shrine_entry(actor,address);
    if(!entry)af_v3_save_halt(-1);
    return entry;
}
void af_rw_native_shrine_ctor(ACTOR *a,GAME *g) {
    ((void (*)(ACTOR *,GAME *))required(a,0x80A0A240))(a,g);
}
void af_rw_native_shrine_dtor(ACTOR *a,GAME *g) {
    ((void (*)(ACTOR *,GAME *))required(a,0x80A0A358))(a,g);
}
void af_rw_native_shrine_talk(ACTOR *a,GAME *g) {
    ((void (*)(ACTOR *,GAME *))required(a,0x80A0A7A4))(a,g);
}
void af_rw_native_shrine_action(ACTOR *a,int action) {
    if(action<0 || action>3)af_v3_save_halt(-1);
    ((void (*)(ACTOR *,int))required(a,0x80A0AB44))(a,action);
}
