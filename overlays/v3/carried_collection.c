/* Native collection calls share the same bounded additive identities as the
 * inventory readers. Never let a new paper index address the native bitset. */
#include "carried_items.h"
#ifdef AF_V3_PAPER_PACKS
#include "carried_paper.h"
#endif
#include "holiday_cards.h"
#include "save_codec.h"
#ifdef AF_V3_PLAYER_TRAVEL
#include "travel_collection.h"
#endif
typedef unsigned char u8;
typedef unsigned int u32;
extern void af_carried_prior_record(u32);
extern int af_carried_prior_owned(const u8 *,u32);
extern u8 *af_v3_card_data(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));
#ifdef __mips__
#define players ((u8 *)0x80126EC0u)
#define active (*(u8 *volatile *)0x80136FD8u)
#else
extern u8 af_console_players[4*0xBD0],*af_test_carried_active;
#define players af_console_players
#define active af_test_carried_active
#endif
static u32 slot(const u8 *player) {
    for(u32 i=0;i<4;i++)if(player==players+i*0xBD0u)return i;
    return 4;
}
void af_carried_record(u32 argument) {
    u32 item=(unsigned short)argument;
#ifdef AF_V3_PAPER_PACKS
    if(af_carried_paper_reserved(item)) {
        if(af_carried_paper_packs_enabled())
            af_carried_prior_record(0x2000u+(unsigned)af_carried_paper_style(item));
        return;
    }
#endif
    if(!af_carried_reserved(item)) {af_carried_prior_record(argument);return;}
    if(item-0x2040u>=4 || af_carried_category(item)!=49)return;
    u32 player=slot(active);
#ifdef AF_V3_PLAYER_TRAVEL
    if(player==4) {af_travel_paper(active,1);return;}
#else
    if(player==4)af_v3_save_halt(AF_SAVE_ARGUMENT);
#endif
    if(af_carried_paper_collect(af_v3_card_data(),player,1)<0)af_v3_save_halt(AF_SAVE_CATALOGUE_INVALID);
}
int af_carried_owned(const u8 *player,u32 item) {
#ifdef AF_V3_PAPER_PACKS
    if(af_carried_paper_reserved(item))return af_carried_paper_packs_enabled()?
        af_carried_prior_owned(player,0x2000u+(unsigned)af_carried_paper_style(item)):0;
#endif
    if(!af_carried_reserved(item))return af_carried_prior_owned(player,item);
    u32 index=slot(player);
    if(item-0x2040u>=4 || af_carried_category(item)!=49)return 0;
#ifdef AF_V3_PLAYER_TRAVEL
    if(index==4)return af_travel_paper(player,0);
#else
    if(index==4)return 0;
#endif
    int result=af_carried_paper_collect(af_v3_card_data(),index,0);
    if(result<0)af_v3_save_halt(AF_SAVE_CATALOGUE_INVALID);
    return result;
}
