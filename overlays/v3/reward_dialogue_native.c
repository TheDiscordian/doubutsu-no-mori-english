/* Gift and Shrine dialogue has its own complete additive source-message map.
 * It cannot use Wisp's map, or silently ignore an unmapped source message. */
#include "reward_event.h"
extern int af_rw_message(int);
extern void af_rw_native_message(int),af_rw_native_continue(void *,int);

static int message(int source) {
    int native=af_rw_message(source);
    if(native<0)__builtin_trap();
    return native;
}
void mDemo_Set_msg_num(int source) {
    af_rw_native_message(message(source));
}
void af_rw_continue_message(void *window,int source) {
    if(!window)__builtin_trap();
    af_rw_native_continue(window,message(source));
}
