/* One guarded carried/cover identity path for all sixteen diary styles. */
#include "diary_items.h"
#include "save_runtime.h"
#ifdef AF_V3_PLAYER_TRAVEL
#include "travel_collection.h"
#endif
typedef DiaryByte u8;
typedef DiaryHalf u16;
typedef DiaryWord u32;
#ifdef __mips__
#define header ((const u32 *)0x806E2000u)
#define icons ((const u32 *)0x806E2300u)
#else
extern u32 af_test_diary_items[100],af_test_diary_icons[4];
#define header af_test_diary_items
#define icons af_test_diary_icons
#endif
extern u16 af_diary_native_selected(void);
extern int af_diary_prior_name(u8 *,u32,u32),af_diary_prior_type(u32);
extern u32 af_diary_prior_price(u32);
extern u16 af_diary_prior_display(u32),af_diary_prior_pocket(u32);
extern void af_diary_prior_record(u32),af_v3_require_save_state(void);
extern int af_diary_prior_owned(const u8 *,u32);
extern void af_v3_save_halt(int) __attribute__((noreturn));
#ifdef __mips__
#define state ((struct AfSaveRuntime *)0x8046C000u)
#define players ((u8 *)0x80126EC0u)
#define active (*(u8 *volatile *)0x80136FD8u)
#else
extern struct AfSaveRuntime af_test_diary_item_state;
extern u8 af_test_diary_item_players[4*0xBD0],*af_test_diary_item_active;
#define state (&af_test_diary_item_state)
#define players af_test_diary_item_players
#define active af_test_diary_item_active
#endif

static int extended(u32 item) {
    return item-AF_DIARY_ITEM_FIRST<AF_DIARY_ITEM_COUNT ||
        item-AF_DIARY_COVER_FIRST<AF_DIARY_ITEM_COUNT*4u;
}
static const AFDiaryItem *find(u32 item) {
    u32 index=item-AF_DIARY_ITEM_FIRST;
    if(index>=AF_DIARY_ITEM_COUNT) {
        if(item-AF_DIARY_COVER_FIRST>=AF_DIARY_ITEM_COUNT*4u)return 0;
        index=(item-AF_DIARY_COVER_FIRST)>>2;
    }
    if(header[0]!=0x41464449u || header[1]!=1u || header[2]!=AF_DIARY_ITEM_COUNT ||
       header[3]!=sizeof(AFDiaryItem) || !(af_diary_native_selected()&(1u<<index)))return 0;
    const AFDiaryItem *r=(const AFDiaryItem *)(header+4)+index;
    if(r->item!=AF_DIARY_ITEM_FIRST+index || r->cover!=AF_DIARY_COVER_FIRST+index*4u ||
       r->style!=index || r->category!=AF_DIARY_ITEM_CATEGORY)return 0;
    return r;
}
int af_diary_item_name(u8 *target,u32 capacity,u32 item) {
    if(!extended(item))return af_diary_prior_name(target,capacity,item);
    const AFDiaryItem *r=find(item);
    if(!target || capacity<16u || !r)return 0;
    for(u32 i=0;i<16;i++)target[i]=r->name[i];
    return 1;
}
int af_diary_item_type(u32 argument) {
    u32 item=(u16)argument;
    if(!extended(item))return af_diary_prior_type(argument);
    const AFDiaryItem *r=find(item);
    return r ? (item==r->item ? AF_DIARY_ITEM_CATEGORY : 10) : 0;
}
u32 af_diary_item_price(u32 argument) {
    u32 item=(u16)argument;
    if(!extended(item))return af_diary_prior_price(argument);
    const AFDiaryItem *r=find(item);
    return r ? r->price : 0;
}
u16 af_diary_item_display(u32 argument) {
    u32 item=(u16)argument;
    if(!extended(item))return af_diary_prior_display(argument);
    const AFDiaryItem *r=find(item);
    /* Ordinary placement keeps the carried diary. Only collection consumers
     * convert it to its cover; replacing it here would bypass surface A-tap. */
    return r ? r->item : 0;
}
u16 af_diary_item_pocket(u32 argument) {
    u32 item=(u16)argument;
    if(!extended(item))return af_diary_prior_pocket(argument);
    const AFDiaryItem *r=find(item);
    return r ? r->item : 0;
}
u32 af_diary_item_collection(u32 item) {
    const AFDiaryItem *r=find(item);
    return r ? r->cover : 0;
}
u32 af_diary_item_icon(u32 item) {
    if(item-AF_DIARY_ITEM_FIRST>=AF_DIARY_ITEM_COUNT || !find(item) ||
       icons[0]!=0x806E2320u || icons[1]!=0x806E2340u)return 0;
    return 0x806E2300u;
}
static u32 player_slot(const u8 *player) {
    for(u32 i=0;i<4;i++)if(player==players+i*0xBD0u)return i;
    return 4;
}
void af_diary_item_record(u32 argument) {
    u32 item=(u16)argument;
    if(!extended(item)) {af_diary_prior_record(argument);return;}
    u32 cover=af_diary_item_collection(item);
    if(!cover)return;
    u32 player=player_slot(active);
#ifdef AF_V3_PLAYER_TRAVEL
    if(player==4) {af_travel_collection(active,cover,1);return;}
#else
    if(player==4)af_v3_save_halt(AF_SAVE_ARGUMENT);
#endif
    af_v3_require_save_state();
    int result=af_v3_save_collect(state->working,player,cover,1);
    if(result<0)af_v3_save_halt(result);
}
int af_diary_item_owned(const u8 *player,u32 item) {
    if(!extended(item))return af_diary_prior_owned(player,item);
    u32 cover=af_diary_item_collection(item),slot=player_slot(player);
    if(!cover)return 0;
#ifdef AF_V3_PLAYER_TRAVEL
    if(slot==4)return af_travel_collection(player,cover,0);
#else
    if(slot==4)return 0;
#endif
    af_v3_require_save_state();
    int result=af_v3_save_collect(state->working,slot,cover,0);
    if(result<0)af_v3_save_halt(result);
    return result;
}
