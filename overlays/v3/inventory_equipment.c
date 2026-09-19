/* Inventory preview uses its own kinds. Keep native 0..4 and empty kind 5. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef struct {u16 item;u8 preview,world;} Entry;
#ifdef __mips__
#define header ((const u32 *)0x804A9C00u)
#define shapes ((const u32 *)(0x804A9400u+4u*41u*4u))
#define selected ((int (*)(u32))AF_V3_HELD_SELECTED)
#define resource ((u32 (*)(int))0x800B12C8u)
#else
extern u32 af_iv_header[60],af_iv_shapes[41];
extern int af_iv_selected(u32);
extern u32 af_iv_resource(int);
#define header af_iv_header
#define shapes af_iv_shapes
#define selected af_iv_selected
#define resource af_iv_resource
#endif

int af_v3_inventory_kind_from_item(u32 item) {
    if (item==0x2200u)return 1;
    if (item==0x2201u)return 0;
    if (item==0x2203u)return 3;
    if (item>=0x2204u && item<0x2224u)return 2;
    if (item==0x2202u)return 4;
    if (item<0x2224u || item>=0x225Cu || header[0]!=0x41464956u ||
            header[1]!=1u || header[2]!=56u || header[3]!=4u)return 5;
    const Entry *row=(const Entry *)(header+4)+(item-0x2224u);
    if (row->item!=item || row->preview<6u || row->preview>=41u ||
            row->world<36u || row->world>=115u || selected(item)!=(int)row->world)return 5;
    return row->preview;
}

#ifdef __mips__
int af_v3_inventory_item_kind(void) {
    const u8 *player=*(const u8 *const *)0x80136FD8u;
    return player ? af_v3_inventory_kind_from_item(*(const u16 *)(player+0x3ECu)) : 5;
}
#endif

void af_v3_inventory_static_draw(u8 *submenu,u8 *game) {
    u8 *overlay=*(u8 **)(submenu+0x2C);
    int kind=*(s16 *)(overlay+0x10016);
    if (kind<6 || kind>=41)return;
    u32 shape=shapes[kind];
    if (shape<17u || shape>=67u)return;
    u32 pointer=resource((int)shape);
    if (!pointer)return;
    u8 *graph=*(u8 **)game;
    u32 *commands=*(u32 **)(graph+0x298);
    commands[0]=0xDE000000u;commands[1]=pointer;
    *(u32 **)(graph+0x298)=commands+2;
}
