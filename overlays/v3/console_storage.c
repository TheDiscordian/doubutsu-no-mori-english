/* Format-five adapter around the existing canonical format-four save codec. */
#include "console_storage.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
typedef __UINTPTR_TYPE__ address;
#define MAGIC 0x41464335u
#define GUARD 0xAF4355DEu
#ifdef AF_V3_FISHING_STORAGE
extern u8 af_v3_fishing_state[AF_HF_BYTES];
#endif
#ifdef AF_V3_CARD_STORAGE
extern u8 af_v3_card_state[AF_HC_BYTES];
#ifdef AF_V3_CARRIED_PROFILE
#define cards_profile(p) af_carried_save_profile(p,af_holiday_cards_enabled(),af_carried_save_enabled())
#define cards_bind(p) af_carried_save_bind(p,af_holiday_cards_enabled(),af_carried_save_enabled())
#else
#define cards_profile(p) af_holiday_cards_profile(p,af_holiday_cards_enabled())
#define cards_bind(p) af_holiday_cards_bind(p,af_holiday_cards_enabled())
#endif
#define extended_expand af_v3_save_expand_cards
#define extended_compress af_v3_save_compress_cards
#define extended_measure af_v3_save_measure_cards
#ifdef AF_V3_BANK_STORAGE
/* A separate checked reservation, never an enlargement of native players,
 * the card record, or the existing event-storage code region. */
#ifdef __mips__
#ifndef AF_BANK_STATE_RAM
#error Bank storage requires an explicit checked state reservation
#endif
#define bank_state ((u8 *)AF_BANK_STATE_RAM)
#define bank_guard ((u32 *)(AF_BANK_STATE_RAM+AF_BANK_BYTES))
#else
extern u8 af_bank_storage[AF_BANK_BYTES];
extern u32 af_bank_storage_guard[4];
#define bank_state af_bank_storage
#define bank_guard af_bank_storage_guard
#endif
extern int af_bank_native_selected(void);
#define bank_profile(p) af_bank_profile(p,AF_BANK_BYTES,af_bank_native_selected())
#define bank_bind(p) af_bank_bind(p,AF_BANK_BYTES,af_bank_native_selected())
#undef extended_expand
#undef extended_compress
#undef extended_measure
#define extended_expand af_v3_save_expand_bank
#define extended_compress af_v3_save_compress_bank
#define extended_measure af_v3_save_measure_bank
#endif
#else
#define extended_expand af_v3_save_expand_fishing
#define extended_compress af_v3_save_compress_fishing
#define extended_measure af_v3_save_measure_fishing
#endif
#ifdef __mips__
#define storage ((struct AFConsoleStorage *)0x804DC800u)
#ifdef AF_V3_DIARY_STORAGE
/* The installer must supply checked reservations; the old 72-KiB scratch cannot
 * accommodate diaries, and must never be grown into the model/console pools. */
