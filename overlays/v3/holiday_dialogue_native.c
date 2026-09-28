#include "holiday_dialogue.h"
#include "holiday_npc.h"
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))(at))
extern const AFHolidayDialogue af_holiday_dialogue_data;
static void transport(void *context,const AFHolidayAction *action) {
    AFHolidayNpc *a=context;
    const AFHolidayTransport o={
        .actor=a,.window=FN(0x8009D1F0u,void *,void)(),
        /* The installed shared reader includes all selected carried categories.
         * Quest's old index precheck does not recognise additive item IDs. */
        .item_name=FN(0x801969C8u,int,unsigned char *,unsigned int,unsigned int),
        .town_name=FN(0x800950D8u,const unsigned char *,void),
        .item=FN(0x8009D88Cu,void,void *,int,const unsigned char *,int),
        /* Startup restores this entry to the resident 16-byte field setter. */
        .free_string=FN(0x8009D6D0u,void,void *,int,const unsigned char *,int),
        .turn=FN(0x8007B908u,void,unsigned char),.camera=FN(0x8007BA1Cu,void,int),
        .message=FN(0x8007B5C0u,void,int),.continuation=FN(0x8009DBA4u,void,void *,int),
        .listen=FN(0x8007D098u,void,void),.start=FN(0x8007CF34u,void,void *),
        .order=FN(0x8007B44Cu,void,int,int,unsigned short),
    };
    if(!af_holiday_transport(&af_holiday_dialogue_data,&o,action))a->failed=1;
}
int af_holiday_dialogue_bind(AFHolidayNpc *a) {
    if(!a || af_holiday_message(&af_holiday_dialogue_data,0x3280)<0)return 0;
    a->ops.transport=transport;return 1;
}
int af_holiday_npc_continue(AFHolidayNpc *a) {
    if(!a || a->failed)return 0;
    return FN(0x8009E908u,int,void *)(FN(0x8009D1F0u,void *,void)());
}
