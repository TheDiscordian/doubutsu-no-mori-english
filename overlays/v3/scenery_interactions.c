/* Shared source records extend the native seasonal drop and cutting consumers. */
#include "scenery_trees.h"
typedef struct { const TreeDrop *begin,*end; } TreeDropSpan;
static const TreeDropSpan drop_spans[2]={
    {af_v3_tree_drops,af_v3_tree_drops+13},
#ifdef AF_V3_TREE_FAMILIES
    {af_v3_tree_drops,af_v3_tree_drops+21}};
const TreeDropSpan *af_v3_tree_drop_table(u32 tree) {
    return drop_spans+(tree_rule((u16)tree)!=0);
}
#else
    {af_v3_tree_drops,af_v3_tree_drops+17}};
const TreeDropSpan *af_v3_tree_drop_table(void) {
    return drop_spans+trees_selected();
}
#endif
int af_v3_tree_is_bee(u32 item) {
    item&=65535;
    const TreeRule *r=tree_rule(item);
    return item==0x5e || (r && r->hidden_count && item==r->hidden_first+2u);
}
u32 af_v3_tree_drop_item(u32 tree,u32 item) {
    tree&=65535;item&=65535;
    const TreeRule *r=tree_rule(tree);
    if (tree==0x69 || (r && r->hidden_count && tree==r->hidden_first)) {
#ifdef __mips__
        const u8 *player=*(const u8 **)0x80136FD8u;
        if (player[0xA8E]==4) return 0x2100;
#else
        extern int af_test_tree_money_luck;
        if (af_test_tree_money_luck) return 0x2100;
#endif
    }
    return item;
}
extern const u16 *af_tree_field_units(int,int);
#ifndef __mips__
extern void af_test_tree_cut_native(int,int,u8 *,u32);
#endif
static void cut_attributes(int bx,int bz,u8 *attributes,u32 variant) {
#ifdef __mips__
    u8 *owner=scene_owner(af_v3_scenery_config+variant);
    ((void (*)(int,int,u8 *))(owner+0x4F98))(bx,bz,attributes);
#else
    af_test_tree_cut_native(bx,bz,attributes,variant);
#endif
    if (!trees_selected()) return;
    const u16 *cells=af_tree_field_units(bx*16,bz*16);
    if (!cells) return;
    for (u32 i=0;i<256;++i) if (tree_rule(cells[i]))
        for (u32 j=0;j<TREE_CUTS;++j)
            if (cells[i]==af_v3_tree_cuts[j][0]) {
                attributes[i]=(u8)af_v3_tree_cuts[j][1];break;
            }
}
#define CUT(n) \
void af_v3_tree_cut##n(int x,int z,u8 *attributes) { cut_attributes(x,z,attributes,n); }
CUT(0) CUT(1) CUT(2) CUT(3)
#ifdef __mips__
/* The native bee branch retains a0 for its ordinary drop call. Other arguments
   are reloaded by the original code, and its saved return address stays intact. */
__asm__(".set noreorder\n.section .text.af_v3_tree_bee_query,\"ax\"\n"
        ".globl af_v3_tree_bee_query\naf_v3_tree_bee_query:\n"
        "addiu $sp,$sp,-24\nsw $ra,20($sp)\njal af_v3_tree_is_bee\nsw $a0,16($sp)\n"
        "lw $a0,16($sp)\nlw $ra,20($sp)\njr $ra\naddiu $sp,$sp,24\n.set reorder\n");
#endif