#define diary ((AFDiary *)AF_DIARY_STATE_RAM)
#define diary_guard ((u32 *)(AF_DIARY_STATE_RAM+AF_DIARY_BYTES))
#define scratch ((u8 *)AF_DIARY_SCRATCH_RAM)
#define scratch_guard ((u32 *)(AF_DIARY_SCRATCH_RAM+AF_CONSOLE_RAW))
#else
#define scratch ((u8 *)0x804E3000u)
#define scratch_guard ((u32 *)0x804F4980u)
#endif
#define hash ((u32 *)0x804F5000u)
#define hash_guard ((u32 *)0x804F9000u)
#define native_players ((u8 *)0x80126EC0u)
#ifdef AF_V3_LINKED_CANONICAL
extern int af_v3_save_check_extended(const u8 *,u32,const u8 *,u8 *);
extern int af_v3_save_pack_extended(u8 *,u32,const u8 *);
#define canonical_check af_v3_save_check_extended
#define canonical_pack af_v3_save_pack_extended
#else
#define canonical_check ((int (*)(const u8 *,u32,const u8 *,u8 *))AF_CONSOLE_CANONICAL_CHECK)
#define canonical_pack ((int (*)(u8 *,u32,const u8 *))AF_CONSOLE_CANONICAL_PACK)
#endif
#define original_clear ((void (*)(u8 *))AF_CONSOLE_PRIOR_PLAYER_CLEAR)
#else
extern struct AFConsoleStorage af_console_storage;
extern u8 af_console_scratch[AF_CONSOLE_RAW],af_console_players[4*0xBD0];
extern u32 af_console_hash[AF_CZ_HASH_WORDS],af_console_scratch_guard[4],af_console_hash_guard[4];
extern int af_console_canonical_check(const u8 *,u32,const u8 *,u8 *);
extern int af_console_canonical_pack(u8 *,u32,const u8 *);
extern void af_console_original_clear(u8 *);
#define storage (&af_console_storage)
#define scratch af_console_scratch
#define hash af_console_hash
#define scratch_guard af_console_scratch_guard
#define hash_guard af_console_hash_guard
#define native_players af_console_players
#define canonical_check af_console_canonical_check
#define canonical_pack af_console_canonical_pack
#define original_clear af_console_original_clear
#ifdef AF_V3_DIARY_STORAGE
extern AFDiary af_diary_storage;
extern u32 af_diary_guard[4];
#define diary (&af_diary_storage)
#define diary_guard af_diary_guard
#endif
#endif
extern void af_v3_require_save_state(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));
static void zero(u8 *p,u32 n) {while(n--)*p++=0;}
static void copy(u8 *d,const u8 *s,u32 n) {while(n--)*d++=*s++;}
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static u32 town(const u8 *p) {return (u32)p[8]<<8|p[9];}
static int separate(const void *a,u32 an,const void *b,u32 bn) {
    address x=(address)a,y=(address)b;
    if(an>(address)-1-x || bn>(address)-1-y)return 0;
    return x<=y?y-x>=an:x-y>=bn;
}
static int external(const void *p,u32 n) {
    return p && separate(p,n,storage,sizeof(*storage)) &&
        separate(p,n,scratch,AF_CONSOLE_RAW+16) && separate(p,n,hash,AF_CZ_WORK_BYTES+16)
#ifdef AF_V3_DIARY_STORAGE
        && separate(p,n,diary,AF_DIARY_BYTES+16)
#endif
#ifdef AF_V3_FISHING_STORAGE
        && separate(p,n,af_v3_fishing_state,AF_HF_BYTES)
#endif
#ifdef AF_V3_CARD_STORAGE
        && separate(p,n,af_v3_card_state,AF_HC_BYTES)
#ifdef AF_V3_BANK_STORAGE
        && separate(p,n,bank_state,AF_BANK_BYTES+16)
#endif
#endif
        ;
}
static int guards(void) {
    if(storage->magic!=MAGIC)return 0;
    for(u32 i=0;i<4;i++)if(storage->guard[i]!=GUARD ||
        scratch_guard[i]!=GUARD || hash_guard[i]!=GUARD
#ifdef AF_V3_DIARY_STORAGE
        || diary_guard[i]!=GUARD
#endif
        )return 0;
#ifdef AF_V3_DIARY_STORAGE
    if(!af_diary_valid(diary))return 0;
#endif
#ifdef AF_V3_FISHING_STORAGE
    if(!af_holiday_fish_wire_valid(af_v3_fishing_state))return 0;
#endif
#ifdef AF_V3_CARD_STORAGE
    if(!af_holiday_cards_valid(af_v3_card_state))return 0;
#ifdef AF_V3_CARRIED_PROFILE
    if(af_v3_card_state[4]!=AF_HC_CARRIED_WIRE || af_v3_card_state[8]!=af_carried_save_enabled() ||
       !cards_profile(af_v3_card_state))return 0;
#elif defined(AF_V3_EVENT_ITEM_PROFILE)
    if(af_v3_card_state[4]!=2 || af_v3_card_state[7]!=af_holiday_cards_enabled())return 0;
#endif
#endif
#ifdef AF_V3_BANK_STORAGE
    for(u32 i=0;i<4;i++)if(bank_guard[i]!=GUARD)return 0;
    if(!bank_profile(bank_state))return 0;
#endif
    return 1;
}
void af_v3_console_storage_reset(void) {
    zero((u8 *)storage,sizeof(*storage));storage->magic=MAGIC;
    for(u32 i=0;i<4;i++)storage->guard[i]=scratch_guard[i]=hash_guard[i]=GUARD;
#ifdef AF_V3_DIARY_STORAGE
    af_diary_reset(diary);
    for(u32 i=0;i<4;i++)diary_guard[i]=GUARD;
#endif
#ifdef AF_V3_FISHING_STORAGE
    af_holiday_fish_wire_reset(af_v3_fishing_state);
#endif
#ifdef AF_V3_CARD_STORAGE
    af_holiday_cards_reset(af_v3_card_state);
#ifdef AF_V3_EVENT_ITEM_PROFILE
    (void)cards_bind(af_v3_card_state);
#endif
#endif
#ifdef AF_V3_BANK_STORAGE
    for(u32 i=0;i<4;i++)bank_guard[i]=GUARD;
    if(!af_bank_reset(bank_state,AF_BANK_BYTES) || !bank_bind(bank_state))af_v3_save_halt(AF_SAVE_ARGUMENT);
#endif
}
int af_v3_console_storage_valid(void) {return guards() && !storage->busy;}
static int enter(void) {
    if(!af_v3_console_storage_valid())return 0;
    storage->busy=1;return 1;
}
static int leave(int result) {
    if(!guards() || storage->busy!=1)result=AF_SAVE_ARGUMENT;
    storage->busy=0;return result;
}
int af_v3_save_workspace_acquire(AFConsoleWorkspace *out) {
    if(!external(out,sizeof(*out)) || !af_v3_console_storage_valid())return 0;
    /* require_state itself checks !busy: do not take the loan first. */
    af_v3_require_save_state();
    if(!enter())return 0;
    out->data=scratch;out->index=hash;
    out->scratch_bytes=AF_CONSOLE_RAW;out->hash_bytes=AF_CZ_WORK_BYTES;
    return 1;
}
int af_v3_save_workspace_release(void) {
    if(storage->busy!=1)return AF_SAVE_ARGUMENT;
    return leave(AF_SAVE_OK);
}
static int expand(const u8 *bank,const u8 **logical) {
    *logical=bank;
    u32 version=word(bank+AF_SAVE_PAYLOAD+4);
    if(word(bank+4)==0x4E414633 && (version==0x00050680
#ifdef AF_V3_CREATURE_PROFILE
        || version==0x00070680
#endif
#ifdef AF_V3_INSECT_SEASONS
        || version==0x00090680
#endif
#ifdef AF_V3_DIARY_STORAGE
        || version==0x000B0680
#ifdef AF_V3_HOLIDAY_STORAGE
        || version==0x000C0680
#ifdef AF_V3_FISHING_STORAGE
        || version==0x000D0680
#ifdef AF_V3_CARD_STORAGE
        || version==0x000E0680
#ifdef AF_V3_EVENT_ITEM_PROFILE
        || version==0x000F0680
#endif
#ifdef AF_V3_CARRIED_PROFILE
        || version==0x00100680
#ifdef AF_V3_CARRIED_QUEST
        || version==0x00110680
#ifdef AF_V3_PAPER_PACKS
        || version==0x00120680
#ifdef AF_V3_CARRIED_NPC
        || version==0x00130680
#ifdef AF_V3_GOLDEN_REWARD_STORAGE
        || version==0x00140680
#ifdef AF_V3_BANK_STORAGE
        || version==0x00150680
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
        )) {
#ifdef AF_V3_DIARY_STORAGE
#ifdef AF_V3_FISHING_STORAGE
        int result=extended_expand(bank,AF_SAVE_BANK,scratch,AF_CONSOLE_RAW);
#else
        int result=af_v3_save_expand_diary(bank,AF_SAVE_BANK,scratch,AF_CONSOLE_RAW);
#endif
#else
        int result=af_v3_save_expand(bank,AF_SAVE_BANK,scratch,AF_CZ_RAW);
#endif
        if(result<0)return result==AF_CZ_FORMAT?AF_SAVE_FORMAT:
            result==AF_CZ_ARGUMENT?AF_SAVE_ARGUMENT:AF_SAVE_CRC;
#ifdef AF_V3_EVENT_ITEM_PROFILE
        if(!cards_profile(scratch+AF_CZ_RAW+AF_CZ_FISHING_EXTRA))return AF_SAVE_PROFILE_MISSING;
#endif
#ifdef AF_V3_BANK_STORAGE
        if(!bank_profile(scratch+AF_CZ_RAW+AF_CZ_CARD_EXTRA))return AF_SAVE_PROFILE_MISSING;
#endif
        *logical=scratch;
    }
    return 0;
}

