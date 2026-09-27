/* The NES interpreter owns all integer registers, including gp, t6 and t9.
 * Preserve full 64-bit registers around ordinary o32 C, plus HI and LO. */
.set noreorder
.set noat
.set gp=64
.text
.macro disk_bridge name, target
.globl \name
.type \name,@function
\name:
    addiu $sp,$sp,-288
    sd $0,16($sp)
    .irp reg,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,30,31
    sd $\reg,16+8*\reg($sp)
    .endr
    addiu $8,$sp,288
    sd $8,248($sp)
    mfhi $8
    sd $8,272($sp)
    mflo $8
    sd $8,280($sp)
    move $4,$30
    jal \target
    addiu $5,$sp,16
    ld $8,272($sp)
    mthi $8
    ld $8,280($sp)
    mtlo $8
    .irp reg,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,30,31
    ld $\reg,16+8*\reg($sp)
    .endr
    jr $14
    addiu $sp,$sp,288
.size \name,.-\name
.endm
disk_bridge af_v3_qd_wdm_bridge,af_v3_qd_native_wdm_dispatch
disk_bridge af_v3_qd_ram_bridge,af_v3_qd_native_ram_dispatch
