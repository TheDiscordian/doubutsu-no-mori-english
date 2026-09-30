/* Keep all official Harvest pages on their own additive message map. Native
 * message numbers read back from the window must not be compared to donor IDs. */
#include "harvest_event.h"
extern void af_cw_native_message(int),af_cw_native_continue(void *,int);
void af_hr_begin_message(int source) {
    int native=af_hr_message(source);
    if(native>=0)af_cw_native_message(native);
}
void af_hr_continue_message(int source) {
    void *window=mMsg_Get_base_window_p();
    int native=af_hr_message(source);
    if(window && native>=0)af_cw_native_continue(window,native);
}
