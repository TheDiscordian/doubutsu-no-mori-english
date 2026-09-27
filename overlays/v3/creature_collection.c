/* Native and added species share catch/completion consumers, not bit indices. */
#include "save_runtime.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
#ifdef __mips__
#define state ((struct AfSaveRuntime *)0x8046C000u)
#define players ((u8 *)0x80126EC0u)
#define active (*(u8 *volatile *)0x80136FD8u)
#else
extern struct AfSaveRuntime af_creature_collection_state;
extern u8 af_creature_players[4*0xBD0],*af_creature_active;
#define state (&af_creature_collection_state)
#define players af_creature_players
#define active af_creature_active
#endif
extern int af_creature_item_type(u32);
extern int af_creature_save_collect(u8 *,u32,u32,u32);
extern void af_v3_require_save_state(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));

static u32 read_word(const u8 *p) {
    return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];
}
static void write_word(u8 *p,u32 value) {
    p[0]=(u8)(value>>24);p[1]=(u8)(value>>16);p[2]=(u8)(value>>8);p[3]=(u8)value;
}
static unsigned slot(const u8 *private) {
    for (unsigned i=0;i<4;i++) if (private==players+i*0xBD0) return i;
    return 4;
}
static unsigned item(unsigned kind,unsigned index) {
    return (kind ? 0x2D00u : 0x2300u)+index;
}
static int selected(unsigned kind,unsigned index) {
    return kind<2 && index<(kind ? 40u : 41u) &&
        (index<32 || af_creature_item_type(item(kind,index))==(kind ? 18 : 8));
}

int af_v3_creature_collected(u8 *private,unsigned kind,unsigned index,unsigned mark) {
    if (!private || mark>1 || !selected(kind,index)) return 0;
    if (index<32) {
        u8 *p=private+0xABC+kind*4;
        u32 bits=read_word(p),bit=1u<<index;
        if (mark) {bits|=bit;write_word(p,bits);}
        return !!(bits&bit);
    }
    unsigned player=slot(private);
    /* A visitor's extra collections need Controller Pak transport. Never put
     * those records in another player's slot or discard a successful catch. */
    if (player==4) {
        if (mark) af_v3_save_halt(AF_SAVE_ARGUMENT);
        return 0;
    }
    af_v3_require_save_state();
    int result=af_creature_save_collect(state->working,player,item(kind,index),mark);
    if (result<0) af_v3_save_halt(result);
    return result;
}

/* prospective is the catch under consideration, or -1 for the saved result. */
int af_v3_creature_complete(u8 *private,unsigned kind,int prospective) {
    if (!private || kind>1) return 0;
    u32 native=read_word(private+0xABC+kind*4);
    if (prospective>=0 && prospective<32) native|=1u<<(unsigned)prospective;
    if (native!=0xFFFFFFFFu) return 0;
    for (unsigned i=32;i<(kind ? 40u : 41u);i++)
        if (selected(kind,i) && prospective!=(int)i &&
            !af_v3_creature_collected(private,kind,i,0)) return 0;
    return 1;
}
static int last_catch(unsigned kind,unsigned index) {
    return selected(kind,index) && !af_v3_creature_collected(active,kind,index,0) &&
        af_v3_creature_complete(active,kind,(int)index);
}

void af_v3_creature_notice_fish(u8 *player,int actor) {
    if (!player) return;
    /* Rubbish 32..34 and the coastal salmon alias 35 are not added species. */
    int index=actor==35 ? 22 : actor>=36 && actor<45 ? actor-4 : actor;
    if (actor<0 || actor>=45 || (actor>=32 && actor<=34)) return;
    write_word(player+0xD24,(u32)last_catch(0,(unsigned)index));
    af_v3_creature_collected(active,0,(unsigned)index,1);
}
u8 *af_v3_creature_last_insect(u8 *player,int index) {
    if (player) write_word(player+0xD14,(u32)last_catch(1,(unsigned)index));
    return player;
}
u8 *af_v3_creature_notice_insect(u8 *player,int index) {
    af_v3_creature_collected(active,1,(unsigned)index,1);
    return player;
}
void af_v3_creature_start_complete(void) {
    if (!active) return;
    if (af_v3_creature_complete(active,0,-1)) active[0xAEC]|=1;
    if (af_v3_creature_complete(active,1,-1)) active[0xAEC]|=4;
}
static int talk(unsigned kind) {
    unsigned mask=3u<<(kind*2);
    return active && af_v3_creature_complete(active,kind,-1) &&
        (active[0xAEC]&mask)!=mask;
}
int af_v3_creature_fish_talk(void) {return talk(0);}
int af_v3_creature_insect_talk(void) {return talk(1);}
