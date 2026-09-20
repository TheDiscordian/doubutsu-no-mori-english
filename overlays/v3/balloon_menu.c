/* Additive outdoor balloon menu, retaining every native item classification. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define WORD(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define HALF(p,o) (*(u16 *)((u8 *)(p)+(o)))
#ifdef __mips__
#define PTR(p,o) (*(void **)((u8 *)(p)+(o)))
#define ACTIVE (*(u8 **)0x80136FD8u)
#define FIELD (*(u8 *)AF_V3_MENU_FIELD_ADDRESS)
#define GAME (*(void **)0x8010EF90u)
static void *native(u32 at) {
    if (at>=0x8086F310u) at=WORD(*(void **)0x8010DCECu,0x2CC0)-0x808787A0u+at;
    return (void *)at;
}
#else
extern void *af_test_balloon_menu_pointer(void *,u32),*af_test_balloon_menu_function(u32);
extern u8 *af_test_balloon_menu_active,af_test_balloon_menu_field;
extern void *af_test_balloon_menu_game;
#define PTR af_test_balloon_menu_pointer
#define ACTIVE af_test_balloon_menu_active
#define FIELD af_test_balloon_menu_field
#define GAME af_test_balloon_menu_game
#define native af_test_balloon_menu_function
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))
extern int af_v3_player_selected_equipment(u32),af_v3_balloon_queue(void *,u32,int);

int af_v3_balloon_menu_type(void *submenu,u32 item,int slot) {
    unsigned shape=item-0x2244u;
    if (shape<8u && (unsigned)slot<15u && ACTIVE &&
            !(WORD(ACTIVE,0x34)>>(slot*2)&3u) &&
            af_v3_player_selected_equipment(item)==(int)(91u+shape)) {
        if (FIELD==0) return 44;
        return FIELD==1?12:8;
    }
    return FN(0x80875610u,int,void *,u32,int)(submenu,item,slot);
}

void af_v3_balloon_menu_fly(void *submenu,void *menu) {
    if (!submenu || !menu || !ACTIVE || FIELD || !GAME) return;
    void *overlay=PTR(submenu,0x2C);
    if (!overlay) return;
    u8 *tag=PTR(overlay,0x106D0);
    if (!tag) return;
    int slot=FN(0x8086F910u,int,void *)(tag+8);
    if ((unsigned)slot>=15u || (WORD(ACTIVE,0x34)>>(slot*2)&3u)) return;
    u32 item=HALF(ACTIVE,0x14+slot*2);
    if (!af_v3_balloon_queue(GAME,item,0)) {
        FN(0x80871570u,void,void *,void *,int)(submenu,menu,11);
        return;
    }
    *((u8 *)submenu+0xDF)=(u8)slot;HALF(submenu,0xE0)=(u16)item;
    u32 replacement=WORD(menu,0x38)==13u?(u16)WORD(menu,0x3C):0;
    FN(0x800B8B08u,void,void *,int,u32,int)(ACTIVE,slot,replacement,0);
    FN(0x8086F4ACu,int,void *,int,int)(submenu,0,0);
    FN(0x80871760u,void,void *,void *,int)(submenu,menu,1);
}
