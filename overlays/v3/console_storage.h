#ifndef AF_V3_CONSOLE_STORAGE_H
#define AF_V3_CONSOLE_STORAGE_H
#include "save_codec.h"
#include "save_compressed.h"
#ifdef AF_V3_DIARY_STORAGE
#ifdef AF_V3_FISHING_STORAGE
#ifdef AF_V3_CARD_STORAGE
#define AF_CONSOLE_RAW AF_CZ_CARD_RAW
unsigned char *af_v3_card_data(void);
#else
#define AF_CONSOLE_RAW AF_CZ_FISHING_RAW
#endif
unsigned char *af_v3_fishing_data(void);
#else
#define AF_CONSOLE_RAW AF_CZ_DIARY_RAW
#endif
AFDiary *af_v3_diary_data(void);
int af_v3_diary_measure(const af_save_u8 *bank,const af_save_u8 *state,const AFDiary *candidate);
int af_v3_diary_preflight(const AFDiary *candidate);
#else
#define AF_CONSOLE_RAW AF_CZ_RAW
#endif
struct AFConsoleStorage {
    af_save_u32 magic,busy,town,ready;
    af_save_u8 players[AF_CZ_CONSOLE];
    af_save_u32 guard[4];
};
_Static_assert(sizeof(struct AFConsoleStorage)==0x19A0,"Console state allocation");
void af_v3_console_storage_reset(void);
int af_v3_console_storage_valid(void);
int af_v3_console_storage_commit(const af_save_u8 *bank,const af_save_u8 *profile,
    af_save_u8 *state,const af_save_u8 **logical);
void af_v3_console_player_clear(af_save_u8 *player);
af_save_u8 *af_v3_console_player_data(void);
#endif
