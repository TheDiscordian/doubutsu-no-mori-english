#ifndef AF_V3_TRAVEL_PLAYER_H
#define AF_V3_TRAVEL_PLAYER_H
#include "save_codec.h"
#include "diary.h"
#include "holiday_cards.h"
#include "bank_account.h"

/* One player's added records, independent of native Private padding. Full
 * selection requirements travel with the record; shared town state does not. */
enum {
    AF_TP_HEADER=32, AF_TP_PROFILE=272,
    AF_TP_FURNITURE=AF_TP_HEADER+AF_TP_PROFILE,
    AF_TP_CLOTHING=AF_TP_FURNITURE+128, AF_TP_SURFACES=AF_TP_CLOTHING+32,
    AF_TP_CREATURES=AF_TP_SURFACES+64, AF_TP_REWARDS=AF_TP_CREATURES+4,
    AF_TP_PAPER=AF_TP_REWARDS+12, AF_TP_CARD=AF_TP_PAPER+1,
    AF_TP_ACCOUNT=AF_TP_CARD+8, AF_TP_CONSOLE=AF_TP_ACCOUNT+8+3,
    AF_TP_CONSOLE_BYTES=1632, AF_TP_DIARY=AF_TP_CONSOLE+AF_TP_CONSOLE_BYTES,
    AF_TP_BYTES=AF_TP_DIARY+AF_DIARY_PLAYER
};
typedef struct {af_save_u8 bytes[AF_TP_PROFILE];} AFTravelSelection;
/* Profile layout: 192 main bytes, 64 surfaces, four creatures, two diary-cover
 * bytes, carried-family mask, paper mode, retained account requirement, seven
 * zero reserved bytes. The account field preserves already-built state only;
 * this adapter does not enable a feature or supply missing acquisition. */
typedef struct {
    af_save_u8 *players,*working,*console,*cards,*accounts;
    AFDiary *diary;
} AFTravelTown;

/* No live native copies or device I/O. Export and restore are transactional:
 * argument/profile/record failures leave output and town unchanged. Restore
 * requires the record's full identity to match the destination resident. */
/* Older native/catch-only notes do not contain editable added records. This
 * provenance bit survives conversion, preventing unknown blanks from replacing
 * a home resident's diary, console, holiday-card, or retained account data. */
enum { AF_TP_UNKNOWN_EDITABLE=1 };
int af_v3_player_records_valid(const af_save_u8 *,af_save_u32,
    const AFTravelSelection *current);
int af_v3_player_blank(af_save_u8 *,af_save_u32,const af_save_u8 identity[16],
    const AFTravelSelection *);
int af_v3_player_rebind(af_save_u8 *,af_save_u32,const AFTravelSelection *);
int af_v3_player_export(af_save_u8 *,af_save_u32,const AFTravelTown *,
    af_save_u32 slot,const AFTravelSelection *);
int af_v3_player_restore(AFTravelTown *,af_save_u32 slot,const af_save_u8 *,
    af_save_u32,const AFTravelSelection *current);
/* Visitor operations address only the identity-bound player record. Native
 * item adapters still validate/canonicalize selected items before calling. */
int af_v3_player_collect(af_save_u8 *,af_save_u32,const af_save_u8 identity[16],
    af_save_u32 item,af_save_u32 mark,const AFTravelSelection *current);
int af_v3_player_paper(af_save_u8 *,af_save_u32,const af_save_u8 identity[16],
    af_save_u32 mark,const AFTravelSelection *current);
#endif