int af_v3_save_check(const u8 *bank,u32 size,const u8 *profile,u8 *state) {
    const u8 *logical;int result;
    if(size!=AF_SAVE_BANK || !external(bank,size) || !external(profile,AF_SAVE_PROFILE) ||
       (state && (!external(state,AF_SAVE_STATE) || !separate(state,AF_SAVE_STATE,bank,size) ||
        !separate(state,AF_SAVE_STATE,profile,AF_SAVE_PROFILE))) || !enter())return AF_SAVE_ARGUMENT;
    result=expand(bank,&logical);
    if(result==0)result=canonical_check(logical,AF_SAVE_BANK,profile,state);
    return leave(result);
}

int af_v3_save_pack(u8 *bank,u32 size,const u8 *state) {
    int result;u32 id;
    if(size!=AF_SAVE_BANK || !external(bank,size) || !external(state,AF_SAVE_STATE) ||
       !separate(bank,size,state,AF_SAVE_STATE) || !enter())return AF_SAVE_ARGUMENT;
    copy(scratch,bank,AF_SAVE_BANK);
    result=canonical_pack(scratch,AF_SAVE_BANK,state);
    if(result!=AF_SAVE_OK)return leave(result);
    id=town(scratch);
    if(storage->ready && storage->town!=id)zero(scratch+AF_CZ_BANK,AF_CZ_CONSOLE);
    else copy(scratch+AF_CZ_BANK,storage->players,AF_CZ_CONSOLE);
#ifdef AF_V3_DIARY_STORAGE
    AFDiary *candidate=(AFDiary *)(scratch+AF_CZ_RAW);
    if(storage->ready && storage->town!=id)af_diary_reset(candidate);
    else copy((u8 *)candidate,(const u8 *)diary,AF_DIARY_BYTES);
#ifdef AF_V3_FISHING_STORAGE
    u8 *fishing=scratch+AF_CZ_RAW+AF_DIARY_BYTES;
    if(storage->ready && storage->town!=id)af_holiday_fish_wire_reset(fishing);
    else copy(fishing,af_v3_fishing_state,AF_HF_BYTES);
#ifdef AF_V3_CARD_STORAGE
    u8 *cards=scratch+AF_CZ_RAW+AF_CZ_FISHING_EXTRA;
    if(storage->ready && storage->town!=id)af_holiday_cards_reset(cards);
    else copy(cards,af_v3_card_state,AF_HC_BYTES);
#ifdef AF_V3_EVENT_ITEM_PROFILE
    if(!cards_bind(cards))return leave(AF_SAVE_PROFILE_MISSING);
#endif
#ifdef AF_V3_BANK_STORAGE
    u8 *account=scratch+AF_CZ_RAW+AF_CZ_CARD_EXTRA;
    if(storage->ready && storage->town!=id) {
        if(!af_bank_reset(account,AF_BANK_BYTES))return leave(AF_SAVE_ARGUMENT);
    } else copy(account,bank_state,AF_BANK_BYTES);
    if(!bank_bind(account))return leave(AF_SAVE_PROFILE_MISSING);
#endif
#endif
    result=extended_compress(bank,AF_SAVE_BANK,scratch,AF_CZ_BANK,
        scratch+AF_CZ_BANK,AF_CZ_CONSOLE,(const u8 *)candidate,hash,AF_CZ_WORK_BYTES);
#else
    result=af_v3_save_compress_diary(bank,AF_SAVE_BANK,scratch,AF_CZ_BANK,
        scratch+AF_CZ_BANK,AF_CZ_CONSOLE,candidate,hash,AF_CZ_WORK_BYTES);
#endif
#else
    result=af_v3_save_compress(bank,AF_SAVE_BANK,scratch,AF_CZ_BANK,
        scratch+AF_CZ_BANK,AF_CZ_CONSOLE,hash,AF_CZ_WORK_BYTES);
#endif
    if(result<0)return leave(result==AF_CZ_SPACE?AF_SAVE_CAPACITY:AF_SAVE_ARGUMENT);
    if(!guards())return leave(AF_SAVE_ARGUMENT);
    copy(storage->players,scratch+AF_CZ_BANK,AF_CZ_CONSOLE);
#ifdef AF_V3_DIARY_STORAGE
    copy((u8 *)diary,scratch+AF_CZ_RAW,AF_DIARY_BYTES);
#endif
#ifdef AF_V3_FISHING_STORAGE
    copy(af_v3_fishing_state,scratch+AF_CZ_RAW+AF_DIARY_BYTES,AF_HF_BYTES);
#endif
#ifdef AF_V3_CARD_STORAGE
    copy(af_v3_card_state,scratch+AF_CZ_RAW+AF_CZ_FISHING_EXTRA,AF_HC_BYTES);
#endif
#ifdef AF_V3_BANK_STORAGE
    copy(bank_state,scratch+AF_CZ_RAW+AF_CZ_CARD_EXTRA,AF_BANK_BYTES);
#endif
    storage->town=id;storage->ready=1;
    return leave(AF_SAVE_OK);
}

