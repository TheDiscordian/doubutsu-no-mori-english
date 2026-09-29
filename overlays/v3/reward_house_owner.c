/* Retain the complete native home/railway door routine and its geometry. */
#include "reward_event.h"
extern void af_v3_save_halt(int) __attribute__((noreturn));
__UINTPTR_TYPE__ af_rw_house_entry(const ACTOR *actor) {
    if(!actor || *(const s16 *)actor!=0x66)return 0;
    const u32 *descriptor=(const u32 *)(__UINTPTR_TYPE__)
        *(const u32 *)((const u8 *)actor+0x170);
    if(!descriptor || descriptor[0]!=0x3E90000 || descriptor[2]!=0x809BE720 ||
       descriptor[3]<0x809C0E50 || descriptor[3]-descriptor[2]>0x8000 ||
       !descriptor[4] || descriptor[4]&15u)return 0;
#ifdef __mips__
    if(descriptor[4]<0x80000000u || descriptor[4]>0x80800000u-(descriptor[3]-descriptor[2]))return 0;
#endif
    return (__UINTPTR_TYPE__)descriptor[4]+0x809BF584-descriptor[2];
}
void af_rw_native_house_door(void *door,int type,ACTOR *actor) {
    __UINTPTR_TYPE__ entry=af_rw_house_entry(actor);
    if(!entry || !door || type<0 || type>3)af_v3_save_halt(-1);
    ((void (*)(void *,int,ACTOR *))entry)(door,type,actor);
}
