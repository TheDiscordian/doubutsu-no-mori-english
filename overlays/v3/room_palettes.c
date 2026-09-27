/* Selected endpoints use the same checked fade and frame-owned renderer as
   fixed building models. No additional actor, heap, or saved allocation. */
#include "tent_model.c"

#ifdef __mips__
extern u16 mFI_GetFieldId(void);
extern int mHS_get_arrange_idx(int);
#define roof_common ((const volatile u8 *)0x80126EA0u)
#define roof_field (*(const volatile u16 *volatile *)0x8013A248u)
#else
extern u8 af_v3_test_roof_common[0x10004];
extern const u16 *af_v3_test_roof_field;
extern int mHS_get_arrange_idx(int);
#define roof_common af_v3_test_roof_common
#define roof_field af_v3_test_roof_field
static u16 mFI_GetFieldId(void) { return *roof_field; }
#endif

u32 af_v3_roof_index(signed short control) {
    u32 home;
    if (control == 1) {
        /* Native N64 has no GameCube island cottage. Only actual player
           fields select a home; all other gameplay locations use colour 0. */
        if (!roof_field) return 0;
        u32 field=mFI_GetFieldId();
        if ((field&0xF000u)!=0x6000u) return 0;
        home=(field-0x6000u)&3u;
    } else {
        u32 player=roof_common[0x10003];
        if (player>=4) return 0;
        home=(u32)mHS_get_arrange_idx((int)player);
        if (home>=4) return 0;
    }
    u32 colour=roof_common[0x3588u+home*0xB48u+0x24u];
    return colour<12 ? colour : 0;
}

/* These generic callback signatures also accept native catalogue instances. */
void af_v3_roof_ct(void *actor,u8 *data) { af_v3_tent_model_ct(actor,data); }
void af_v3_roof_mv(void *actor,void *room,void *game,u8 *data) {
    af_v3_tent_model_mv(actor,room,game,data);
}
void af_v3_roof_dw(void *actor,void *room,void *game,u8 *data) {
    if (actor && game && ((TentGame *)game)->gfx)
        af_v3_palette_fade_dw(actor,room,game,data);
}