int af_v3_console_storage_commit(const u8 *bank,const u8 *profile,u8 *state,const u8 **logical) {
    const u8 *decoded;int result;
#ifdef AF_V3_BANK_STORAGE
    u8 candidate_bank[AF_BANK_BYTES];
#endif
    if(!logical || !external(logical,sizeof(*logical)) || !external(bank,AF_SAVE_BANK) ||
       !external(profile,AF_SAVE_PROFILE) || !external(state,AF_SAVE_STATE) ||
       !separate(state,AF_SAVE_STATE,bank,AF_SAVE_BANK) ||
       !separate(state,AF_SAVE_STATE,profile,AF_SAVE_PROFILE) ||
       !separate(logical,sizeof(*logical),bank,AF_SAVE_BANK) ||
       !separate(logical,sizeof(*logical),profile,AF_SAVE_PROFILE) ||
       !separate(logical,sizeof(*logical),state,AF_SAVE_STATE) || !enter())return AF_SAVE_ARGUMENT;
    result=expand(bank,&decoded);
#ifdef AF_V3_BANK_STORAGE
    if(result==0) {
        if(decoded==scratch)copy(candidate_bank,scratch+AF_CZ_RAW+AF_CZ_CARD_EXTRA,AF_BANK_BYTES);
        else if(!af_bank_reset(candidate_bank,AF_BANK_BYTES))return leave(AF_SAVE_ARGUMENT);
        if(!bank_bind(candidate_bank))return leave(AF_SAVE_PROFILE_MISSING);
    }
#endif
    if(result==0)result=canonical_check(decoded,AF_SAVE_BANK,profile,state);
    if(result<0)return leave(result);
    if(decoded==scratch)copy(storage->players,scratch+AF_CZ_BANK,AF_CZ_CONSOLE);
    else zero(storage->players,AF_CZ_CONSOLE);
#ifdef AF_V3_DIARY_STORAGE
    if(decoded==scratch)copy((u8 *)diary,scratch+AF_CZ_RAW,AF_DIARY_BYTES);
    else af_diary_reset(diary);
#endif
#ifdef AF_V3_FISHING_STORAGE
    if(decoded==scratch)copy(af_v3_fishing_state,scratch+AF_CZ_RAW+AF_DIARY_BYTES,AF_HF_BYTES);
    else af_holiday_fish_wire_reset(af_v3_fishing_state);
#endif
#ifdef AF_V3_CARD_STORAGE
    if(decoded==scratch)copy(af_v3_card_state,scratch+AF_CZ_RAW+AF_CZ_FISHING_EXTRA,AF_HC_BYTES);
    else af_holiday_cards_reset(af_v3_card_state);
#ifdef AF_V3_EVENT_ITEM_PROFILE
    (void)cards_bind(af_v3_card_state);
#endif
#endif
#ifdef AF_V3_BANK_STORAGE
    copy(bank_state,candidate_bank,AF_BANK_BYTES);
#endif
    storage->town=town(decoded);storage->ready=1;*logical=decoded;
    return leave(result);
}

