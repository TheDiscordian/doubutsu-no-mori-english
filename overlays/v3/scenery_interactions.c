/* Shared source records extend the native seasonal drop and cutting consumers. */
#include "scenery_trees.h"
typedef struct { const TreeDrop *begin,*end; } TreeDropSpan;
static const TreeDropSpan drop_spans[2]={
    {af_v3_tree_drops,af_v3_tree_drops+13},
    {af_v3_tree_drops,af_v3_tree_drops+17}};
static int interaction_selected(void) {
    return af_v3_player_selected_equipment(af_v3_tree_rule.selected_item)>=0;
}
const TreeDropSpan *af_v3_tree_drop_table(void) {
    return drop_spans+interaction_selected();
}
int af_v3_tree_is_bee(u32 item) {
    item&=65535;
    return item==0x5e || (item==af_v3_tree_rule.hidden_first+2u && interaction_selected());
}
u32 af_v3_tree_drop_item(u32 tree,u32 item) {
    tree&=65535;item&=65535;
    if (tree==0x69 || (tree==af_v3_tree_rule.hidden_first && interaction_selected())) {
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
    if (!interaction_selected()) return;
    const u16 *cells=af_tree_field_units(bx*16,bz*16);
    if (!cells) return;
    for (u32 i=0;i<256;++i)
        for (u32 j=0;j<8;++j)
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
