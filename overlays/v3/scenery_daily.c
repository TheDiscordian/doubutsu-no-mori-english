/* Shared daily-growth extension. Original families retain native consumers;
   selected imported trees also participate in neighbour and acre limits. */
#include "scenery_trees.h"
typedef struct {
    u16 *around[4];
    int cap,days,flower_days;
    int preserved[3];
    int x,z;
} GrowInfo;
#ifdef __mips__
_Static_assert(__builtin_offsetof(GrowInfo,cap)==0x10,"Native growth condition");
_Static_assert(__builtin_offsetof(GrowInfo,x)==0x28,"Native growth coordinates");
static u8 *owner(void) { return *(u8 **)(uptr)af_v3_tree_daily_config.slot; }
#define native_near ((int (*)(u16 *,GrowInfo *,int,int))(owner()+af_v3_tree_daily_config.near))
#define native_plant ((int (*)(u16 *,GrowInfo *))(owner()+af_v3_tree_daily_config.plant))
#define native_set ((void (*)(u16 *,u16 *))(owner()+af_v3_tree_daily_config.set_info))
#define native_reset ((void (*)(u16 *,u8 *,u8 *,u16 *))(owner()+af_v3_tree_daily_config.reset_info))
#define native_thin ((void (*)(u16 *,u16 *,int,int))(owner()+af_v3_tree_daily_config.thin))
#else
extern int native_near(u16 *,GrowInfo *,int,int);
extern int native_plant(u16 *,GrowInfo *);
extern void native_set(u16 *,u16 *);
extern void native_reset(u16 *,u8 *,u8 *,u16 *);
extern void native_thin(u16 *,u16 *,int,int);
#endif
extern float af_scenery_random(void);
static int selected(void) { return af_v3_player_selected_equipment(af_v3_tree_rule.selected_item)>=0; }
static int gold(u32 item) { return item-af_v3_tree_rule.first<af_v3_tree_rule.count; }
static int hidden(u32 item) { return item-af_v3_tree_rule.hidden_first<af_v3_tree_rule.hidden_count; }
static int native_tree(u32 item) {
    return item-0x800u<0x3cu || item-0x84fu<5u || item-0x5eu<4u || item==0x69u;
}
static int native_sapling(u32 item) {
    static const u16 ids[]={0x800,0x805,0x80d,0x815,0x81d,0x825,0x82d,0x832,0x837,0x84f};
    for (u32 i=0;i<sizeof(ids)/sizeof(ids[0]);++i) if (item==ids[i]) return 1;
    return 0;
}
static u16 *neighbour(u16 *item,GrowInfo *info,int x,int z,u32 direction) {
    u16 *acre=info->around[direction];
    switch (direction) {
    case 0: return z>0 ? item-16 : acre ? acre+240+x : 0;
    case 1: return z<15 ? item+16 : acre ? acre+x : 0;
    case 2: return x>0 ? item-1 : acre ? acre+z*16+15 : 0;
    default:return x<15 ? item+1 : acre ? acre+z*16 : 0;
    }
}
int af_v3_tree_near(u16 *item,GrowInfo *info,int x,int z) {
    if (!selected()) return native_near(item,info,x,z);
    int imported=*item==af_v3_tree_rule.first;
    if (!imported && !native_sapling(*item)) return native_near(item,info,x,z);
    int odd=(x^z)&1;
    for (u32 i=0;i<4;++i) {
        u16 *p=neighbour(item,info,x,z,i);
        if (!p) continue;
        u32 value=*p;
        int stump=value-af_v3_tree_rule.stumps[3]<4u;
        int tree=gold(value) || hidden(value);
        int sapling=value==af_v3_tree_rule.first;
        if (imported) { stump|=value-1u<4u;tree|=native_tree(value);sapling|=native_sapling(value); }
        if (stump || (tree && (odd || !sapling))) {
            *item=imported?af_v3_tree_daily_config.dead:af_v3_tree_daily_config.native_dead;
            /* The donor's even-cell branch returns true after killing. Its
               subsequent family check leaves the dead sapling unchanged. */
            return imported && !odd;
        }
    }
    return imported ? 1 : native_near(item,info,x,z);
}
int af_v3_tree_daily_plant(u16 *item,GrowInfo *info) {
    const TreeDaily *d=&af_v3_tree_daily_config;
    if ((!gold(*item) && *item!=d->dead) || !selected()) return native_plant(item,info);
    if (info->cap==-1 || *item==d->dead) *item=0;
    else if (info->cap==0) *item=d->dead;
    else if (af_v3_tree_near(item,info,info->x,info->z) && gold(*item) && info->days>0)
        *item=(u16)af_v3_tree_grow(*item,info->days-1,info->cap);
    return 1;
}
void af_v3_tree_set_info(u16 *bits,u16 *items) {
    native_set(bits,items);
    if (selected()) for (u32 i=0;i<256;++i)
        if (items[i]==af_v3_tree_rule.first) bits[i/16]|=(u16)(1u<<(i%16));
}
void af_v3_tree_reset_info(u16 *bits,u8 *normal,u8 *other,u16 *items) {
    if (selected()) for (u32 i=0;i<256;++i)
        if (items[i]==af_v3_tree_daily_config.dead) bits[i/16]&=(u16)~(1u<<(i%16));
    native_reset(bits,normal,other,items);
}
static void kill(u16 *items,u16 *bits,int *normal,int *other) {
    int ordinary=*normal>0;
    int *count=ordinary?normal:other;
    int choice=(int)(af_scenery_random()*(float)*count);
    for (u32 i=0;i<256;++i) if (bits[i/16]&(1u<<(i%16))) {
        if (ordinary!=(items[i]-0x800u<5u)) continue;
        if (choice<=0) {
            bits[i/16]&=(u16)~(1u<<(i%16));
            items[i]=gold(items[i])?af_v3_tree_daily_config.dead:af_v3_tree_daily_config.native_dead;
            --*count;break;
        }
        --choice;
    }
}
void af_v3_tree_thin(u16 *items,u16 *bits,int normal,int other) {
    if (!selected()) { native_thin(items,bits,normal,other);return; }
    u8 trees=0,remaining=(u8)(normal+other);
    for (u32 i=0;i<256;++i) if (native_tree(items[i]) || gold(items[i]) || hidden(items[i])) ++trees;
    int excess=(int)trees-(int)af_v3_tree_daily_config.limit;
    while (excess>0 && remaining) { kill(items,bits,&normal,&other);--excess;--remaining; }
}
#ifdef __mips__
/* The sole native loader owns the pointer. Resume the checked renewal prologue
   after the resident bootstrap has loaded and verified this packet. */
__asm__(".set noreorder\n.section .text.af_v3_tree_renew_native,\"ax\"\n"
        ".globl af_v3_tree_renew_native\naf_v3_tree_renew_native:\n"
        "lui $t9,0x8010\nlw $t9,0x0C5C($t9)\naddiu $t9,$t9,0x4764\n"
        "addiu $sp,$sp,-104\njr $t9\nsw $ra,36($sp)\n.set reorder\n");
#endif