u8 *af_v3_console_player_data(void) {
    af_v3_require_save_state();return storage->players;
}
#ifdef AF_V3_DIARY_STORAGE
AFDiary *af_v3_diary_data(void) {af_v3_require_save_state();return diary;}
#ifdef AF_V3_FISHING_STORAGE
u8 *af_v3_fishing_data(void) {af_v3_require_save_state();return af_v3_fishing_state;}
#endif
#ifdef AF_V3_CARD_STORAGE
u8 *af_v3_card_data(void) {af_v3_require_save_state();return af_v3_card_state;}
#endif
#ifdef AF_V3_BANK_STORAGE
u8 *af_v3_bank_data(void) {af_v3_require_save_state();return bank_state;}
u8 *af_bank_native_account(void) {return af_v3_bank_data();}
#endif
int af_v3_diary_measure(const u8 *bank,const u8 *state,const AFDiary *candidate) {
    if(!external(bank,AF_SAVE_BANK) || !external(state,AF_SAVE_STATE) ||
       !external(candidate,AF_DIARY_BYTES) || !af_diary_valid(candidate) ||
       !separate(candidate,AF_DIARY_BYTES,bank,AF_SAVE_BANK) ||
       !separate(candidate,AF_DIARY_BYTES,state,AF_SAVE_STATE) ||
       !separate(bank,AF_SAVE_BANK,state,AF_SAVE_STATE) || !enter())return AF_SAVE_ARGUMENT;
    copy(scratch,bank,AF_SAVE_BANK);
    int result=canonical_pack(scratch,AF_SAVE_BANK,state);
    if(result!=AF_SAVE_OK)return leave(result);
    if(storage->ready && storage->town!=town(scratch))return leave(AF_SAVE_BINDING);
#ifdef AF_V3_FISHING_STORAGE
    copy(scratch+AF_CZ_RAW,(const u8 *)candidate,AF_DIARY_BYTES);
    copy(scratch+AF_CZ_RAW+AF_DIARY_BYTES,af_v3_fishing_state,AF_HF_BYTES);
#ifdef AF_V3_CARD_STORAGE
    copy(scratch+AF_CZ_RAW+AF_CZ_FISHING_EXTRA,af_v3_card_state,AF_HC_BYTES);
#endif
#ifdef AF_V3_BANK_STORAGE
    copy(scratch+AF_CZ_RAW+AF_CZ_CARD_EXTRA,bank_state,AF_BANK_BYTES);
#endif
    result=extended_measure(scratch,AF_CZ_BANK,storage->players,AF_CZ_CONSOLE,
        scratch+AF_CZ_RAW,hash,AF_CZ_WORK_BYTES);
#else
    result=af_v3_save_measure_diary(scratch,AF_CZ_BANK,storage->players,AF_CZ_CONSOLE,
        candidate,hash,AF_CZ_WORK_BYTES);
#endif
    if(result==AF_CZ_SPACE)result=AF_SAVE_CAPACITY;
    else if(result<0)result=AF_SAVE_ARGUMENT;
    return leave(result);
}
#endif
void af_v3_console_player_clear(u8 *player) {
    u32 slot=4;
    for(u32 i=0;i<4;i++)if(player==native_players+i*0xBD0)slot=i;
    if(slot<4) {
        af_v3_require_save_state();zero(storage->players+slot*0x660,0x660);
#ifdef AF_V3_DIARY_STORAGE
        if(af_diary_player_clear(diary,slot)!=AF_DIARY_OK)af_v3_save_halt(AF_SAVE_ARGUMENT);
#endif
#ifdef AF_V3_CREATURE_PROFILE
        extern void af_v3_creature_player_clear(u32);
        af_v3_creature_player_clear(slot);
#endif
#ifdef AF_V3_FISHING_STORAGE
        if(!af_holiday_fish_wire_clear_person(af_v3_fishing_state,player))af_v3_save_halt(AF_SAVE_ARGUMENT);
#endif
#ifdef AF_V3_CARD_STORAGE
        if(!af_holiday_cards_clear(af_v3_card_state,slot))af_v3_save_halt(AF_SAVE_ARGUMENT);
#endif
#ifdef AF_V3_BANK_STORAGE
        if(!af_bank_clear(bank_state,AF_BANK_BYTES,slot))af_v3_save_halt(AF_SAVE_ARGUMENT);
        extern int af_bank_april_player_clear(u32);
        if(af_bank_april_player_clear(slot)<0)af_v3_save_halt(AF_SAVE_ARGUMENT);
#endif
    }
    original_clear(player);
}
