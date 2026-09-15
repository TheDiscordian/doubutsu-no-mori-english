/* Fixed imported-house markers, preserving every original building marker.
 * Call sites already save ra. Only the original result register and at change;
 * these leaf routines use no stack, other GPRs, HI/LO, or floating-point state.
 */
.set noreorder
.set noat
.set gp=64
.text
.macro marker name, value
.globl \name
.ent \name
\name:
    addiu $at, \value, -0x50DA
    sltiu $at, $at, 20
    beqz $at, normal\@
    ori $at, $zero, 0xA005
    ori $at, $zero, 0xA126
normal\@:
    addu \value, \value, $at
    andi \value, \value, 0xFFFF
    jr $ra
    ori $at, $zero, 0xA005
.end \name
.endm

/* Both original and imported inputs use these checked leaf entries through
 * the two guarded native expression windows. */
marker af_v3_house_marker_v1, $v1
marker af_v3_house_marker_a0, $a0

.globl af_v3_is_house_marker_v1
.ent af_v3_is_house_marker_v1
af_v3_is_house_marker_v1:
    addiu $at, $v1, 0x0FFB
    andi $at, $at, 0xFFFF
    sltiu $at, $at, 218
    bnez $at, yes
    nop
    addiu $at, $v1, 0x0E00
    andi $at, $at, 0xFFFF
    jr $ra
    sltiu $at, $at, 20
yes:
    jr $ra
    addiu $at, $zero, 1
.end af_v3_is_house_marker_v1
