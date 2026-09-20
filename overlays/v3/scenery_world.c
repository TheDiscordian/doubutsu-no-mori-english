/* Imported-tree queries preserve real foreground identities and native terrain. */
#include "scenery_trees.h"
typedef struct { u32 prefix[11];u16 flags,item; } TreeUnit;
_Static_assert(sizeof(TreeUnit)==48,"Native collision unit stride");
_Static_assert(__builtin_offsetof(TreeUnit,item)==46,"Native collision item offset");
extern int af_v3_tree_column_native(void *,const TreeUnit *,int,u32,u32);
extern int af_v3_tree_dig_native(const u16 *,u32,u32,u32);
extern int af_v3_tree_npc_native(u32);
static int world_selected(void) {
    return af_v3_player_selected_equipment(af_v3_tree_rule.selected_item)>=0;
}
static u16 geometry_item(u16 item) {
    u32 stage=item-af_v3_tree_rule.first;
    if (stage>0 && stage<af_v3_tree_rule.count) return (u16)(0x800+(stage<4?stage:4));
    if ((u32)(item-af_v3_tree_rule.hidden_first)<af_v3_tree_rule.hidden_count) return 0x804;
    if ((u32)(item-af_v3_tree_rule.stumps[3])<4u) return (u16)(item-af_v3_tree_rule.stumps[3]+1);
    return item;
}
int af_v3_tree_column(void *column,const TreeUnit *unit,int grounded,u32 minimum,u32 maximum) {
    u16 item=unit->item,mapped=geometry_item(item);
    if (mapped!=item && world_selected()) {
        /* Native callers exclude an inclusive item range, not the donor's
           callback/coordinate pair. Test the real ID before geometry mapping. */
        if (item>=(u16)minimum && item<=(u16)maximum) return 0;
        TreeUnit copy;
        for (u32 i=0;i<11;++i) copy.prefix[i]=unit->prefix[i];
        copy.flags=unit->flags;
        copy.item=mapped;
        return af_v3_tree_column_native(column,&copy,grounded,0xffff,0);
    }
    return af_v3_tree_column_native(column,unit,grounded,minimum,maximum);
}
int af_v3_tree_dig(const u16 *item,u32 x,u32 y,u32 z) {
    if ((*item==af_v3_tree_rule.first || *item==af_v3_tree_daily_config.dead ||
            (u32)(*item-af_v3_tree_rule.stumps[3])<4u) && world_selected()) return 1;
    return af_v3_tree_dig_native(item,x,y,z);
}
int af_v3_tree_npc(u32 item) {
    if ((u16)item==af_v3_tree_rule.first && world_selected()) return 1;
    return af_v3_tree_npc_native(item);
}
#ifdef __mips__
/* Full original routines stay in core; these restore their displaced entries. */
__asm__(".set noreorder\n.section .text.af_v3_tree_world_native,\"ax\"\n"
        ".globl af_v3_tree_column_native\naf_v3_tree_column_native:\n"
        "addiu $sp,$sp,-32\nsw $s1,24($sp)\nj 0x8006C988\nnop\n"
        ".globl af_v3_tree_dig_native\naf_v3_tree_dig_native:\n"
        "sw $a1,4($sp)\nsw $a2,8($sp)\nj 0x8008C96C\nnop\n"
        ".globl af_v3_tree_npc_native\naf_v3_tree_npc_native:\n"
        "sw $a0,0($sp)\nandi $a0,$a0,65535\nj 0x8008D7B8\nnop\n.set reorder\n");
#endif
