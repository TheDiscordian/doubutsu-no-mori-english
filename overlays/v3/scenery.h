#ifndef AF_V3_SCENERY_H
#define AF_V3_SCENERY_H
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef struct {
    u32 slot, constructor, bank_offset, bytes, vrom, crc;
    u32 table_offset, table_count, first_index, body_loop, shadow_loop, classify;
} Scenery;
_Static_assert(sizeof(Scenery)==48,"Scenery configuration stride");
enum { MAGIC, VERSION, BYTES, READY, CPU, CPU_N, GPU, GPU_N, CALLBACK, CALLBACK_N,
       ROWS, ROW_N, TYPES, TYPE_N, PALETTES, ACTIVE, TERMS, TRAMPOLINE, TERM };
extern const Scenery af_v3_scenery_config[4];
extern u8 *af_v3_ground_prepare(u32);
extern int af_v3_player_selected_equipment(u32);
extern int af_scenery_dma(void *,u32,u32);
extern u32 af_scenery_crc(const void *,u32);
extern void af_scenery_writeback(void *,u32);
extern void af_scenery_invalidate(void *,u32);
extern int af_scenery_term(void);
extern void af_scenery_fault(const char *,const char *);
#ifdef __mips__
#define scene_owner(c) (*(u8 **)(uptr)(c)->slot)
#else
extern u8 *af_test_scenery_owners[4];
extern void af_test_scenery_constructor(void *,void *,u32);
extern void af_test_scenery_classify(u32,void *,void *,void *,u32);
extern void af_test_scenery_body(void *,void *,void *,void *,void *,u32);
#define scene_owner(c) af_test_scenery_owners[(c)-af_v3_scenery_config]
#endif
#endif
