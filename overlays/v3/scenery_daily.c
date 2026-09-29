/* Shared daily-growth extension. Original families retain native consumers;
   selected imported trees also participate in neighbour and acre limits. */
#include "scenery_trees.h"
typedef struct {
    u16 *around[4];
    int cap,days,flower_days;
    int spoil,block_x,block_z;
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
    if (!trees_selected()) return native_near(item,info,x,z);
    const TreeRule *r=tree_rule(*item);
    int imported=r && *item==r->first;
    if (!imported && !native_sapling(*item)) return native_near(item,info,x,z);
    int odd=(x^z)&1;
    for (u32 i=0;i<4;++i) {
        u16 *p=neighbour(item,info,x,z,i);
        if (!p) continue;
        u32 value=*p;
        const TreeRule *n=tree_rule(value);
        int stump=n && tree_stump(n,value);
        int tree=n && (tree_live(n,value) || tree_hidden(n,value));
        int sapling=n && value==n->first;
        if (imported) { stump|=value-1u<4u;tree|=native_tree(value);sapling|=native_sapling(value); }
        if (stump || (tree && (odd || !sapling))) {
            *item=imported?(u16)(r->first+r->count):af_v3_tree_daily_config.native_dead;
            /* The donor's even-cell branch returns true after killing. Its
               subsequent family check leaves the dead sapling unchanged. */
            return imported && !odd;
        }
    }
    return imported ? 1 : native_near(item,info,x,z);
}
int af_v3_tree_daily_plant(u16 *item,GrowInfo *info) {
    const TreeRule *r=tree_rule(*item);
    if (!r || (u32)(*item-r->first)>r->count) return native_plant(item,info);
    u16 dead=(u16)(r->first+r->count);
    if (info->cap==-1 || *item==dead) *item=0;
    else if (info->cap==0) *item=dead;
    else if (af_v3_tree_near(item,info,info->x,info->z) && tree_live(r,*item)) {
#ifdef AF_V3_TREE_FAMILIES
        int allowed=1;
        if (r->unused==1) allowed=info->block_z==6;
        if (r->unused==2) {
            /* The donor checks each cell's ground height, including cliffs,
               not the acre's nominal height or the player's current position. */
            extern int af_tree_block_position(float *,float *,int,int);
            extern float af_tree_ground_height(TreePosition,float);
            TreePosition p={0,0,0};
            af_tree_block_position(&p.x,&p.z,info->block_x,info->block_z);
            p.x+=20.0f+40.0f*info->x;p.z+=20.0f+40.0f*info->z;
            allowed=af_tree_ground_height(p,0.0f)>=100.0f;
        }
        if (!allowed) *item=dead;
        else
#endif
        if (info->days>0) *item=(u16)af_v3_tree_grow(*item,info->days-1,info->cap);
    }
    return 1;
}
void af_v3_tree_set_info(u16 *bits,u16 *items) {
    native_set(bits,items);
    for (u32 i=0;i<256;++i) {
        const TreeRule *r=tree_rule(items[i]);
        if (r && items[i]==r->first) bits[i/16]|=(u16)(1u<<(i%16));
    }
}
void af_v3_tree_reset_info(u16 *bits,u8 *normal,u8 *other,u16 *items) {
    u8 cedars=0;
    for (u32 i=0;i<256;++i) if (bits[i/16]&(1u<<(i%16))) {
        const TreeRule *r=tree_rule(items[i]);
        if (r && items[i]==r->first+r->count) bits[i/16]&=(u16)~(1u<<(i%16));
        else if (r && r->unused==2 && tree_live(r,items[i])) ++cedars;
    }
    native_reset(bits,normal,other,items);
    /* Native counting puts cedar candidates in 'other'. Move that exact count
       to normal, retaining native dead/empty handling and eight-bit wrapping. */
    *normal=(u8)(*normal+cedars);*other=(u8)(*other-cedars);
}
static void kill(u16 *items,u16 *bits,int *normal,int *other) {
    int ordinary=*normal>0;
    int *count=ordinary?normal:other;
    int choice=(int)(af_scenery_random()*(float)*count);
    for (u32 i=0;i<256;++i) if (bits[i/16]&(1u<<(i%16))) {
        const TreeRule *r=tree_rule(items[i]);
        if (ordinary!=(items[i]-0x800u<5u || (r && r->unused==2 && tree_live(r,items[i])))) continue;
        if (choice<=0) {
            bits[i/16]&=(u16)~(1u<<(i%16));
            items[i]=r?(u16)(r->first+r->count):af_v3_tree_daily_config.native_dead;
            --*count;break;
        }
        --choice;
    }
}
void af_v3_tree_thin(u16 *items,u16 *bits,int normal,int other) {
    if (!trees_selected()) { native_thin(items,bits,normal,other);return; }
    u8 trees=0,remaining=(u8)(normal+other);
    for (u32 i=0;i<256;++i) {
        const TreeRule *r=tree_rule(items[i]);
        if (native_tree(items[i]) || (r && (tree_live(r,items[i]) || tree_hidden(r,items[i])))) ++trees;
    }
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
