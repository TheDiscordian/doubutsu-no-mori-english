#ifndef AF_V3_TRAVEL_NATIVE_H
#define AF_V3_TRAVEL_NATIVE_H
#include "travel_player.h"
#include "pak_native.h"
typedef struct {
    af_save_u32 magic,ready,reserved[2];
    af_save_u8 record[AF_TP_BYTES];
    af_save_u32 guard[4];
} AFTravelVisitor;
enum { AF_TRAVEL_MAGIC=0x41465431u,AF_TRAVEL_GUARD=0xAF54524Cu,
    AF_TRAVEL_STATE_BYTES=(sizeof(AFTravelVisitor)+15)&~15u };
int af_v3_travel_prepare(void);
void af_v3_travel_passport_clear(af_save_u8 *);
int af_v3_travel_passport_save(af_save_u8 *,const af_save_u8 *,void *);
int af_v3_travel_passport_load(af_save_u8 *,af_save_u8 *,void *);
void af_v3_travel_private_copy(af_save_u8 *,const af_save_u8 *);
int af_v3_travel_visitor_collect(af_save_u8 *,unsigned,unsigned);
int af_v3_travel_visitor_paper(af_save_u8 *,unsigned);
int af_v3_travel_creature_collect(af_save_u8 *,unsigned,unsigned);
/* Actual context construction uses the existing guarded getters before taking
 * a workspace loan. Tests supply native buffers, not alternate record logic. */
int af_travel_town(AFTravelTown *,AFTravelSelection *);
int af_travel_storage_idle(void);
af_save_u8 *af_travel_active(void);
int af_pak_check_private(const af_save_u8 *);
void af_pak_set_kind(void *,unsigned);
void af_pak_clear_private(af_save_u8 *),af_pak_clear_animal(af_save_u8 *);
void af_cw_passport_stage(af_save_u8 *),af_cw_passport_complete(af_save_u8 *,int);
void af_v3_save_halt(int) __attribute__((noreturn));
#endif
