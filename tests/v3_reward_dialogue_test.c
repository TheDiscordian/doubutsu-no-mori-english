#include <assert.h>
#include <stdio.h>
extern int af_rw_message(int);
extern void mDemo_Set_msg_num(int),af_rw_continue_message(void *,int);
static int current=-1,continued=-1;
static void *expected_window;
void af_rw_native_message(int id) {current=id;}
void af_rw_native_continue(void *window,int id) {assert(window==expected_window);continued=id;}
int main(void) {
    int window;expected_window=&window;
    unsigned count=0;
    for(int source=0;source<65536;source++) {
        int native=af_rw_message(source);
        if(native<0)continue;
        assert(native>=13136 && native<13182);
        mDemo_Set_msg_num(source);assert(current==native);
        af_rw_continue_message(&window,source);assert(continued==native);count++;
    }
    assert(count==46 && af_rw_message(-1)==-1 && af_rw_message(65536)==-1);
    puts("Gift dialogue: every source ID maps to its own additive native message for start and continuation; unknown IDs remain rejected.");
}
