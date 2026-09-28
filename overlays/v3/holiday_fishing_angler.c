/* Connect the native host to the imported stall without replacing the native
 * host's dialogue/demo/item-handover state machine or its original fallback. */
#include "holiday_fishing_angler.h"
#ifdef __mips__
_Static_assert(sizeof(AFHFClip)==16,"Native four-function fishing clip");
_Static_assert(sizeof(AFHFClipState)<=64,"Owned fishing clip lifetime state");
#endif
_Static_assert(sizeof(AFHFNativePerson)==16,"Native by-value identity ABI");
static int active(void) {
    return af_hf_native_clip==&af_hf_bridge_clip && af_hf_clip_state.owner &&
        af_hf_clip_state.source==&af_hf_source_clip;
}
static int enter(void) {
    if(!active())return 0;
    if(!af_hf_live_enter()) {af_hf_native_halt();return 0;}
    return 1;
}
static void leave(void) {
    int failed=af_hf_live.failed || af_hf_live.records.error;
    af_hf_live_leave();
    if(failed)af_hf_native_halt();
}
static int message(AFHFH item) {
    /* 2301 is the native herabuna, not the donor brook trout. Its existing
       translated message stays native; the imported trout owns 2328. */
    if(item==0x2301)return 0x10F7;
    if(item==0x2328)item=0x2301;
    return active()?af_hf_source_clip.message(item):-1;
}
static void random_top(void) {
    if(enter()) {af_hf_source_clip.random_top();leave();}
}
static void topname(void) {
    if(enter()) {af_hf_live_topname();leave();}
}
static int size(int rank) {
    if(!enter())return -1;
    int result=af_hf_source_clip.size(rank);leave();return result;
}
const AFHFClip af_hf_bridge_clip={message,random_top,topname,size};
int af_hf_clip_lifecycle(void *owner,int phase) {
    AFHFClipState *s=&af_hf_clip_state;
    if(!owner || (phase!=0 && phase!=1))return 0;
    if(phase==1) {
        if(s->owner!=owner)return 0;
        if(af_hf_native_clip==&af_hf_bridge_clip)af_hf_native_clip=s->previous;
        af_hf_clear(s,sizeof(*s),0);return 1;
    }
    if(s->owner || !af_hf_source_clip.message || !af_hf_source_clip.random_top ||
       !af_hf_source_clip.topname || !af_hf_source_clip.size)return 0;
    s->previous=af_hf_native_clip;s->source=&af_hf_source_clip;s->owner=owner;
    af_hf_native_clip=&af_hf_bridge_clip;return 1;
}
static int mapped(int value) {
    /* Clip-produced values already use additive IDs. Native host immediates
       still use source IDs. The herabuna value is never a host immediate. */
    if(active() && value!=0x10F7) {
        int target=af_hf_live_message(value);
        if(target>=0)return target;
    }
    return value;
}
void af_hf_angler_continue(void *window,int value) {af_hf_native_continue(window,mapped(value));}
void af_hf_angler_start_message(int value) {af_hf_native_start_message(mapped(value));}
int af_hf_angler_message_number(void *window) {
    int value=af_hf_native_message_number(window);
    if(active())for(unsigned int i=0;i<af_hf_message_count;i++)
        if(af_hf_message_map[i][1]==value)return af_hf_message_map[i][0];
    return value;
}
int af_hf_angler_number(AFHFB *out,int value,int unit) {
    if(!active())return af_hf_native_number(out,value,unit);
    if(!enter())return 0;
    int count=af_hf_live_number(out,value,unit);
    if(!count)af_hf_live.failed=1;
    leave();return count;
}
void af_hf_angler_winner(AFHFNativePerson key) {
    if(!active()) {
        AFHFB *event=af_hf_native_event_area(af_hf_native_clock.month==6?20:2,0);
        if(event)af_hf_copy(event+4,&key,16);
        else af_hf_native_halt();
        return;
    }
    if(!enter())return;
    af_holiday_fish_native_person(&af_hf_live.event.person,(const AFHFB*)&key);
    af_hf_live_record(&af_hf_live.event.person,af_hf_live.event.size);
    leave();
}
