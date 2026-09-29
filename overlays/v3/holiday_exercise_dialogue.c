/* Exercise source IDs share the installed holiday/card transport and the
 * complete participant branch graph. No same-number native text fallback. */
#include "holiday_exercise.h"
#include "holiday_dialogue.h"
#include "constants.h"
extern const AFHolidayDialogue af_holiday_dialogue_data;
extern int af_he_participant_message(int);
extern void af_he_native_message(int),af_he_native_continue(void *,int);
extern void af_he_native_order(int,int,u16);
extern void af_he_native_free_string(void *,int,const u8 *,int);
extern void af_he_native_item_string(void *,int,const u8 *,int);
extern int af_he_native_item_name(u8 *,u32,u32);
/* Checked item resolver and failure handler belong to the actual card/player
 * transaction. Returning zero is not permission to put an empty item in hand. */
extern int af_he_item(u16),af_he_failed(void);
extern void af_he_fault(void);
int af_he_message(int source) {
    int n=af_he_participant_message(source);
    return n>=0?n:af_holiday_message(&af_holiday_dialogue_data,(u32)source);
}
void mDemo_Set_msg_num(int source) {
    int n=af_he_message(source);
    if(n<0 || af_he_failed()) {af_he_fault();return;}
    af_he_native_message(n);
}
void mMsg_Set_continue_msg_num(void *window,int source) {
    int n=af_he_message(source);
    if(!window || n<0 || af_he_failed()) {af_he_fault();return;}
    af_he_native_continue(window,n);
}
void mDemo_Set_OrderValue(int type,int slot,u16 value) {
    if(type==mDemo_ORDER_NPC1 && slot==0) {
        int native=af_he_item(value);
        if(native<=0) {af_he_fault();return;}
        value=(u16)native;
    }
    if(!af_he_failed())af_he_native_order(type,slot,value);
}
void mIN_copy_name_str(u8 *out,u16 source) {
    int native=af_he_item(source);
    if(!out)return;
    for(unsigned int i=0;i<16;i++)out[i]=' ';
    if(native<=0 || !af_he_native_item_name(out,16,(u32)native))af_he_fault();
}
int mIN_get_item_article(u16 source) {
    /* Native text fields never prepend grammatical articles. Their official
     * surrounding wording is retained; this metadata has no native reader. */
    if(af_he_item(source)<=0)af_he_fault();
    return 0;
}
void mMsg_Set_free_str_art(void *window,int slot,const u8 *text,int length,int article) {
    (void)article;
    if(window && text && length>=0 && length<=16 && !af_he_failed())
        af_he_native_free_string(window,slot,text,length);
    else af_he_fault();
}
void mSC_item_string_set(u16 source,int slot) {
    u8 text[16];mIN_copy_name_str(text,source);
    void *window=mMsg_Get_base_window_p();
    if(window && slot>=0 && slot<5 && !af_he_failed())af_he_native_item_string(window,slot,text,16);
    else af_he_fault();
}
void mSC_event_name_set(int event) {
    /* Reuse the shared official event labels, including the town-name prefix.
     * The complete transport validates its actor/window/services together. */
    extern int af_he_event_string(int);
    if(!af_he_event_string(event))af_he_fault();
}
