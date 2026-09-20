/* Keep the full native rod drawer. Its saved submenu is at caller sp+88.
   Only t5 is an output; at and ra are scratch, and caller ra is already saved. */
.set noreorder
.set noat
.section .text.af_v3_inventory_bobber,"ax",@progbits
.globl af_v3_inventory_bobber
.ent af_v3_inventory_bobber
af_v3_inventory_bobber:
    lw $t5, 88($sp)
    lw $t5, 44($t5)
    lui $at, 1
    addu $t5, $t5, $at
    lh $t5, 0x16($t5)
    addiu $t5, $t5, -8
    bnez $t5, 1f
    nop
    lui $t5, (AF_V3_BOBBER_POINTER >> 16)
    jr $ra
    ori $t5, $t5, (AF_V3_BOBBER_POINTER & 0xFFFF)
1:
    lui $t5, 0x0C01
    jr $ra
    addiu $t5, $t5, -0x620
.end af_v3_inventory_bobber
