/* Keep native double-buffered player clothing banks and saved field widths. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
extern u32 af_v3_clothing_source(int, u32);
extern void af_v3_load_clothing(void *, void *, int);
#ifdef __mips__
#define private_data (*(u8 **)0x80136FD8u)
#define bank_ids ((int *)0x8010C0D4u)
#define register_bank ((int (*)(void *, int, u32, u32))0x800B1838u)
#define toggle_bank ((int (*)(void))0x800B1944u)
#define texture_buffer ((u8 *(*)(void *))0x800B1AE0u)
#else
extern u8 *af_v3_player_private;
extern int af_v3_player_bank_ids[4];
extern int af_v3_player_register_bank(void *, int, u32, u32);
extern int af_v3_player_toggle_bank(void);
extern u8 *af_v3_player_texture_buffer(void *);
#define private_data af_v3_player_private
#define bank_ids af_v3_player_bank_ids
#define register_bank af_v3_player_register_bank
#define toggle_bank af_v3_player_toggle_bank
#define texture_buffer af_v3_player_texture_buffer
#endif

static void startup(void *game, int slot, int offset, u32 palette) {
    if (!game || (u32)slot > 1) return;
    const u8 *player = private_data;
    u32 index = player ? ((u32)player[0xA76] << 8) | player[0xA77] : 0;
    u32 source = af_v3_clothing_source(index, palette);
    /* A missing resource never becomes an out-of-range cartridge read. The
       profile guard owns compatibility; this does not change saved clothing. */
    if (!source) source = af_v3_clothing_source(0, palette);
    bank_ids[slot + palette*2] = offset + register_bank(game, 14+palette, source, palette ? 32 : 512);
}

void af_v3_player_cloth_texture(void *game, int slot, int offset) { startup(game, slot, offset, 0); }
void af_v3_player_cloth_palette(void *game, int slot, int offset) { startup(game, slot, offset, 1); }

void af_v3_player_change_cloth(void *game, u16 index) {
    if (!game || !af_v3_clothing_source(index, 0)) return;
    toggle_bank();
    u8 *texture = texture_buffer(game);
    if (!texture) { toggle_bank(); return; }
    af_v3_load_clothing(texture, texture+512, index);
}
