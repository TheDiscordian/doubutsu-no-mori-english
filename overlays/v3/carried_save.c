/* Spirits leave the active player's pockets on a completed save or departure.
 * Stage that change in the write buffer; never remove live items on an I/O
 * failure, a player-load/reset-guard save, or a codec capacity probe. */
#include "save_runtime.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
enum { PRIVATE_BYTES=0xBD0, ID_BYTES=16, POCKETS=0x14, CONDITIONS=0x34 };
extern void *af_cw_private(void);
extern u32 af_carried_quantity(u32);
extern void af_v3_require_save_state(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));
extern int af_cw_prior_save_step(int,int,int);
#ifdef __mips__
#define live ((u8 *)0x80126EA0u)
#define save_step (*(const volatile int *)0x80107634u)
#define native_copy ((void (*)(const void *,void *,u32))0x800360E0u)
#define allocate ((u8 *(*)(u32))0x8009BFC0u)
#define release ((void (*)(void *))0x8009C040u)
#define erase ((int (*)(void))0x800CDC10u)
#define write_page ((int (*)(const u8 *,u32))0x800CDC30u)
#else
extern u8 af_save_live[AF_SAVE_PAYLOAD];
extern int af_cw_test_save_step;
extern void af_save_copy(const void *,void *,u32);
extern u8 *af_save_allocate(u32);
extern void af_save_release(void *);
extern int af_save_erase(void),af_save_write_page(const u8 *,u32);
#define live af_save_live
#define save_step af_cw_test_save_step
#define native_copy af_save_copy
#define allocate af_save_allocate
#define release af_save_release
#define erase af_save_erase
#define write_page af_save_write_page
#endif

static struct {
    u8 *player;
    u8 identity[ID_BYTES];
    int active,ending,kind,mode;
} pending;

static int identity(const u8 *a,const u8 *b) {
    if(!a || !b)return 0;
    for(unsigned i=0;i<ID_BYTES;i++)if(a[i]!=b[i])return 0;
    return 1;
}
void af_cw_clean_spirits(u8 *player) {
    if(!player || af_carried_quantity(0x2D28)!=1)return;
    u32 cond=(u32)player[CONDITIONS]<<24|(u32)player[CONDITIONS+1]<<16|
        (u32)player[CONDITIONS+2]<<8|player[CONDITIONS+3];
    for(unsigned i=0;i<15;i++) {
        u8 *p=player+POCKETS+i*2;
        unsigned item=(unsigned)p[0]<<8|p[1];
        if(item>=0x2D28 && item<=0x2D2C) {
            p[0]=p[1]=0;cond&=~(3u<<(i*2));
        }
    }
    player[CONDITIONS]=cond>>24;player[CONDITIONS+1]=cond>>16;
    player[CONDITIONS+2]=cond>>8;player[CONDITIONS+3]=cond;
}
static void stage(u8 *bank,const u8 *player) {
    if(!bank || bank==live)af_v3_save_halt(AF_SAVE_ARGUMENT);
    if(!player)return;
    /* The visitor has no home-player row in this town. Its separate passport
     * carries the inventory, while every unrelated resident stays unchanged. */
    for(unsigned i=0;i<4;i++) {
        u8 *p=bank+0x20+i*PRIVATE_BYTES;
        if(identity(p,player))af_cw_clean_spirits(p);
    }
}
void af_cw_save_prepare(u8 *bank) {
    if(pending.active && pending.ending)stage(bank,pending.identity);
    af_v3_save_prepare(bank);
}
int af_cw_save_step(int kind,int unused,int mode) {
    int before=save_step;
    if(before==0) {
        pending.active=1;pending.kind=kind;pending.mode=mode;
        pending.ending=(kind==1 || kind==3) && mode==0;
        pending.player=af_cw_private();
        for(unsigned i=0;i<ID_BYTES;i++)
            pending.identity[i]=pending.player?pending.player[i]:0;
    } else if(pending.active && (pending.kind!=kind || pending.mode!=mode)) {
        af_v3_save_halt(AF_SAVE_ARGUMENT);
    }
    int result=af_cw_prior_save_step(kind,unused,mode);
    if(result) {
        /* Several native error paths also return 1. Only state 8 follows the
         * successful second-bank write; the Pak-recovery route returns -2. */
        if(pending.active && pending.ending && before==8 && result==1 &&
           identity(pending.player,pending.identity))af_cw_clean_spirits(pending.player);
        pending.active=0;pending.player=0;
    }
    return result;
}
void af_cw_passport_stage(u8 *player) {
    if(!pending.active || pending.ending)af_cw_clean_spirits(player);
}
void af_cw_passport_complete(u8 *player,int result) {
    /* During the combined town/Pak transaction, the outer state machine owns
     * completion. A successful Pak write alone is not a successful town save. */
    if(!pending.active && result==1)af_cw_clean_spirits(player);
}
int af_cw_save_sync(void) {
    /* The explicit save-menu callers use the existing complete-bank write
     * contract. Title erasure and automatic player loading keep their readers. */
    af_v3_require_save_state();
    u8 *bank=allocate(AF_SAVE_BANK);
    if(!bank)return -1;
    u8 *player=af_cw_private(),id[ID_BYTES];
    for(unsigned i=0;i<ID_BYTES;i++)id[i]=player?player[i]:0;
    native_copy(live,bank,AF_SAVE_PAYLOAD);stage(bank,player);
    af_v3_save_prepare(bank);
    int result=erase();
    if(result==0) {
        for(u32 page=0;page<512;page++) {
            result=write_page(bank+page*128,page);
            for(u32 retry=0;result==-1 && retry<3;retry++)
                result=write_page(bank+page*128,page);
            if(result!=0)break;
        }
    }
    if(result==0) {
        native_copy(bank,live,0x14);
        if(identity(player,id))af_cw_clean_spirits(player);
    }
    release(bank);
    return result==0?0:-1;
}
