/* Additional stationery shares the real native letter window and text/editor
 * code. Its complete artwork is already resident; native styles keep their DMA. */
typedef unsigned char u8;
typedef unsigned int u32;
#ifdef __mips__
#define pointer(p,o) (*(void **)((u8 *)(p)+(o)))
static void original(void *submenu) {
    u8 *metadata=*(u8 **)0x8010DCECu;
    u32 constructor=*(u32 *)(metadata+0x2BA0u);
    ((void (*)(void *))(constructor-0x8088A6E8u+0x8088A604u))(submenu);
}
#else
extern void *af_test_carried_menu_pointer(void *,u32);
extern void af_test_carried_board_original(void *);
#define pointer af_test_carried_menu_pointer
#define original af_test_carried_board_original
#endif
void af_carried_board_load(void *submenu) {
    u8 *overlay=submenu?pointer(submenu,0x2C):0;
    u8 *board=overlay?pointer(overlay,0x106E4):0;
    if(!board)return;
    /* New-letter initialization records the inventory state's low byte. All
     * four quantities resolve to the parent's single saved stationery style. */
    if(board[4] && (u32)board[0x31]-64u<4u)board[0x31]=64;
    if(board[0x31]==64u) {
        /* New display lists and every resource use physical segment zero.
         * Leave the native DMA buffer alone: storing the resident art there
         * would let the next native paper load overwrite the shared packet. */
        return;
    }
    original(submenu);
}
