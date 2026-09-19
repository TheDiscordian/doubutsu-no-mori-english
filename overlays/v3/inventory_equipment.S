/* Original callbacks keep linked addresses in expanded immutable tables.
   Resolve them from the current inventory BSS, never a saved heap pointer. */
.set noreorder
.set noat
.section .text.af_v3_inventory_dispatch,"ax",@progbits
.globl af_v3_inventory_dispatch
.ent af_v3_inventory_dispatch
af_v3_inventory_dispatch:
    beqz $t9, 2f
    nop
    lui $t0, 0x8088
    addiu $t0, $t0, -0x2B80
    subu $t1, $t9, $t0
    sltiu $t0, $t1, 0x3D30
    beqz $t0, 1f
    nop
    lw $t0, 0x2C($a0)
    lui $t9, 1
    addu $t0, $t0, $t9
    lw $t0, 0x6DC($t0)
    addiu $t0, $t0, -0x41C0
    addu $t9, $t0, $t1
1:
    jr $t9
    nop
2:
    jr $ra
    nop
.end af_v3_inventory_dispatch
