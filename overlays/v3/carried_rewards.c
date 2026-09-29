/* All reward categories retain their source order and probability. Filter with
 * the installed item reader before counting, selecting, or giving any item. */
#include "carried_event.h"
typedef struct {u16 source,item;u8 quantity,pad[3];} Reward;
extern const Reward af_cw_rewards[];
extern const u32 af_cw_reward_count;
extern int af_carried_type(u32),af_carried_owned(const u8 *,u32);
extern u16 af_cw_paper_stack(u16,unsigned);

u16 af_cw_reward_native(u16 source) {
    u32 lo=0,hi=af_cw_reward_count;
    while(lo<hi) {
        u32 mid=lo+(hi-lo)/2;const Reward *r=af_cw_rewards+mid;
        if(source<r->source)hi=mid;
        else if(source>r->source)lo=mid+1;
        else {
            /* Paper policy is global, including the imported orange style.
             * Native counterparts and already-mapped imported packs both pass
             * through it. Other item rewards retain their source quantity. */
            u16 item=(r->source>>8)==0x20?af_cw_paper_stack(r->item,r->quantity):r->item;
            return item && af_carried_type(item)>0?item:0;
        }
    }
    return 0;
}
int af_cw_reward_supported(u16 item) {return af_cw_reward_native(item)!=0;}
int mSP_CollectCheck(u16 source) {
    u16 item=af_cw_reward_native(source);const u8 *player=af_cw_private();
    if(!item || !player)return 1;
    /* Source collection checks intentionally exclude clothes and umbrellas.
     * They remain uncollected candidates even after receiving one. */
    unsigned type=source>>12,category=source>>8;
    return type==1 || type==3 || category==0x20 || category==0x26 || category==0x27 ?
        af_carried_owned(player,item)!=0:0;
}
u16 af_cw_reward_at(int selected,const u16 *list) {
    if(selected<0 || !list)return 0;
    for(;*list;list++)if(af_cw_reward_supported(*list)) {
        if(!selected)return *list;
        --selected;
    }
    return 0;
}
u16 mRmTp_FtrItemNo2Item1ItemNo(u16 source,int keep_tools) {
    /* The checked complete reward lists contain carried items and ordinary
     * furniture, never room-display aliases. Convert their actual identity at
     * this boundary; subsequent name/demo/inventory calls receive native IDs. */
    return keep_tools==1?af_cw_reward_native(source):0;
}
