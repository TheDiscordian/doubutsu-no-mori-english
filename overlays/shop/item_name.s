.set noreorder
.set noat
.text
.balign 4
.globl af_shop_item_name
# item (a0), item-field slot (a1). Both tail paths preserve the caller's ra/sp.
# The existing quest wrapper handles full names but intentionally ignores item
# zero. Shops must instead clear that field, matching their original helper.
af_shop_item_name:
    andi    $a0, $a0, 0xffff
    bnez    $a0, full_name
    nop
    lui     $a0, 0x8014
    addiu   $a0, $a0, 0x2410
    move    $a2, $a0
    j       af_set_item_str
    move    $a3, $zero
full_name:
    j       af_quest_set_item
    nop
    .space  72 - (. - af_shop_item_name)
