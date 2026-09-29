/* Wisp's official text uses its own source-message map and already-converted
 * native reward IDs. Other families' message/item resolvers are not equivalent. */
#include "carried_event.h"
#include "constants.h"
extern int af_cw_message(int),af_carried_type(u32);
extern void af_cw_native_message(int),af_cw_native_continue(void *,int);
extern void af_cw_native_order(int,int,u16);
extern int af_cw_native_item_name(u8 *,u32,u32);
extern void af_cw_native_item_string(void *,int,const u8 *,int);
extern const u8 af_cw_angry_names[32][16];

void mDemo_Set_msg_num(int source) {
    int native=af_cw_message(source);
    if(native>=0)af_cw_native_message(native);
}
void mMsg_Set_continue_msg_num(void *window,int source) {
    int native=af_cw_message(source);
    if(window && native>=0)af_cw_native_continue(window,native);
}
void mDemo_Set_OrderValue(int type,int slot,u16 value) {
    /* NPC1[0] holds the already-converted reward; translating it twice can
     * silently award an unrelated donor item with the same numeric value. */
    if(type==mDemo_ORDER_NPC1 && slot==0 && (!value || af_carried_type(value)<=0))return;
    af_cw_native_order(type,slot,value);
}
void mIN_copy_name_str(u8 *out,u16 item) {
    if(!out)return;
    for(unsigned i=0;i<16;i++)out[i]=' ';
    if(item && af_carried_type(item)>0)(void)af_cw_native_item_name(out,16,item);
}
int mIN_get_item_article(u16 item) {
    (void)item;
    /* Native fields do not synthesize articles. The surrounding complete
     * official English dialogue supplies its wording. */
    return 0;
}
void mString_Load_StringFromRom(u8 *out,unsigned length,int source) {
    if(!out || length!=16 || source<0x62E || source>=0x64E)return;
    for(unsigned i=0;i<16;i++)out[i]=af_cw_angry_names[source-0x62E][i];
}
void mMsg_Set_item_str(void *window,int slot,const u8 *text,int length) {
    if(window && text && slot>=0 && slot<5 && length>=0 && length<=16)
        af_cw_native_item_string(window,slot,text,length);
}
void mMsg_Set_item_str_art(void *window,int slot,const u8 *text,int length,int article) {
    (void)article;mMsg_Set_item_str(window,slot,text,length);
}
